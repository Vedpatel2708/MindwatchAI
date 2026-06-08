"""
backend/agent/agent.py — MINDWATCH
LangChain ReAct agent — runs in a thread pool to avoid blocking FastAPI's event loop.
"""

import asyncio
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from langchain_groq import ChatGroq
from langchain.agents import initialize_agent, AgentType
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.agents import AgentAction, AgentFinish

from agent.tools import ALL_TOOLS
from agent.prompts import format_assessment_prompt
from config import settings
from database import supabase_client
from websocket_manager import ws_manager

logger = logging.getLogger(__name__)
MAX_RETRIES = 2

# Single shared thread pool — agent.run() is synchronous so it must run off
# the event loop thread to avoid freezing all WebSocket connections and requests.
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="agent")


class AssessmentCallbackHandler(BaseCallbackHandler):
    """Persists each ReAct step to analysis_steps in real time."""

    def __init__(self, assessment_id: str):
        super().__init__()
        self.assessment_id = assessment_id
        self.step_number = 0

    def _next(self):
        self.step_number += 1
        return self.step_number

    def _insert(self, row: dict):
        try:
            supabase_client.table("analysis_steps").insert(row).execute()
        except Exception as e:
            logger.warning(f"Step insert failed: {e}")

    def on_agent_action(self, action: AgentAction, **kwargs):
        # Save thought separately if present
        thought = ""
        if action.log:
            thought = action.log.split("Action:")[0].strip()
            # Strip common prefixes that LLMs add
            for prefix in ("Thought:", "thought:", "THOUGHT:"):
                if thought.startswith(prefix):
                    thought = thought[len(prefix):].strip()

        if thought:
            self._insert({
                "assessment_id": self.assessment_id,
                "step_number": self._next(),
                "step_type": "thought",
                "content": thought[:2000],
                "is_error": False,
            })

        self._insert({
            "assessment_id": self.assessment_id,
            "step_number": self._next(),
            "step_type": "action",
            "tool_name": action.tool,
            "tool_input": (
                action.tool_input
                if isinstance(action.tool_input, dict)
                else {"input": str(action.tool_input)[:500]}
            ),
            "is_error": False,
        })

    def on_tool_end(self, output: str, **kwargs):
        try:
            parsed = json.loads(output)
        except Exception:
            parsed = {"raw": str(output)[:1000]}
        self._insert({
            "assessment_id": self.assessment_id,
            "step_number": self._next(),
            "step_type": "observation",
            "tool_output": parsed,
            "is_error": False,
        })

    def on_tool_error(self, error: Exception, **kwargs):
        self._insert({
            "assessment_id": self.assessment_id,
            "step_number": self._next(),
            "step_type": "observation",
            "is_error": True,
            "error_detail": str(error)[:500],
        })

    def on_agent_finish(self, finish: AgentFinish, **kwargs):
        self._insert({
            "assessment_id": self.assessment_id,
            "step_number": self._next(),
            "step_type": "final_answer",
            "content": finish.return_values.get("output", "")[:3000],
            "is_error": False,
        })


def _build_agent(assessment_id: str):
    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name="llama-3.1-8b-instant",
        temperature=0,
        max_tokens=1024,  # reduced — final answer is ~300 tokens, no need for more
        request_timeout=30,
    )
    return initialize_agent(
        tools=ALL_TOOLS,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        max_iterations=6,           # reduced from 8 — prevents runaway loops
        early_stopping_method="generate",
        handle_parsing_errors=True,
        callbacks=[AssessmentCallbackHandler(assessment_id=assessment_id)],
    )


def _parse_output(output: str) -> dict:
    """Extract JSON from agent output, with graceful fallback."""
    if not output:
        return _fallback("No output from agent.")

    # Try clean JSON parse first
    stripped = output.strip()
    if stripped.startswith("{"):
        try:
            return json.loads(stripped)
        except Exception:
            pass

    # Find the last JSON block in the output (agent sometimes writes prose then JSON)
    matches = list(re.finditer(r'\{[^{}]{20,}\}', stripped, re.DOTALL))
    for match in reversed(matches):
        try:
            return json.loads(match.group())
        except Exception:
            continue

    return _fallback(output[:300])


def _fallback(reason: str) -> dict:
    return {
        "risk_level": "moderate",
        "primary_concerns": ["Automated assessment completed"],
        "detected_patterns": [],
        "protective_factors": [],
        "summary": f"The ML pipeline completed initial screening. {reason[:200]}",
        "immediate_actions": ["Please consult a mental health professional for a full evaluation."],
        "resources": [
            {"name": "988 Suicide & Crisis Lifeline", "contact": "988", "type": "crisis"},
            {"name": "SAMHSA Helpline", "contact": "1-800-662-4357", "type": "mental_health"},
        ],
        "follow_up_suggested": True,
    }


def _run_agent_sync(assessment_id: str, prompt: str) -> dict:
    """
    Synchronous agent execution — called in a thread pool worker.
    Must NOT use asyncio or await here.
    """
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            agent = _build_agent(assessment_id=assessment_id)
            result_text = agent.run(prompt)
            return _parse_output(result_text)
        except Exception as exc:
            last_error = exc
            logger.warning(f"Agent attempt {attempt + 1} failed: {exc}")
            if attempt < MAX_RETRIES - 1:
                import time
                time.sleep(2 ** attempt)  # blocking sleep is fine inside thread

    logger.error(f"Agent failed after {MAX_RETRIES} attempts: {last_error}")
    return None


async def run_assessment(assessment_id: str) -> None:
    """
    Async entry point called by FastAPI BackgroundTask.
    Fetches the assessment, runs the agent in a thread, saves results.
    """
    logger.info(f"Starting agent assessment: {assessment_id}")

    # 1. Fetch assessment row
    try:
        res = supabase_client.table("assessments").select("*").eq("id", assessment_id).single().execute()
        assessment = res.data
        if not assessment:
            logger.error(f"Assessment {assessment_id} not found in DB.")
            return
    except Exception as e:
        logger.error(f"DB fetch failed for {assessment_id}: {e}")
        return

    # 2. Mark as analyzing
    try:
        supabase_client.table("assessments").update({"status": "analyzing"}).eq("id", assessment_id).execute()
    except Exception as e:
        logger.warning(f"Could not set status=analyzing: {e}")

    # 3. Build prompt
    prompt = format_assessment_prompt(
        assessment_id=assessment_id,
        input_text=assessment.get("input_text", ""),
        input_type=assessment.get("input_type", "journal"),
        crisis_score=float(assessment.get("crisis_score") or 0),
        depression_score=float(assessment.get("depression_score") or 0),
        anxiety_score=float(assessment.get("anxiety_score") or 0),
        crisis_signal=float(assessment.get("crisis_signal") or 0),
        dominant_emotion=assessment.get("dominant_emotion", "unknown"),
        risk_level=assessment.get("risk_level", "analyzing"),
        detected_symptoms=assessment.get("detected_symptoms") or [],
    )

    # 4. Run agent in thread pool — avoids blocking the event loop
    loop = asyncio.get_event_loop()
    report_data = await loop.run_in_executor(
        _executor,
        _run_agent_sync,
        assessment_id,
        prompt,
    )

    now = datetime.now(timezone.utc).isoformat()

    # 5. Save results
    if report_data:
        try:
            final_risk = report_data.get("risk_level", assessment.get("risk_level", "moderate"))
            supabase_client.table("assessments").update({
                "risk_level":      final_risk,
                "agent_summary":   report_data.get("summary", ""),
                "recommendations": report_data.get("immediate_actions", []),
                "resources":       report_data.get("resources", []),
                "status":          "completed",
                "analyzed_at":     now,
            }).eq("id", assessment_id).execute()

            if final_risk in ("high", "crisis"):
                supabase_client.table("risk_alerts").insert({
                    "assessment_id": assessment_id,
                    "session_id":    assessment.get("session_id"),
                    "crisis_score":  assessment.get("crisis_score", 0),
                    "risk_level":    final_risk,
                    "threshold_used": 0.5,
                }).execute()

            await ws_manager.broadcast("assessment.completed", {
                "assessment_id": assessment_id,
                "risk_level":    final_risk,
                "summary":       report_data.get("summary", "")[:150],
                "timestamp":     now,
            })
            logger.info(f"Assessment {assessment_id} completed — risk: {final_risk}")
        except Exception as e:
            logger.error(f"Failed to save results for {assessment_id}: {e}")
    else:
        # Agent failed — still mark completed with ML-only result
        try:
            supabase_client.table("assessments").update({
                "status":        "completed",
                "agent_summary": "ML screening completed. Full agent analysis unavailable.",
                "analyzed_at":   now,
            }).eq("id", assessment_id).execute()
            await ws_manager.broadcast("assessment.completed", {
                "assessment_id": assessment_id,
                "risk_level":    assessment.get("risk_level", "moderate"),
                "summary":       "ML screening completed.",
                "timestamp":     now,
            })
        except Exception as e:
            logger.error(f"Failed to mark {assessment_id} as completed: {e}")

"""
backend/routers/consumer.py — MINDWATCH
Mental health support chat endpoint.
Reuses the analyze-situation pattern from the fraud project.
"""

import json
import logging
import re
from fastapi import APIRouter
from pydantic import BaseModel, Field
from config import settings
from models.schemas import APIEnvelope

logger = logging.getLogger(__name__)
router = APIRouter()


class SituationRequest(BaseModel):
    situation: str = Field(..., min_length=5, description="User's description of their mental health situation")


class SituationAnalysis(BaseModel):
    is_scam: bool = False          # kept for schema compatibility
    risk_level: str
    confidence: float
    scam_type: str                 # repurposed as "situation_type" for mental health
    explanation: str
    immediate_actions: list[str]
    report_to: list[str]          # repurposed as support resources


@router.post("/analyze-situation", response_model=APIEnvelope[SituationAnalysis])
async def analyze_situation(body: SituationRequest):
    """
    Analyze a mental health situation described in plain English.
    Powers the MINDWATCH Support Chat.
    Uses Groq LLM for compassionate, clinically-informed responses.
    Falls back to keyword matching if Groq is unavailable.
    """
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage, SystemMessage

    SYSTEM = """You are MINDWATCH Support, a compassionate AI mental health support assistant.
A user will describe their mental health situation. Analyze it and respond with ONLY a valid JSON object.

JSON format:
{
  "is_scam": false,
  "risk_level": "safe" | "low" | "moderate" | "high" | "crisis",
  "confidence": 0.0 to 1.0,
  "scam_type": "depression" | "anxiety" | "crisis" | "grief" | "trauma" | "general_support" | "seeking_info",
  "explanation": "2-3 compassionate, supportive sentences acknowledging their feelings and providing context. Be warm and non-judgmental.",
  "immediate_actions": ["3-4 specific, actionable steps they can take right now"],
  "report_to": ["support resource 1", "support resource 2"]
}

Rules:
- Always be compassionate and non-judgmental
- If ANY suicidal ideation is mentioned, risk_level MUST be "crisis"
- For crisis situations, include "Call 988" as the first immediate_action
- report_to should contain 2-3 relevant support resources
- Output ONLY the JSON. Nothing else."""

    try:
        llm = ChatGroq(api_key=settings.GROQ_API_KEY, model_name="llama-3.1-8b-instant", temperature=0.3, max_tokens=800)
        response = llm.invoke([
            SystemMessage(content=SYSTEM),
            HumanMessage(content=f"Mental health situation: {body.situation}"),
        ])
        raw = response.content.strip()
        match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        data = json.loads(match.group() if match else raw)
        return APIEnvelope.success(SituationAnalysis(
            is_scam=False,
            risk_level=str(data.get("risk_level", "low")),
            confidence=float(data.get("confidence", 0.75)),
            scam_type=str(data.get("scam_type", "general_support")),
            explanation=str(data.get("explanation", "")),
            immediate_actions=list(data.get("immediate_actions", [])),
            report_to=list(data.get("report_to", [])),
        ))
    except Exception as exc:
        logger.warning(f"Groq unavailable, using keyword fallback: {exc}")

    # Keyword fallback
    s = body.situation.lower()
    PATTERNS = [
        (["kill myself", "end my life", "don't want to live", "suicide", "suicidal", "hurt myself"],
         "crisis", "crisis", 1.0,
         "What you're sharing sounds really serious, and I want you to know you're not alone. Your feelings are valid, and there is support available right now. Please reach out to a crisis resource immediately.",
         ["Call or text 988 (Suicide & Crisis Lifeline) RIGHT NOW", "Text HOME to 741741 for Crisis Text Line", "Go to your nearest emergency room if you're in immediate danger", "Tell someone you trust what you're going through"]),
        (["hopeless", "worthless", "no point", "can't go on", "exhausted", "empty", "sad all the time"],
         "high", "depression", 0.8,
         "It sounds like you're carrying a really heavy weight right now. These feelings of hopelessness and exhaustion are signs that you deserve support. You're not alone in this.",
         ["Reach out to a therapist or counselor this week", "Call SAMHSA at 1-800-662-4357 for free support", "Practice one small act of self-care today", "Share these feelings with someone you trust"]),
        (["anxious", "panic", "can't stop worrying", "racing thoughts", "scared", "overwhelmed"],
         "moderate", "anxiety", 0.75,
         "Anxiety can feel overwhelming and all-consuming. What you're experiencing is real, and there are effective ways to manage these feelings with the right support.",
         ["Try a grounding exercise: name 5 things you can see", "Practice slow breathing: inhale 4 counts, hold 4, exhale 4", "Consider speaking with a therapist about anxiety management", "Limit caffeine and screen time before bed"]),
        (["help a friend", "worried about someone", "how to help"],
         "low", "seeking_info", 0.7,
         "It shows real care that you're thinking about how to support someone. Being there for a friend struggling with mental health can make a huge difference.",
         ["Listen without judgment — just let them talk", "Ask directly: 'Are you having thoughts of suicide?'", "Encourage them to seek professional help", "Share the 988 crisis line with them"]),
    ]

    for keywords, risk, stype, conf, explanation, actions in PATTERNS:
        if any(kw in s for kw in keywords):
            resources = ["988 Suicide & Crisis Lifeline (call/text 988)", "Crisis Text Line (text HOME to 741741)"] if risk == "crisis" else ["SAMHSA Helpline: 1-800-662-4357", "Find a therapist: psychologytoday.com"]
            return APIEnvelope.success(SituationAnalysis(
                is_scam=False, risk_level=risk, confidence=conf, scam_type=stype,
                explanation=explanation, immediate_actions=actions, report_to=resources,
            ))

    return APIEnvelope.success(SituationAnalysis(
        is_scam=False, risk_level="low", confidence=0.5, scam_type="general_support",
        explanation="Thank you for sharing. Whatever you're going through, you deserve support and understanding. Mental health is just as important as physical health.",
        immediate_actions=["Speak with a mental health professional if symptoms persist", "Practice self-care and reach out to trusted people", "Remember that seeking help is a sign of strength"],
        report_to=["SAMHSA Helpline: 1-800-662-4357", "Mental Health America: mhanational.org"],
    ))

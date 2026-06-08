"""
backend/routers/assessments.py — MINDWATCH
POST /assessments — submit text for analysis
GET  /assessments  — list assessments
GET  /assessments/{id} — get single assessment with analysis steps
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Query
from pydantic import BaseModel, Field
from database import supabase_client
from ml.crisis_scorer import score_text
from models.schemas import APIEnvelope, PaginatedList
from websocket_manager import ws_manager
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class AssessmentRequest(BaseModel):
    input_text: str = Field(..., min_length=10, description="Journal entry, message, or clinical note")
    input_type: str = Field(default="journal", description="journal | chat | note")
    session_id: Optional[str] = Field(default=None, description="Optional session UUID for longitudinal tracking")


@router.post("", response_model=APIEnvelope[dict])
async def submit_assessment(body: AssessmentRequest, background_tasks: BackgroundTasks):
    """Submit text for mental health crisis analysis."""
    now = datetime.now(timezone.utc)

    # Step 1: ML pre-screening
    try:
        score = score_text(body.input_text)
    except Exception as exc:
        return APIEnvelope.failure("ML_ERROR", str(exc))

    # Step 2: Insert assessment row
    row = {
        "input_text":       body.input_text,
        "input_type":       body.input_type,
        "session_id":       body.session_id,
        "crisis_score":     score.crisis_score,
        "depression_score": score.depression_score,
        "anxiety_score":    score.anxiety_score,
        "crisis_signal":    score.crisis_signal,
        "sentiment_score":  score.sentiment_score,
        "dominant_emotion": score.dominant_emotion,
        "detected_symptoms": score.detected_symptoms,
        "risk_level":       score.risk_level,
        "status":           "pending",
    }
    try:
        res = supabase_client.table("assessments").insert(row).execute()
        assessment_id = res.data[0]["id"]
    except Exception as exc:
        return APIEnvelope.failure("DB_ERROR", str(exc))

    # Step 3: Broadcast to dashboard
    await ws_manager.broadcast("assessment.submitted", {
        "assessment_id": assessment_id,
        "risk_level":    score.risk_level,
        "crisis_score":  score.crisis_score,
        "dominant_emotion": score.dominant_emotion,
        "timestamp":     now.isoformat(),
    })

    # Step 4: Dispatch agent analysis as background task
    background_tasks.add_task(_run_agent, assessment_id)

    return APIEnvelope.success({
        "assessment_id": assessment_id,
        "risk_level": score.risk_level,
        "crisis_score": score.crisis_score,
        "depression_score": score.depression_score,
        "anxiety_score": score.anxiety_score,
        "dominant_emotion": score.dominant_emotion,
        "detected_symptoms": score.detected_symptoms,
        "status": "pending",
        "message": "Text submitted. Agent analysis starting...",
        # ML model outputs
        "phq9_severity": score.phq9_severity,
        "phq9_severity_score": score.phq9_severity_score,
        "crisis_ml_probability": score.crisis_ml_probability,
        "emotion_ml": score.emotion_ml,
        "ml_models_used": score.ml_models_used,
    })


async def _run_agent(assessment_id: str):
    try:
        from agent.agent import run_assessment
        await run_assessment(assessment_id)
    except Exception as exc:
        logger.error(f"Agent failed for assessment {assessment_id}: {exc}")


@router.get("", response_model=APIEnvelope[PaginatedList[dict]])
async def list_assessments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    risk_level: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
):
    start = (page - 1) * page_size
    end = start + page_size - 1
    query = supabase_client.table("assessments").select(
        "id,input_type,crisis_score,risk_level,dominant_emotion,status,submitted_at,agent_summary",
        count="exact"
    )
    if risk_level:
        query = query.eq("risk_level", risk_level)
    if session_id:
        query = query.eq("session_id", session_id)
    query = query.order("submitted_at", desc=True).range(start, end)
    try:
        result = query.execute()
    except Exception as exc:
        return APIEnvelope.failure("DB_ERROR", str(exc))
    total = result.count or 0
    items = result.data or []
    return APIEnvelope.success(PaginatedList(
        items=items, total=total, page=page, page_size=page_size,
        has_more=(start + len(items)) < total,
    ))


@router.get("/{assessment_id}", response_model=APIEnvelope[dict])
async def get_assessment(assessment_id: str):
    try:
        res = supabase_client.table("assessments").select("*").eq("id", assessment_id).single().execute()
    except Exception:
        return APIEnvelope.failure("NOT_FOUND", f"Assessment '{assessment_id}' not found.")

    if not res.data:
        return APIEnvelope.failure("NOT_FOUND", f"Assessment '{assessment_id}' not found.")

    assessment = res.data

    # Fetch analysis steps
    try:
        steps_res = supabase_client.table("analysis_steps").select("*").eq(
            "assessment_id", assessment_id
        ).order("step_number", desc=False).execute()
        assessment["analysis_steps"] = steps_res.data or []
    except Exception:
        assessment["analysis_steps"] = []

    return APIEnvelope.success(assessment)

"""
backend/routers/analytics.py — MINDWATCH
GET /analytics/summary — dashboard stats
"""

import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter
from database import supabase_client
from models.schemas import APIEnvelope

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary", response_model=APIEnvelope[dict])
async def get_analytics_summary():
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    seven_days_ago = (now - timedelta(days=7)).isoformat()

    try:
        today_res = supabase_client.table("assessments").select("id", count="exact").gte("submitted_at", today_start).execute()
        total_today = today_res.count or 0
    except Exception:
        total_today = 0

    try:
        high_res = supabase_client.table("assessments").select("id", count="exact").in_(
            "risk_level", ["high", "crisis"]
        ).gte("submitted_at", today_start).execute()
        high_risk_today = high_res.count or 0
    except Exception:
        high_risk_today = 0

    try:
        alerts_res = supabase_client.table("risk_alerts").select("id", count="exact").eq("status", "open").execute()
        open_alerts = alerts_res.count or 0
    except Exception:
        open_alerts = 0

    # 7-day daily series
    daily_series = []
    try:
        all_recent = supabase_client.table("assessments").select("submitted_at,risk_level").gte("submitted_at", seven_days_ago).execute()
        by_day: dict = {}
        high_by_day: dict = {}
        for a in (all_recent.data or []):
            day = a["submitted_at"][:10]
            by_day[day] = by_day.get(day, 0) + 1
            if a.get("risk_level") in ("high", "crisis"):
                high_by_day[day] = high_by_day.get(day, 0) + 1
        for i in range(6, -1, -1):
            day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_series.append({"date": day, "assessments": by_day.get(day, 0), "high_risk": high_by_day.get(day, 0)})
    except Exception:
        for i in range(6, -1, -1):
            daily_series.append({"date": (now - timedelta(days=i)).strftime("%Y-%m-%d"), "assessments": 0, "high_risk": 0})

    # Emotion distribution
    emotion_dist = {}
    try:
        em_res = supabase_client.table("assessments").select("dominant_emotion").gte("submitted_at", seven_days_ago).execute()
        for a in (em_res.data or []):
            e = a.get("dominant_emotion", "unknown")
            emotion_dist[e] = emotion_dist.get(e, 0) + 1
    except Exception:
        pass

    return APIEnvelope.success({
        "total_assessments_today": total_today,
        "high_risk_today": high_risk_today,
        "open_alerts": open_alerts,
        "crisis_rate_today": round(high_risk_today / total_today, 4) if total_today > 0 else 0.0,
        "daily_series": daily_series,
        "emotion_distribution": emotion_dist,
    })

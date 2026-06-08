"""
backend/agent/tools.py — MINDWATCH
5 clinical analysis tools for the mental health assessment agent.
Anchor embeddings are pre-cached at module load time to avoid recomputing on every call.
"""

import json
import logging
from pydantic import BaseModel, Field
from langchain.tools import Tool
from database import supabase_client
from ml.embeddings import embeddings_service
from ml.crisis_scorer import DEPRESSION_ANCHORS, ANXIETY_ANCHORS, CRISIS_ANCHORS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pre-cache all anchor embeddings once at import time.
# Without this, analyze_symptom_patterns computes 26 embeddings on every call
# (26 × ~40ms = ~1s of blocking work per tool invocation).
# With the cache, the tool runs in <50ms total.
# ---------------------------------------------------------------------------
_ANCHOR_CACHE: dict[str, list] = {}


def _cached_embedding(text: str) -> list:
    if text not in _ANCHOR_CACHE:
        _ANCHOR_CACHE[text] = embeddings_service.get_embedding(text)
    return _ANCHOR_CACHE[text]


def _warm_anchor_cache():
    """Pre-compute embeddings for all anchor phrases."""
    all_anchors = DEPRESSION_ANCHORS + ANXIETY_ANCHORS + CRISIS_ANCHORS
    logger.info(f"Warming anchor embedding cache ({len(all_anchors)} phrases)...")
    for anchor in all_anchors:
        _cached_embedding(anchor)
    logger.info("Anchor cache ready.")


# Warm the anchor cache when explicitly called from main.py startup
# (NOT at import time — the embedding model may not be loaded yet)
def _warm_anchor_cache():
    """Pre-compute and cache embeddings for all DSM-5 anchor phrases."""
    all_anchors = DEPRESSION_ANCHORS + ANXIETY_ANCHORS + CRISIS_ANCHORS
    logger.info(f"Warming anchor embedding cache ({len(all_anchors)} phrases)...")
    # Batch encode all anchors at once — ~10x faster than encoding one by one
    embeddings = embeddings_service._model.encode(
        all_anchors, convert_to_numpy=True, show_progress_bar=False, batch_size=32
    )
    for anchor, emb in zip(all_anchors, embeddings):
        _ANCHOR_CACHE[anchor] = emb.tolist()
    logger.info(f"Anchor cache ready — {len(_ANCHOR_CACHE)} embeddings cached.")


# ---------------------------------------------------------------------------
# Tool 1: Analyze Symptom Patterns
# ---------------------------------------------------------------------------

class AnalyzeSymptomPatternsInput(BaseModel):
    text: str = Field(..., description="The text to analyze for DSM-5 symptom patterns")
    threshold: float = Field(default=0.45, description="Similarity threshold 0.0-1.0")


def _analyze_symptom_patterns(text: str, threshold: float = 0.45) -> str:
    try:
        text_emb = embeddings_service.get_embedding(text[:800])  # cap input length
        results = {"depression": [], "anxiety": [], "crisis": []}

        for anchor in DEPRESSION_ANCHORS:
            sim = embeddings_service.cosine_similarity(text_emb, _cached_embedding(anchor))
            if sim > threshold:
                results["depression"].append({"symptom": anchor[:80], "similarity": round(sim, 3)})

        for anchor in ANXIETY_ANCHORS:
            sim = embeddings_service.cosine_similarity(text_emb, _cached_embedding(anchor))
            if sim > threshold:
                results["anxiety"].append({"symptom": anchor[:80], "similarity": round(sim, 3)})

        for anchor in CRISIS_ANCHORS:
            sim = embeddings_service.cosine_similarity(text_emb, _cached_embedding(anchor))
            if sim > max(threshold - 0.1, 0.3):
                results["crisis"].append({"symptom": anchor[:80], "similarity": round(sim, 3)})

        # Limit results to top 3 per category to keep output short
        for k in results:
            results[k] = sorted(results[k], key=lambda x: x["similarity"], reverse=True)[:3]

        total = sum(len(v) for v in results.values())
        return json.dumps({"symptoms_found": total, "patterns": results})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Tool 2: Check Crisis Indicators
# ---------------------------------------------------------------------------

class CheckCrisisIndicatorsInput(BaseModel):
    text: str = Field(..., description="Text to check for acute crisis and suicidality signals")


def _check_crisis_indicators(text: str) -> str:
    try:
        text_lower = text.lower()
        CRISIS_PHRASES = [
            "kill myself", "end my life", "want to die", "don't want to live",
            "suicide", "suicidal", "self-harm", "cutting myself", "hurt myself",
            "no reason to live", "better off dead", "goodbye forever",
            "can't go on", "won't be here", "ending it all",
        ]
        PROTECTIVE_PHRASES = [
            "get help", "talk to someone", "therapy", "support", "family",
            "friends", "reasons to live", "tomorrow", "hope", "better",
        ]

        crisis_matches = [p for p in CRISIS_PHRASES if p in text_lower]
        protective_matches = [p for p in PROTECTIVE_PHRASES if p in text_lower]

        severity = "none"
        if len(crisis_matches) >= 3:
            severity = "severe"
        elif len(crisis_matches) >= 1:
            severity = "present"

        return json.dumps({
            "crisis_indicators_found": len(crisis_matches),
            "severity": severity,
            "matched_phrases": crisis_matches[:5],
            "protective_factors_found": len(protective_matches),
            "protective_phrases": protective_matches[:3],
            "immediate_safety_concern": severity in ("present", "severe"),
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Tool 3: Assess Temporal Patterns
# ---------------------------------------------------------------------------

class AssessTemporalPatternsInput(BaseModel):
    session_id: str = Field(..., description="Session UUID to analyze trajectory over time")


def _assess_temporal_patterns(session_id: str) -> str:
    # Guard against the agent passing "none", "null", "N/A" etc.
    if not session_id or session_id.lower() in ("none", "null", "n/a", "unknown", ""):
        return json.dumps({"status": "no_session_id", "message": "No session tracking for this assessment."})
    try:
        result = supabase_client.table("assessments").select(
            "crisis_score, risk_level, dominant_emotion, submitted_at"
        ).eq("session_id", session_id).order("submitted_at", desc=False).limit(10).execute()

        assessments = result.data or []
        if len(assessments) < 2:
            return json.dumps({"status": "insufficient_history", "assessments_found": len(assessments)})

        scores = [float(a.get("crisis_score") or 0) for a in assessments]
        trend = "stable"
        if len(scores) >= 3:
            recent_avg = sum(scores[-3:]) / 3
            early_avg = sum(scores[:3]) / 3
            if recent_avg > early_avg + 0.1:
                trend = "worsening"
            elif recent_avg < early_avg - 0.1:
                trend = "improving"

        return json.dumps({
            "assessments_analyzed": len(assessments),
            "trend": trend,
            "current_score": round(scores[-1], 3) if scores else 0,
            "peak_score": round(max(scores), 3),
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Tool 4: Get Resource Recommendations
# ---------------------------------------------------------------------------

class GetResourceRecommendationsInput(BaseModel):
    risk_level: str = Field(..., description="Risk level: safe | low | moderate | high | crisis")
    dominant_concern: str = Field(default="general", description="Primary concern type")


def _get_resource_recommendations(risk_level: str, dominant_concern: str = "general") -> str:
    RESOURCES = {
        "crisis": [
            {"name": "988 Suicide & Crisis Lifeline", "contact": "988 (call/text)", "type": "crisis"},
            {"name": "Crisis Text Line", "contact": "Text HOME to 741741", "type": "crisis"},
            {"name": "Emergency Services", "contact": "911", "type": "emergency"},
        ],
        "high": [
            {"name": "SAMHSA Helpline", "contact": "1-800-662-4357", "type": "mental_health"},
            {"name": "NAMI Helpline", "contact": "1-800-950-6264", "type": "support"},
            {"name": "Find a Therapist", "contact": "https://www.psychologytoday.com/us/therapists", "type": "therapy"},
        ],
        "moderate": [
            {"name": "BetterHelp Online Therapy", "contact": "https://www.betterhelp.com", "type": "therapy"},
            {"name": "7 Cups (free peer support)", "contact": "https://www.7cups.com", "type": "peer"},
            {"name": "Headspace (mindfulness)", "contact": "https://www.headspace.com", "type": "self_help"},
        ],
        "low": [
            {"name": "Woebot AI Support", "contact": "https://woebothealth.com", "type": "app"},
            {"name": "Calm App", "contact": "https://www.calm.com", "type": "self_help"},
        ],
        "safe": [
            {"name": "Mental Health America", "contact": "https://www.mhanational.org", "type": "education"},
        ],
    }
    level = risk_level.lower() if risk_level else "moderate"
    resources = RESOURCES.get(level, RESOURCES["moderate"])
    if level == "crisis":
        resources = RESOURCES["crisis"] + RESOURCES["high"][:1]
    return json.dumps({"risk_level": level, "resources": resources})


# ---------------------------------------------------------------------------
# Tool 5: Compute Text Similarity
# ---------------------------------------------------------------------------

class ComputeTextSimilarityInput(BaseModel):
    text: str = Field(..., description="Text to find similar historical assessments for")
    top_k: int = Field(default=3, description="Number of similar assessments to return")


def _compute_text_similarity(text: str, top_k: int = 3) -> str:
    try:
        query_emb = embeddings_service.get_embedding(text[:500])
        result = supabase_client.table("assessments").select(
            "id, input_text, crisis_score, risk_level"
        ).not_.is_("input_text", "null").limit(20).execute()  # reduced from 50

        assessments = result.data or []
        if not assessments:
            return json.dumps({"status": "no_history", "similar": []})

        scored = []
        for a in assessments:
            try:
                a_emb = embeddings_service.get_embedding(a["input_text"][:300])
                sim = embeddings_service.cosine_similarity(query_emb, a_emb)
                scored.append({
                    "similarity": round(sim, 3),
                    "risk_level": a.get("risk_level"),
                    "crisis_score": a.get("crisis_score"),
                })
            except Exception:
                pass

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return json.dumps({"similar_assessments": scored[:top_k]})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

ALL_TOOLS = [
    Tool(
        name="analyze_symptom_patterns",
        func=_analyze_symptom_patterns,
        description=(
            "Analyze text for DSM-5 clinical symptom patterns using semantic similarity. "
            "Returns matched symptoms across depression, anxiety, and crisis dimensions. "
            "Input: text (string)"
        ),
        args_schema=AnalyzeSymptomPatternsInput,
    ),
    Tool(
        name="check_crisis_indicators",
        func=_check_crisis_indicators,
        description=(
            "Scan text for explicit crisis and suicidality indicators. "
            "Returns severity level, matched phrases, and protective factors. "
            "Input: text (string)"
        ),
        args_schema=CheckCrisisIndicatorsInput,
    ),
    Tool(
        name="assess_temporal_patterns",
        func=_assess_temporal_patterns,
        description=(
            "Analyze a user's historical assessments to detect trend (improving/stable/worsening). "
            "Input: session_id (UUID string or 'none' if not available)"
        ),
        args_schema=AssessTemporalPatternsInput,
    ),
    Tool(
        name="get_resource_recommendations",
        func=_get_resource_recommendations,
        description=(
            "Get appropriate mental health resources for a given risk level. "
            "Always call this before your final answer. "
            "Input: risk_level (safe|low|moderate|high|crisis)"
        ),
        args_schema=GetResourceRecommendationsInput,
    ),
    Tool(
        name="compute_text_similarity",
        func=_compute_text_similarity,
        description=(
            "Find historically similar assessments for context. "
            "Input: text (string), top_k (int, default 3)"
        ),
        args_schema=ComputeTextSimilarityInput,
    ),
]

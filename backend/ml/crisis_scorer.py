"""
backend/ml/crisis_scorer.py
============================
PURPOSE:
    Multi-signal mental health crisis scoring engine.
    Combines THREE layers of analysis:

    LAYER 1 — Trained ML Models (scikit-learn):
        - PHQ-9 Severity Classifier: predicts depression severity (0-4 scale)
        - Crisis Risk Classifier: binary crisis detection (Random Forest)
        - Emotion Classifier: 8-class emotion prediction (Logistic Regression)
        Trained in ml/train_models.py, loaded once at startup.

    LAYER 2 — Semantic Similarity (sentence-transformers):
        Cosine similarity against 28 DSM-5 clinical anchor phrases.
        Captures meaning beyond keywords: "I have no reason to go on" ≈ suicidal
        even with no explicit crisis words.

    LAYER 3 — Keyword Pattern Matching:
        Direct scan for explicit crisis phrases. High recall for statements
        like "I want to kill myself" that should ALWAYS trigger crisis level.

    FUSION:
        Final crisis_score = weighted combination of all three layers.
        ML models ground the score in learned patterns.
        Semantic similarity catches nuanced expressions.
        Keyword matching ensures explicit statements are never missed.
"""

import logging
import os
from dataclasses import dataclass, field

import numpy as np

from ml.embeddings import embeddings_service

logger = logging.getLogger(__name__)

# ── DSM-5 Symptom Anchors (Semantic Layer) ────────────────────────────────────

DEPRESSION_ANCHORS = [
    "I feel hopeless and empty, like nothing will ever get better",
    "I have no motivation or energy to do anything",
    "I sleep too much or cannot sleep at all",
    "I feel worthless and guilty all the time",
    "I have lost interest in activities I used to enjoy",
    "I feel sad and tearful most of the day",
    "I have difficulty concentrating or making decisions",
    "I have lost my appetite and lost weight",
    "I feel like a burden to everyone around me",
    "Life doesn't feel worth living anymore",
]

ANXIETY_ANCHORS = [
    "I feel constantly worried and cannot stop my anxious thoughts",
    "I have panic attacks and feel like I cannot breathe",
    "I am afraid of social situations and avoid people",
    "I have racing thoughts and cannot calm down",
    "My heart pounds and I feel physically tense all the time",
    "I have nightmares and flashbacks to traumatic events",
    "I am terrified something terrible is about to happen",
    "I cannot control my worry no matter how hard I try",
]

CRISIS_ANCHORS = [
    "I want to kill myself and have thought about how to do it",
    "I am planning to end my life",
    "I have been cutting myself or hurting myself on purpose",
    "I don't want to be alive anymore",
    "I have a plan to commit suicide",
    "I am going to hurt myself tonight",
    "I see no reason to continue living",
    "I have been stockpiling medications to overdose",
]

EMOTION_ANCHORS = {
    "sadness":     "I feel deeply sad, heartbroken, and grief-stricken",
    "hopelessness":"Everything feels hopeless and futile, there is no point",
    "fear":        "I am terrified and paralyzed by fear and dread",
    "anger":       "I am filled with rage and overwhelming anger",
    "numbness":    "I feel completely empty and numb, nothing matters",
    "loneliness":  "I feel utterly alone and isolated from everyone",
    "shame":       "I feel deep shame and embarrassment about myself",
    "exhaustion":  "I am completely exhausted and drained of all energy",
}

# ── Trained ML Model Registry ─────────────────────────────────────────────────

class MLModelRegistry:
    """Holds the three trained sklearn models. Loaded once at startup."""
    def __init__(self):
        self.phq9_model = None        # GradientBoosting pipeline
        self.crisis_model = None      # RandomForest pipeline
        self.emotion_model = None     # LogisticRegression pipeline
        self.emotion_encoder = None   # LabelEncoder for emotion classes
        self._loaded = False

    def load(self, model_dir: str = "models") -> None:
        """Load all three models from disk if they exist."""
        import joblib

        phq9_path    = os.path.join(model_dir, "phq9_classifier.joblib")
        crisis_path  = os.path.join(model_dir, "crisis_classifier.joblib")
        emotion_path = os.path.join(model_dir, "emotion_classifier.joblib")

        if os.path.exists(phq9_path):
            self.phq9_model = joblib.load(phq9_path)
            logger.info("✅ PHQ-9 model loaded")
        else:
            logger.warning(f"PHQ-9 model not found at {phq9_path}. Run ml/train_models.py")

        if os.path.exists(crisis_path):
            self.crisis_model = joblib.load(crisis_path)
            logger.info("✅ Crisis model loaded")
        else:
            logger.warning(f"Crisis model not found at {crisis_path}. Run ml/train_models.py")

        if os.path.exists(emotion_path):
            saved = joblib.load(emotion_path)
            self.emotion_model   = saved["pipeline"]
            self.emotion_encoder = saved["label_encoder"]
            logger.info("✅ Emotion model loaded")
        else:
            logger.warning(f"Emotion model not found at {emotion_path}. Run ml/train_models.py")

        self._loaded = any([self.phq9_model, self.crisis_model, self.emotion_model])


ml_registry = MLModelRegistry()


# ── Dataclass for Results ──────────────────────────────────────────────────────

@dataclass
class CrisisScoreResult:
    crisis_score: float = 0.0
    depression_score: float = 0.0
    anxiety_score: float = 0.0
    crisis_signal: float = 0.0
    sentiment_score: float = 0.0
    dominant_emotion: str = "neutral"
    detected_symptoms: list[str] = field(default_factory=list)
    risk_level: str = "safe"
    # ML model outputs
    phq9_severity: str = "unknown"    # minimal/mild/moderate/moderately_severe/severe
    phq9_severity_score: int = 0      # 0-4
    crisis_ml_probability: float = 0.0
    emotion_ml: str = "unknown"
    ml_models_used: list[str] = field(default_factory=list)


# ── Anchor Embedding Cache ─────────────────────────────────────────────────────

_anchor_cache: dict = {}

def _get_anchor_embeddings(anchors: list[str], key: str) -> list[list[float]]:
    if key not in _anchor_cache:
        _anchor_cache[key] = [embeddings_service.get_embedding(a) for a in anchors]
    return _anchor_cache[key]


def _max_similarity(emb: list[float], anchor_embs: list[list[float]]) -> float:
    sims = [embeddings_service.cosine_similarity(emb, a) for a in anchor_embs]
    return max(sims) if sims else 0.0


def _mean_top_k(emb: list[float], anchor_embs: list[list[float]], k: int = 3) -> float:
    sims = sorted([embeddings_service.cosine_similarity(emb, a) for a in anchor_embs], reverse=True)
    return float(np.mean(sims[:k])) if sims else 0.0


def _simple_sentiment(text: str) -> float:
    pos = {"happy", "joy", "love", "grateful", "hope", "better", "good", "great", "peace", "calm"}
    neg = {"hate", "kill", "die", "worthless", "hopeless", "pain", "hurt", "terrible", "awful",
           "sad", "empty", "alone", "fail", "useless", "burden", "tired", "exhausted", "scared"}
    words = set(text.lower().split())
    p, n = len(words & pos), len(words & neg)
    t = p + n
    return round((p - n) / t, 4) if t > 0 else 0.0


# ── PHQ-9 label map ───────────────────────────────────────────────────────────
PHQ9_LABELS = {0: "minimal", 1: "mild", 2: "moderate", 3: "moderately_severe", 4: "severe"}


def score_text(text: str) -> CrisisScoreResult:
    """
    Score a piece of text using all three analysis layers.

    Args:
        text: Journal entry, chat message, or clinical note.

    Returns:
        CrisisScoreResult with all scored dimensions and ML predictions.
    """
    if not text or len(text.strip()) < 10:
        return CrisisScoreResult()

    result = CrisisScoreResult()
    models_used = []

    # ── LAYER 1: Trained ML Models ────────────────────────────────────────────

    if ml_registry.phq9_model is not None:
        try:
            phq9_pred = int(ml_registry.phq9_model.predict([text])[0])
            phq9_proba = ml_registry.phq9_model.predict_proba([text])[0]
            result.phq9_severity_score = phq9_pred
            result.phq9_severity = PHQ9_LABELS.get(phq9_pred, "unknown")
            # Map PHQ-9 severity to depression score (0-1)
            result.depression_score = round(phq9_pred / 4.0, 4)
            models_used.append("phq9_classifier")
        except Exception as e:
            logger.warning(f"PHQ-9 model failed: {e}")

    if ml_registry.crisis_model is not None:
        try:
            crisis_proba = ml_registry.crisis_model.predict_proba([text])[0]
            result.crisis_ml_probability = round(float(crisis_proba[1]), 4)
            models_used.append("crisis_classifier")
        except Exception as e:
            logger.warning(f"Crisis model failed: {e}")

    if ml_registry.emotion_model is not None and ml_registry.emotion_encoder is not None:
        try:
            emotion_pred = ml_registry.emotion_model.predict([text])[0]
            result.emotion_ml = ml_registry.emotion_encoder.inverse_transform([emotion_pred])[0]
            models_used.append("emotion_classifier")
        except Exception as e:
            logger.warning(f"Emotion model failed: {e}")

    # ── LAYER 2: Semantic Similarity ──────────────────────────────────────────

    text_emb = embeddings_service.get_embedding(text)

    dep_embs = _get_anchor_embeddings(DEPRESSION_ANCHORS, "depression")
    anx_embs = _get_anchor_embeddings(ANXIETY_ANCHORS, "anxiety")
    cri_embs = _get_anchor_embeddings(CRISIS_ANCHORS, "crisis")

    sem_depression = _mean_top_k(text_emb, dep_embs, k=3)
    sem_anxiety    = _mean_top_k(text_emb, anx_embs, k=3)
    sem_crisis     = _max_similarity(text_emb, cri_embs)

    # If ML models didn't run, fall back to semantic only
    if result.depression_score == 0.0:
        result.depression_score = round(sem_depression, 4)

    result.anxiety_score = round(sem_anxiety, 4)

    # Dominant emotion: ML model first, semantic fallback
    if result.emotion_ml == "unknown":
        emo_anchors = {k: embeddings_service.get_embedding(v) for k, v in EMOTION_ANCHORS.items()}
        emo_scores  = {k: embeddings_service.cosine_similarity(text_emb, v) for k, v in emo_anchors.items()}
        result.dominant_emotion = max(emo_scores, key=emo_scores.get)
    else:
        result.dominant_emotion = result.emotion_ml

    # ── LAYER 3: Keyword Matching ─────────────────────────────────────────────

    CRISIS_KEYWORDS = [
        "kill myself", "end my life", "want to die", "don't want to live",
        "suicide", "suicidal", "self-harm", "cutting myself",
        "no reason to live", "better off dead", "planning to", "goodbye forever",
    ]
    text_lower = text.lower()
    keyword_match = any(kw in text_lower for kw in CRISIS_KEYWORDS)
    keyword_crisis = 1.0 if keyword_match else 0.0

    # ── FUSION: Combine all layers ────────────────────────────────────────────

    # Crisis signal = max of (ML probability, semantic similarity, keyword match)
    # Taking max ensures ANY strong signal triggers high risk — this is intentional.
    # In mental health, false negatives (missing a real crisis) are more dangerous
    # than false positives.
    result.crisis_signal = round(
        max(result.crisis_ml_probability, sem_crisis, keyword_crisis),
        4
    )

    # Composite crisis score:
    # Crisis signal weighted highest (0.55) — any crisis indicator dominates
    # Depression weighted (0.25) — primary clinical concern
    # Anxiety weighted (0.20) — secondary concern
    result.crisis_score = round(min(1.0, max(0.0,
        0.55 * result.crisis_signal +
        0.25 * result.depression_score +
        0.20 * result.anxiety_score
    )), 4)

    # ── Detected Symptoms ────────────────────────────────────────────────────

    detected = []
    for anchor, emb in zip(DEPRESSION_ANCHORS, dep_embs):
        if embeddings_service.cosine_similarity(text_emb, emb) > 0.55:
            detected.append(anchor[:70] + "...")
    for anchor, emb in zip(ANXIETY_ANCHORS, anx_embs):
        if embeddings_service.cosine_similarity(text_emb, emb) > 0.55:
            detected.append(anchor[:70] + "...")
    result.detected_symptoms = detected[:5]

    # ── Risk Level ────────────────────────────────────────────────────────────

    if result.crisis_signal > 0.65 or keyword_match or result.crisis_score > 0.75:
        result.risk_level = "crisis"
    elif result.crisis_score > 0.55:
        result.risk_level = "high"
    elif result.crisis_score > 0.35 or result.phq9_severity in ("moderate", "moderately_severe", "severe"):
        result.risk_level = "moderate"
    elif result.crisis_score > 0.15 or result.phq9_severity == "mild":
        result.risk_level = "low"
    else:
        result.risk_level = "safe"

    result.sentiment_score = _simple_sentiment(text)
    result.ml_models_used = models_used

    return result

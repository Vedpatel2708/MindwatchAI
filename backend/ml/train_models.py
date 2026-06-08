"""
backend/ml/train_models.py
============================
PURPOSE:
    Trains three scikit-learn ML classifiers for mental health text analysis:

    1. PHQ-9 Severity Classifier  — depression severity (0-4 scale)
    2. Suicide Risk Classifier     — binary crisis detection
    3. Emotion Classifier          — 8-class emotion prediction

    Each model uses a TF-IDF vectorizer + classifier pipeline serialized
    to disk with joblib. The crisis_scorer.py loads these at startup.

WHY TF-IDF + SKLEARN (not fine-tuned BERT)?
    Fine-tuning BERT requires GPUs and hours of compute. TF-IDF + Logistic
    Regression / Random Forest trains in seconds on CPU, is fully
    interpretable (you can inspect which words drive predictions), and
    achieves strong performance on short clinical text.

    This is the same approach used in production triage tools — fast,
    explainable, reliable.

HOW TO RUN:
    cd backend
    python3 ml/generate_training_data.py   # create training data first
    python3 ml/train_models.py             # train all three models
"""

import json
import os
import logging
import joblib
import numpy as np

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.utils.class_weight import compute_class_weight

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")


def load_json(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def train_phq9_classifier():
    """
    PHQ-9 Depression Severity Classifier
    Input:  free text
    Output: 0=minimal, 1=mild, 2=moderate, 3=moderately_severe, 4=severe

    Model choice: Gradient Boosting — handles the ordinal nature of PHQ-9
    scores better than Logistic Regression. The severity levels have a
    natural ordering (mild → severe) that boosting captures well.
    """
    logger.info("Training PHQ-9 Severity Classifier...")
    data = load_json(os.path.join(DATA_DIR, "phq9_training.json"))
    texts = [d["text"] for d in data]
    labels = [d["label"] for d in data]

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 3),       # unigrams + bigrams + trigrams capture phrases
            max_features=5000,        # top 5000 most informative words/phrases
            sublinear_tf=True,        # log TF scaling reduces dominance of common words
            min_df=1,                 # include all terms (small dataset)
        )),
        ("clf", GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=3,
            random_state=42,
        )),
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    logger.info(f"PHQ-9 Classifier Report:\n{classification_report(y_test, y_pred, target_names=['minimal','mild','moderate','mod_severe','severe'])}")

    # Cross-validation for robust accuracy estimate
    cv_scores = cross_val_score(pipeline, texts, labels, cv=5, scoring='accuracy')
    logger.info(f"PHQ-9 CV Accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    path = os.path.join(MODEL_DIR, "phq9_classifier.joblib")
    joblib.dump(pipeline, path)
    logger.info(f"✅ PHQ-9 model saved: {path}")
    return pipeline


def train_crisis_classifier():
    """
    Suicide/Crisis Risk Binary Classifier
    Input:  free text
    Output: 0=no_crisis, 1=crisis

    Model choice: Random Forest with class_weight="balanced" — crisis texts
    are rare (by design) so we need to handle class imbalance. Balanced
    weights penalize misclassifying the minority crisis class more heavily.
    False negatives (missing a real crisis) are far more dangerous than
    false positives.
    """
    logger.info("Training Crisis Risk Classifier...")
    data = load_json(os.path.join(DATA_DIR, "crisis_training.json"))
    texts = [d["text"] for d in data]
    labels = [d["label"] for d in data]

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=3000,
            sublinear_tf=True,
        )),
        ("clf", RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",  # penalizes missing crisis class
            random_state=42,
            n_jobs=-1,                # use all CPU cores
        )),
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    logger.info(f"Crisis Classifier Report:\n{classification_report(y_test, y_pred, target_names=['no_crisis','crisis'])}")
    logger.info(f"Crisis AUC-ROC: {roc_auc_score(y_test, y_proba):.3f}")

    path = os.path.join(MODEL_DIR, "crisis_classifier.joblib")
    joblib.dump(pipeline, path)
    logger.info(f"✅ Crisis model saved: {path}")
    return pipeline


def train_emotion_classifier():
    """
    Multi-class Emotion Classifier
    Input:  free text
    Output: one of 8 emotions (sadness, anxiety, anger, hopelessness,
            loneliness, shame, numbness, neutral)

    Model choice: Logistic Regression (multinomial) — fast, interpretable,
    works well for text classification. The coefficients tell you exactly
    which words/phrases are most indicative of each emotion.
    """
    logger.info("Training Emotion Classifier...")
    data = load_json(os.path.join(DATA_DIR, "emotion_training.json"))
    texts = [d["text"] for d in data]
    labels = [d["label"] for d in data]

    le = LabelEncoder()
    encoded_labels = le.fit_transform(labels)

    X_train, X_test, y_train, y_test = train_test_split(
        texts, encoded_labels, test_size=0.2, random_state=42, stratify=encoded_labels
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=4000,
            sublinear_tf=True,
        )),
        ("clf", LogisticRegression(
            solver="lbfgs",
            max_iter=1000,
            C=1.0,
            random_state=42,
        )),
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    logger.info(f"Emotion Classifier Report:\n{classification_report(y_test, y_pred, target_names=le.classes_)}")

    # Save both the pipeline and the label encoder
    path = os.path.join(MODEL_DIR, "emotion_classifier.joblib")
    joblib.dump({"pipeline": pipeline, "label_encoder": le}, path)
    logger.info(f"✅ Emotion model saved: {path}")
    return pipeline, le


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)

    logger.info("=" * 60)
    logger.info("MINDWATCH — ML Model Training Pipeline")
    logger.info("=" * 60)

    # Check data exists
    for fname in ["phq9_training.json", "crisis_training.json", "emotion_training.json"]:
        path = os.path.join(DATA_DIR, fname)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Training data not found: {path}\n"
                f"Run: python3 ml/generate_training_data.py first"
            )

    train_phq9_classifier()
    train_crisis_classifier()
    train_emotion_classifier()

    logger.info("=" * 60)
    logger.info("✅ All models trained and saved to models/")
    logger.info("   Restart the API to load them: uvicorn main:app --reload")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

"""
backend/ml/embeddings.py
=========================
PURPOSE:
    Provides semantic text embeddings using the HuggingFace sentence-transformers
    library. Used by the agent's `compute_similarity_score` tool to find
    historically flagged fraud transactions that are semantically similar to
    the current transaction being investigated.

ARCHITECTURE ROLE:
    This module sits between the agent tools layer and the ML pipeline layer.
    The agent calls `embeddings_service.get_embedding(description)` to get a
    vector, then computes cosine similarity against stored fraud embeddings
    to find similar past cases — grounding the agent's reasoning in real data.

WHY all-MiniLM-L6-v2:
    - Only 80MB on disk (vs 400MB+ for larger models)
    - Runs on CPU in <50ms per embedding (no GPU needed)
    - State-of-art performance on the SBERT semantic similarity benchmark
    - Completely free — no API key, no internet after first download
    - 384-dimensional output vectors: compact enough for cosine similarity
      without losing meaningful semantic information
    (Requirement 12.9)

DESIGN DECISION — LAZY LOADING:
    The model is NOT loaded when this module is imported. It is loaded the
    first time `get_embedding()` is called. This avoids adding 2-3 seconds
    to FastAPI startup time on machines with slow disk I/O.
"""

# numpy: numerical array library for vector operations.
# We use it to convert embedding lists to arrays for cosine similarity math.
import numpy as np

# logging: standard Python logging — records model load events and errors.
import logging

# SentenceTransformer: loads and runs the all-MiniLM-L6-v2 model.
# On first run it downloads the model (~80MB) to ~/.cache/huggingface/
# On subsequent runs it loads from the local cache instantly.
from sentence_transformers import SentenceTransformer

# Type hints — improves readability and enables IDE autocompletion.
from typing import Optional

logger = logging.getLogger(__name__)

# The model identifier on HuggingFace Hub.
# This specific model is optimised for semantic sentence similarity tasks.
# "MiniLM" = Mini Language Model (distilled from a larger BERT model)
# "L6" = 6 transformer layers (vs 12 in full BERT — faster, smaller)
# "v2" = version 2 of the architecture (better than v1)
MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingsService:
    """
    Singleton service that computes semantic text embeddings.

    Uses lazy initialisation — the heavy SentenceTransformer model is only
    loaded from disk when the first embedding is requested, not at import time.

    WHY A CLASS INSTEAD OF MODULE-LEVEL FUNCTIONS?
        A class lets us encapsulate the model instance as `self._model`.
        This makes it easy to mock in tests (replace the whole instance)
        and makes the lazy-loading state explicit (self._model is None until loaded).

    Usage:
        from ml.embeddings import embeddings_service
        vec = embeddings_service.get_embedding("Large electronics purchase")
        score = embeddings_service.cosine_similarity(vec, other_vec)
    """

    def __init__(self):
        """
        Initialise the service without loading the model yet.

        self._model starts as None — it will be set on the first call
        to get_embedding() via the _load_model() lazy loader.
        """
        # _model holds the SentenceTransformer instance once loaded.
        # None signals "not yet loaded" — checked in _load_model().
        self._model: Optional[SentenceTransformer] = None

    def _load_model(self) -> None:
        """
        Load the sentence-transformer model if not already loaded.

        Called internally before every embedding computation.
        After the first call, self._model is set and this becomes a no-op.

        WHY LAZY LOADING?
            Loading SentenceTransformer takes 1-3 seconds on first use.
            If we load it at module import time, FastAPI startup is delayed
            even if the agent never runs. Lazy loading defers this cost
            until the first actual investigation.

        Side effects:
            Sets self._model to a loaded SentenceTransformer instance.
        """
        if self._model is None:
            logger.info(f"Loading embedding model '{MODEL_NAME}' (first use)...")

            # SentenceTransformer(model_name) downloads the model on first call
            # and caches it in ~/.cache/huggingface/sentence_transformers/
            # Subsequent calls load from the local cache (~instant).
            self._model = SentenceTransformer(MODEL_NAME)

            logger.info(f"Embedding model '{MODEL_NAME}' loaded successfully.")

    def get_embedding(self, text: str) -> list[float]:
        """
        Compute a 384-dimensional semantic embedding vector for the given text.

        The embedding captures the MEANING of the text, not just the words.
        Two semantically similar texts will have vectors close together in
        384-dimensional space, even if they share no words.

        Example:
            "iPhone purchase" and "electronics retail — mobile device" will
            have high cosine similarity despite sharing zero words.

        Args:
            text: The text to embed. Typically a transaction description
                  like "Large purchase at Electronics Plus".

        Returns:
            list[float]: A list of 384 floats representing the semantic
                         meaning of the text. All values are in [-1.0, 1.0].

        Performance:
            ~30-50ms on CPU for a single sentence.
            The model is loaded lazily on the first call (~1-3s extra).
        """
        # Ensure the model is loaded before we try to use it.
        self._load_model()

        # encode() takes a string (or list of strings) and returns a numpy array.
        # convert_to_numpy=True ensures we get a numpy array, not a tensor.
        # We then convert to a plain Python list for JSON serialisation.
        embedding_array: np.ndarray = self._model.encode(
            text,
            convert_to_numpy=True,
            show_progress_bar=False  # suppress tqdm progress bar for single strings
        )

        # tolist() converts numpy array to a regular Python list of floats.
        # This is important because numpy arrays can't be serialised to JSON
        # directly — regular Python lists can.
        return embedding_array.tolist()

    def cosine_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        """
        Compute cosine similarity between two embedding vectors.

        Cosine similarity measures the angle between two vectors in high-
        dimensional space. It ranges from -1.0 (opposite) to 1.0 (identical).
        For fraud similarity, scores above 0.85 indicate very similar patterns.

        WHY COSINE SIMILARITY (not Euclidean distance)?
            Cosine similarity is scale-invariant — it measures direction, not
            magnitude. Two embeddings for short vs long descriptions of the
            same event will have similar cosine similarity even if their
            magnitude (vector length) differs. Euclidean distance would
            incorrectly penalise vectors with different lengths.

        Args:
            vec_a: First embedding vector (384 floats).
            vec_b: Second embedding vector (384 floats).

        Returns:
            float: Cosine similarity score in [-1.0, 1.0].
                   Typical fraud similarity threshold: > 0.80
        """
        # Convert Python lists to numpy arrays for efficient vectorised math.
        a = np.array(vec_a)
        b = np.array(vec_b)

        # Cosine similarity formula:
        # cos(θ) = (A · B) / (‖A‖ × ‖B‖)
        # where A · B is the dot product and ‖A‖ is the L2 norm (magnitude).

        # dot product: element-wise multiplication then sum
        dot_product = np.dot(a, b)

        # norm: square root of sum of squares (Euclidean length of vector)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        # Guard against division by zero (empty/zero vectors)
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        # Clip to [-1, 1] to handle floating-point precision edge cases
        # (e.g., dot/(norm*norm) might return 1.0000000001 due to float arithmetic)
        similarity = float(dot_product / (norm_a * norm_b))
        return float(np.clip(similarity, -1.0, 1.0))


# ---------------------------------------------------------------------------
# MODULE-LEVEL SINGLETON
# ---------------------------------------------------------------------------
# Create one shared instance — all agent tools share this instance.
# The model itself won't load until the first get_embedding() call.
embeddings_service = EmbeddingsService()

"""
Embedding service — loads sentence-transformers/all-MiniLM-L6-v2 once at
startup and exposes a single embed() function returning a 384-dim vector.

The model is cached in module-level state. Calling embed() after load() is
called is safe from any thread/coroutine — the model object is read-only
after initialization.
"""

import logging
from sentence_transformers import SentenceTransformer

log = logging.getLogger(__name__)

_model: SentenceTransformer | None = None

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load() -> None:
    """Load the model into memory. Must be called once at app startup."""
    global _model
    log.info("loading embedding model", extra={"model": MODEL_NAME})
    _model = SentenceTransformer(MODEL_NAME)
    log.info("embedding model ready", extra={"model": MODEL_NAME, "dims": 384})


def embed(text: str) -> list[float]:
    """
    Embed a single string and return a 384-dimensional vector.

    Raises RuntimeError if load() has not been called.
    """
    if _model is None:
        raise RuntimeError("Embedding model not loaded — call load() at startup")
    vector = _model.encode(text, normalize_embeddings=True)
    return vector.tolist()

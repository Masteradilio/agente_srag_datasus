import logging
from collections.abc import Sequence
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_MODEL_INSTANCE: Any = None


class HuggingFaceLocalEmbeddings:
    """Local, open-source Hugging Face embedding model using sentence-transformers."""

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        self.model_name = model_name
        self._model = None

    def _get_model(self) -> Any:
        global _MODEL_INSTANCE
        if _MODEL_INSTANCE is not None:
            return _MODEL_INSTANCE
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]

            logger.info("Loading HuggingFace embedding model: %s", self.model_name)
            _MODEL_INSTANCE = SentenceTransformer(self.model_name)
            return _MODEL_INSTANCE
        except Exception as exc:
            logger.warning("Could not load SentenceTransformer (%s). Using deterministic lexical embedding.", exc)
            return None

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        model = self._get_model()
        if model is not None:
            try:
                embeddings = model.encode(list(texts), convert_to_numpy=True, normalize_embeddings=True)
                return [arr.tolist() for arr in embeddings]
            except Exception as exc:
                logger.warning("Embedding encoding failed (%s). Falling back.", exc)

        return [_deterministic_pseudo_embedding(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def _deterministic_pseudo_embedding(text: str, dim: int = 384) -> list[float]:
    """Fallback deterministic float vector for offline environments without heavy weights."""
    import hashlib

    vector = [0.0] * dim
    words = text.lower().split()
    for i, word in enumerate(words):
        h = int(hashlib.md5(word.encode()).hexdigest(), 16)
        idx = h % dim
        vector[idx] += 1.0 / (1.0 + (i * 0.1))

    # Normalize
    norm = sum(x * x for x in vector) ** 0.5
    if norm > 0:
        vector = [x / norm for x in vector]
    return vector

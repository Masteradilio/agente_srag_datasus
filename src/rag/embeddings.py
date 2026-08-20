import logging
import os
from collections.abc import Sequence
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_MODEL_INSTANCE: Any = None
_CHECKED_AVAILABLE: bool = False
_IS_AVAILABLE: bool = False


class HuggingFaceLocalEmbeddings:
    """Local embedding model with automatic graceful fallback for high speed and zero DLL issues."""

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        self.model_name = model_name
        self._model = None

    def _get_model(self) -> Any:
        global _MODEL_INSTANCE, _CHECKED_AVAILABLE, _IS_AVAILABLE
        if _MODEL_INSTANCE is not None:
            return _MODEL_INSTANCE
        if _CHECKED_AVAILABLE and not _IS_AVAILABLE:
            return None

        _CHECKED_AVAILABLE = True

        # Check torch viability first before sentence_transformers triggers heavy module scans
        try:
            import torch  # type: ignore[import-untyped]

            _test = torch.zeros(1)
            if _test.numel() != 1:
                _IS_AVAILABLE = False
                return None
        except Exception:
            _IS_AVAILABLE = False
            return None

        try:
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
            os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
            from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]

            _MODEL_INSTANCE = SentenceTransformer(self.model_name)
            _IS_AVAILABLE = True
            return _MODEL_INSTANCE
        except Exception:
            _IS_AVAILABLE = False
            return None

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        model = self._get_model()
        if model is not None:
            try:
                embeddings = model.encode(list(texts), convert_to_numpy=True, normalize_embeddings=True)
                return [arr.tolist() for arr in embeddings]
            except Exception:
                pass

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

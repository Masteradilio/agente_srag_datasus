import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from data.schema import DocumentChunk, RetrievedDocument
from rag.embeddings import HuggingFaceLocalEmbeddings
from utils.paths import ensure_directory

logger = logging.getLogger(__name__)

COLLECTION_NAME = "srag_knowledge_base"


class ChromaVectorStore:
    """Vector Store integrating Hugging Face embeddings with dense cosine similarity and JSON persistence."""

    def __init__(
        self,
        persist_dir: Path = Path("artifacts/vector_store"),
        embeddings: HuggingFaceLocalEmbeddings | None = None,
    ) -> None:
        self.persist_dir = persist_dir
        self.embeddings = embeddings or HuggingFaceLocalEmbeddings()
        self.index_path = persist_dir / "index.json"
        self.embeddings_path = persist_dir / "embeddings.npy"
        self._chunks: list[DocumentChunk] = []
        self._vectors: np.ndarray | None = None

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        self._chunks = list(chunks)
        if not chunks:
            self._vectors = None
            return

        texts = [chunk.content for chunk in chunks]
        vecs = self.embeddings.embed_documents(texts)
        self._vectors = np.array(vecs, dtype=np.float32)
        self.persist()

    def persist(self) -> Path:
        ensure_directory(self.persist_dir)
        self.index_path.write_text(
            json.dumps([c.model_dump(mode="json") for c in self._chunks], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if self._vectors is not None:
            np.save(str(self.embeddings_path), self._vectors)
        return self.index_path

    def load(self) -> None:
        if self.index_path.is_file():
            payload = json.loads(self.index_path.read_text(encoding="utf-8"))
            self._chunks = [DocumentChunk.model_validate(item) for item in payload]
        else:
            self._chunks = []

        if self.embeddings_path.is_file():
            try:
                self._vectors = np.load(str(self.embeddings_path))
            except Exception:
                self._vectors = None
        elif self._chunks:
            texts = [c.content for c in self._chunks]
            vecs = self.embeddings.embed_documents(texts)
            self._vectors = np.array(vecs, dtype=np.float32)

    def search(self, query: str, top_k: int = 5) -> list[RetrievedDocument]:
        if not self._chunks:
            return []

        if self._vectors is None or len(self._vectors) != len(self._chunks):
            texts = [c.content for c in self._chunks]
            vecs = self.embeddings.embed_documents(texts)
            self._vectors = np.array(vecs, dtype=np.float32)

        query_vec = np.array(self.embeddings.embed_query(query), dtype=np.float32)
        # Compute cosine similarity
        norm_q = np.linalg.norm(query_vec)
        if norm_q > 0:
            query_vec = query_vec / norm_q

        norms_docs = np.linalg.norm(self._vectors, axis=1, keepdims=True)
        norms_docs[norms_docs == 0] = 1.0
        normalized_docs = self._vectors / norms_docs

        sims = np.dot(normalized_docs, query_vec)
        ranked_indices = np.argsort(sims)[::-1][:top_k]

        results: list[RetrievedDocument] = []
        for idx in ranked_indices:
            score = float(round(float(sims[idx]), 4))
            chunk = self._chunks[idx]
            results.append(
                RetrievedDocument(
                    chunk_id=chunk.chunk_id,
                    source_path=chunk.source_path,
                    source_type=chunk.source_type,
                    content=chunk.content,
                    score=max(0.01, score),
                    metadata=chunk.metadata,
                )
            )
        return results


# Alias for backward compatibility
LocalVectorStore = ChromaVectorStore


def build_vector_store(
    chunks: list[DocumentChunk],
    persist_dir: Path = Path("artifacts/vector_store"),
) -> ChromaVectorStore:
    store = ChromaVectorStore(persist_dir=persist_dir)
    store.add_chunks(chunks)
    store.persist()
    return store

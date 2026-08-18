import re
from pathlib import Path
from typing import Any

from data.schema import DocumentChunk, RetrievedDocument
from rag.chunking import chunk_documents
from rag.loaders import load_project_documents
from rag.vector_store import ChromaVectorStore, build_vector_store


class BM25Retriever:
    """Sparse lexical retriever using BM25Okapi."""

    def __init__(self, chunks: list[DocumentChunk]) -> None:
        self.chunks = chunks
        self._corpus = [self._tokenize(c.content) for c in chunks]
        self._bm25 = None
        if self._corpus:
            try:
                from rank_bm25 import BM25Okapi  # type: ignore[import-untyped]

                self._bm25 = BM25Okapi(self._corpus)
            except Exception:
                self._bm25 = None

    def search(self, query: str, top_k: int = 5) -> list[RetrievedDocument]:
        if not self.chunks:
            return []
        tokenized_query = self._tokenize(query)
        if not tokenized_query or self._bm25 is None:
            return []

        scores = self._bm25.get_scores(tokenized_query)
        scored_pairs = sorted(
            enumerate(scores),
            key=lambda item: item[1],
            reverse=True,
        )[:top_k]

        results: list[RetrievedDocument] = []
        for idx, score in scored_pairs:
            chunk = self.chunks[idx]
            doc_terms = set(self._corpus[idx])
            if not doc_terms.intersection(tokenized_query):
                continue
            results.append(
                RetrievedDocument(
                    chunk_id=chunk.chunk_id,
                    source_path=chunk.source_path,
                    source_type=chunk.source_type,
                    content=chunk.content,
                    score=float(round(max(0.01, score), 4)),
                    metadata=chunk.metadata,
                )
            )
        return results

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"\w{2,}", text.lower())


def retrieve_context_hybrid(
    query: str,
    top_k: int = 5,
    persist_dir: Path = Path("artifacts/vector_store"),
    chunks: list[DocumentChunk] | None = None,
) -> list[RetrievedDocument]:
    """Hybrid search combining Dense ChromaDB embeddings and Sparse BM25 via Reciprocal Rank Fusion."""
    store = ChromaVectorStore(persist_dir=persist_dir)
    store.load()
    dense_results = store.search(query, top_k=top_k * 2)

    # BM25 sparse results
    available_chunks = chunks or getattr(store, "_fallback_chunks", [])
    bm25_retriever = BM25Retriever(available_chunks)
    sparse_results = bm25_retriever.search(query, top_k=top_k * 2)

    if not dense_results and not sparse_results:
        # Auto-index if database empty
        store = index_project_context(persist_dir=persist_dir)
        return store.search(query, top_k=top_k)

    # Reciprocal Rank Fusion (RRF)
    rrf_scores: dict[str, float] = {}
    doc_map: dict[str, RetrievedDocument] = {}

    for rank, doc in enumerate(dense_results):
        doc_map[doc.chunk_id] = doc
        rrf_scores[doc.chunk_id] = rrf_scores.get(doc.chunk_id, 0.0) + (1.0 / (60.0 + rank + 1.0))

    for rank, doc in enumerate(sparse_results):
        doc_map[doc.chunk_id] = doc
        rrf_scores[doc.chunk_id] = rrf_scores.get(doc.chunk_id, 0.0) + (1.0 / (60.0 + rank + 1.0))

    ranked_chunk_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:top_k]

    fused_docs: list[RetrievedDocument] = []
    for cid in ranked_chunk_ids:
        doc = doc_map[cid]
        doc.score = round(rrf_scores[cid] * 100.0, 4)
        fused_docs.append(doc)

    return fused_docs


def index_project_context(
    run_id: str | None = None,
    persist_dir: Path = Path("artifacts/vector_store"),
) -> ChromaVectorStore:
    documents = load_project_documents(run_id=run_id)
    chunks = chunk_documents(documents)
    return build_vector_store(chunks, persist_dir=persist_dir)


def retrieve_context(
    query: str,
    top_k: int = 5,
    persist_dir: Path = Path("artifacts/vector_store"),
) -> list[RetrievedDocument]:
    return retrieve_context_hybrid(query=query, top_k=top_k, persist_dir=persist_dir)

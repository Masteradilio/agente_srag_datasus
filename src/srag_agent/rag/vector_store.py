import json
import re
from collections import Counter
from pathlib import Path

from srag_agent.data.schema import DocumentChunk, RetrievedDocument
from srag_agent.utils.paths import ensure_directory


class LocalVectorStore:
    def __init__(self, persist_dir: Path = Path("artifacts/vector_store")) -> None:
        self.persist_dir = persist_dir
        self.index_path = persist_dir / "index.json"
        self._chunks: list[DocumentChunk] = []

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        self._chunks = chunks

    def persist(self) -> Path:
        ensure_directory(self.persist_dir)
        self.index_path.write_text(
            json.dumps(
                [chunk.model_dump(mode="json") for chunk in self._chunks],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return self.index_path

    def load(self) -> None:
        if not self.index_path.is_file():
            self._chunks = []
            return
        payload = json.loads(self.index_path.read_text(encoding="utf-8"))
        self._chunks = [DocumentChunk.model_validate(item) for item in payload]

    def search(self, query: str, top_k: int = 5) -> list[RetrievedDocument]:
        query_terms = _tokenize(query)
        scored: list[RetrievedDocument] = []
        for chunk in self._chunks:
            score = _lexical_score(query_terms, chunk.content)
            if score <= 0:
                continue
            scored.append(
                RetrievedDocument(
                    chunk_id=chunk.chunk_id,
                    source_path=chunk.source_path,
                    source_type=chunk.source_type,
                    content=chunk.content,
                    score=score,
                    metadata=chunk.metadata,
                )
            )
        return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]


def build_vector_store(
    chunks: list[DocumentChunk],
    persist_dir: Path = Path("artifacts/vector_store"),
) -> LocalVectorStore:
    store = LocalVectorStore(persist_dir=persist_dir)
    store.add_chunks(chunks)
    store.persist()
    return store


def _tokenize(text: str) -> Counter[str]:
    return Counter(re.findall(r"[a-zA-ZÀ-ÿ0-9_]{3,}", text.lower()))


def _lexical_score(query_terms: Counter[str], content: str) -> float:
    if not query_terms:
        return 0.0
    content_terms = _tokenize(content)
    return float(sum(content_terms.get(term, 0) * weight for term, weight in query_terms.items()))

from pathlib import Path

from data.schema import RetrievedDocument
from rag.chunking import chunk_documents
from rag.loaders import load_project_documents
from rag.vector_store import LocalVectorStore, build_vector_store


def index_project_context(
    run_id: str | None = None,
    persist_dir: Path = Path("artifacts/vector_store"),
) -> LocalVectorStore:
    documents = load_project_documents(run_id=run_id)
    chunks = chunk_documents(documents)
    return build_vector_store(chunks, persist_dir=persist_dir)


def retrieve_context(
    query: str,
    top_k: int = 5,
    persist_dir: Path = Path("artifacts/vector_store"),
) -> list[RetrievedDocument]:
    store = LocalVectorStore(persist_dir=persist_dir)
    store.load()
    if not store.search(query, top_k=1):
        store = index_project_context(persist_dir=persist_dir)
    return store.search(query, top_k=top_k)


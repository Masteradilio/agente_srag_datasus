from srag_agent.rag.chunking import chunk_document, chunk_documents
from srag_agent.rag.loaders import load_project_documents, load_text_document


def test_load_text_document_has_metadata() -> None:
    document = load_text_document("README.md")

    assert document is not None
    assert document.source_path == "README.md"
    assert document.metadata["filename"] == "README.md"


def test_load_project_documents_includes_core_docs() -> None:
    documents = load_project_documents()
    paths = {document.source_path for document in documents}

    assert "README.md" in paths
    assert "MASTER_BACKLOG.md" in paths
    assert "configs/metric_catalog.yaml" in paths


def test_chunk_document_preserves_source_metadata() -> None:
    document = load_text_document("configs/metric_catalog.yaml")
    assert document is not None

    chunks = chunk_document(document, max_chars=200, overlap=20)

    assert chunks
    assert chunks[0].source_path == "configs/metric_catalog.yaml"
    assert "section_index" in chunks[0].metadata


def test_chunk_documents() -> None:
    documents = load_project_documents(document_paths=["README.md"])

    assert chunk_documents(documents, max_chars=300)

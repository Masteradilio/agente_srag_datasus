from srag_agent.data.schema import DocumentSource
from srag_agent.rag.chunking import chunk_documents
from srag_agent.rag.retriever import retrieve_context
from srag_agent.rag.vector_store import LocalVectorStore, build_vector_store


def test_vector_store_persists_and_retrieves_fixture(tmp_path) -> None:
    documents = [
        DocumentSource(
            source_path="fixture.md",
            source_type="markdown",
            content="A metrica de UTI deve ser tratada como proporcao de casos com UTI.",
        )
    ]
    chunks = chunk_documents(documents, max_chars=200)
    store = build_vector_store(chunks, persist_dir=tmp_path / "vector_store")

    loaded = LocalVectorStore(persist_dir=tmp_path / "vector_store")
    loaded.load()
    results = loaded.search("UTI proporcao", top_k=1)

    assert store.index_path.is_file()
    assert results
    assert results[0].source_path == "fixture.md"


def test_retrieve_context_returns_source(tmp_path) -> None:
    documents = [
        DocumentSource(
            source_path="fixture.md",
            source_type="markdown",
            content="Vacinação registrada entre casos nao e cobertura populacional.",
        )
    ]
    build_vector_store(chunk_documents(documents), persist_dir=tmp_path / "vector_store")

    results = retrieve_context(
        "vacinacao cobertura",
        top_k=2,
        persist_dir=tmp_path / "vector_store",
    )

    assert results
    assert results[0].source_path == "fixture.md"

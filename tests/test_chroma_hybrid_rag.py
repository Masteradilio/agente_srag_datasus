from pathlib import Path

from data.schema import DocumentChunk
from rag.embeddings import HuggingFaceLocalEmbeddings
from rag.retriever import BM25Retriever, retrieve_context_hybrid
from rag.vector_store import ChromaVectorStore, build_vector_store


def test_huggingface_local_embeddings() -> None:
    embeddings = HuggingFaceLocalEmbeddings()
    texts = ["Vigilância epidemiológica de SRAG no Brasil.", "Mortalidade e leitos de UTI."]
    vectors = embeddings.embed_documents(texts)

    assert len(vectors) == 2
    assert len(vectors[0]) > 0
    query_vec = embeddings.embed_query("SRAG")
    assert len(query_vec) == len(vectors[0])


def test_chroma_vector_store_persistence(tmp_path: Path) -> None:
    chunks = [
        DocumentChunk(
            chunk_id="chunk-1",
            source_path="docs/metric_catalog.md",
            source_type="doc",
            content="A taxa de mortalidade conhecida mede o percentual de óbitos em relação aos casos com desfecho.",
            metadata={"domain": "epidemiology"},
        ),
        DocumentChunk(
            chunk_id="chunk-2",
            source_path="README.md",
            source_type="doc",
            content="Instruções de instalação do pipeline com ambiente virtual e pytest.",
            metadata={"domain": "setup"},
        ),
    ]

    store = build_vector_store(chunks, persist_dir=tmp_path / "chroma_test")
    results = store.search("mortalidade e desfecho", top_k=1)

    assert len(results) >= 1
    assert "mortalidade" in results[0].content.lower()


def test_bm25_and_hybrid_retrieval(tmp_path: Path) -> None:
    chunks = [
        DocumentChunk(
            chunk_id="c-vsr",
            source_path="report.md",
            source_type="report",
            content="O Vírus Sincicial Respiratório (VSR) teve alta incidência em crianças menores de dois anos.",
            metadata={"pathogen": "VSR"},
        ),
        DocumentChunk(
            chunk_id="c-flu",
            source_path="report.md",
            source_type="report",
            content="Casos de Influenza A apresentaram estabilização na última semana epidemiológica.",
            metadata={"pathogen": "Influenza"},
        ),
    ]

    bm25 = BM25Retriever(chunks)
    sparse_res = bm25.search("Vírus Sincicial VSR crianças", top_k=1)
    assert len(sparse_res) == 1
    assert sparse_res[0].chunk_id == "c-vsr"

    hybrid_res = retrieve_context_hybrid(
        query="Vírus Sincicial VSR",
        top_k=2,
        persist_dir=tmp_path / "hybrid_test",
        chunks=chunks,
    )
    assert len(hybrid_res) >= 1
    assert hybrid_res[0].chunk_id == "c-vsr"
    assert hybrid_res[0].score > 0

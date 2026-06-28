from pathlib import Path

from data.schema import DocumentSource
from utils.paths import resolve_project_path

DEFAULT_DOCUMENT_PATHS = [
    "README.md",
    "docs/PRD_srag_genai_agent.md",
    "MASTER_BACKLOG.md",
    "configs/metric_catalog.yaml",
    "docs/limitations.md",
]


def load_text_document(path: str | Path, source_type: str | None = None) -> DocumentSource | None:
    document_path = resolve_project_path(path)
    if not document_path.is_file():
        return None

    return DocumentSource(
        source_path=str(Path(path).as_posix()),
        source_type=source_type or _infer_source_type(document_path),
        content=document_path.read_text(encoding="utf-8"),
        metadata={"filename": document_path.name},
    )


def load_run_documents(
    run_id: str,
    artifacts_dir: Path = Path("artifacts/runs"),
) -> list[DocumentSource]:
    documents: list[DocumentSource] = []
    for relative_path in [
        artifacts_dir / run_id / "news_sources.json",
        artifacts_dir / run_id / "report.md",
    ]:
        document = load_text_document(relative_path, source_type="run_artifact")
        if document:
            documents.append(document)
    return documents


def load_project_documents(
    run_id: str | None = None,
    document_paths: list[str | Path] | None = None,
) -> list[DocumentSource]:
    documents = [
        document
        for path in (document_paths or DEFAULT_DOCUMENT_PATHS)
        if (document := load_text_document(path))
    ]
    if run_id:
        documents.extend(load_run_documents(run_id))
    return documents


def _infer_source_type(path: Path) -> str:
    if path.suffix.lower() in {".yaml", ".yml"}:
        return "config"
    if path.suffix.lower() == ".json":
        return "json"
    if path.suffix.lower() == ".md":
        return "markdown"
    return "text"


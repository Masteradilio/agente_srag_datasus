import json
import os
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from utils.hashing import calculate_sha256
from utils.paths import ensure_directory, resolve_project_path

PROMPT_VERSION = "agent-report-v1"
METRIC_CATALOG_VERSION = "metric-catalog-v1"
ALLOWLIST_VERSION = "news-allowlist-v1"


class ExecutionManifest(BaseModel):
    run_id: str
    timestamp: str
    selected_folder: str | None
    source_file: str | None
    raw_file_hash: str | None
    refined_file_hash: str | None
    rows_raw: int | None
    rows_refined: int | None
    model: str | None
    embedding_model: str | None
    prompt_version: str
    metric_catalog_version: str
    allowlist_version: str


def build_execution_manifest(
    *,
    run_id: str,
    selected_folder: str | None = None,
    source_file: str | Path | None = None,
    raw_file_hash: str | None = None,
    refined_file: str | Path | None = None,
    rows_raw: int | None = None,
    rows_refined: int | None = None,
    model: str | None = None,
    embedding_model: str | None = None,
) -> ExecutionManifest:
    refined_hash = None
    if refined_file is not None:
        refined_path = resolve_project_path(refined_file)
        if refined_path.is_file():
            refined_hash = calculate_sha256(refined_path)

    return ExecutionManifest(
        run_id=run_id,
        timestamp=datetime.now(UTC).isoformat(),
        selected_folder=selected_folder,
        source_file=str(source_file) if source_file is not None else None,
        raw_file_hash=raw_file_hash,
        refined_file_hash=refined_hash,
        rows_raw=rows_raw,
        rows_refined=rows_refined,
        model=model or os.getenv("LLM_MODEL"),
        embedding_model=embedding_model or os.getenv("EMBEDDING_MODEL"),
        prompt_version=PROMPT_VERSION,
        metric_catalog_version=METRIC_CATALOG_VERSION,
        allowlist_version=ALLOWLIST_VERSION,
    )


def write_execution_manifest(
    manifest: ExecutionManifest,
    artifacts_dir: Path = Path("artifacts/runs"),
) -> Path:
    run_dir = ensure_directory(resolve_project_path(artifacts_dir) / manifest.run_id)
    output_path = run_dir / "manifest.json"
    output_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path



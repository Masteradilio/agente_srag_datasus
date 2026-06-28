import argparse
import json
from pathlib import Path

from pydantic import BaseModel

from agents.graph import run_agent_graph
from audit.manifest import build_execution_manifest, write_execution_manifest
from config import load_settings
from data.ingestion import run_ingestion
from data.preprocessing import run_preprocessing
from reporting.pdf_exporter import export_report_pdf
from utils.hashing import calculate_sha256
from utils.paths import ensure_directory, resolve_project_path


class PipelineResult(BaseModel):
    run_id: str
    artifacts_dir: Path
    manifest_path: Path
    report_markdown_path: Path
    report_pdf_path: Path


def run_pipeline(
    *,
    run_id: str | None = None,
    raw_file: Path | None = None,
) -> PipelineResult:
    settings = load_settings()

    if raw_file is None:
        ingestion = run_ingestion(run_id=run_id, settings=settings)
        current_run_id = ingestion.run_id
        raw_path = ingestion.raw_file_path
        selected_folder = ingestion.selected_folder
        raw_hash = ingestion.raw_file_hash
    else:
        raw_path = resolve_project_path(raw_file)
        if not raw_path.is_file():
            raise FileNotFoundError(f"Raw file not found: {raw_path}")
        current_run_id = run_id or raw_path.parent.name
        selected_folder = "local-raw-file"
        raw_hash = calculate_sha256(raw_path)

    preprocessing = run_preprocessing(raw_path, current_run_id, settings=settings)
    artifacts_root = resolve_project_path(settings.paths.artifacts_dir)
    run_dir = ensure_directory(artifacts_root / current_run_id)

    manifest = build_execution_manifest(
        run_id=current_run_id,
        selected_folder=selected_folder,
        source_file=raw_path,
        raw_file_hash=raw_hash,
        refined_file=preprocessing.parquet_path,
        rows_raw=preprocessing.rows_raw,
        rows_refined=preprocessing.rows_refined,
    )
    manifest_path = write_execution_manifest(manifest, artifacts_dir=artifacts_root)

    state = run_agent_graph(
        user_request="Gerar relatorio SRAG com metricas, graficos, fontes e limitacoes",
        run_id=current_run_id,
        refined_dir=resolve_project_path(settings.paths.refined_dir),
        artifacts_dir=artifacts_root,
        news_candidates=[
            {
                "title": "Busca institucional sobre SRAG",
                "url": "https://www.who.int/search?query=SRAG",
                "snippet": "Fonte institucional permitida para contexto sobre SRAG.",
            }
        ],
    )
    _write_news_sources(state.get("news_evidence", []), run_dir / "news_sources.json")

    report_markdown_path = Path(state["final_report_path"])
    report_pdf_path = export_report_pdf(report_markdown_path, run_dir / "report.pdf")

    return PipelineResult(
        run_id=current_run_id,
        artifacts_dir=run_dir,
        manifest_path=manifest_path,
        report_markdown_path=report_markdown_path,
        report_pdf_path=report_pdf_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the SRAG DataSUS pipeline.")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--raw-file", type=Path, default=None)
    args = parser.parse_args()

    result = run_pipeline(run_id=args.run_id, raw_file=args.raw_file)
    print(result.model_dump_json(indent=2))


def _write_news_sources(news_evidence: list[dict], output_path: Path) -> Path:
    output_path.write_text(
        json.dumps(news_evidence, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


if __name__ == "__main__":
    main()



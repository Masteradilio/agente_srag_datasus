import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests  # type: ignore[import-untyped]
from pydantic import BaseModel

from agents.graph import run_agent_graph
from audit.manifest import build_execution_manifest, write_execution_manifest
from config import load_settings
from data.ingestion import run_ingestion
from data.preprocessing import run_preprocessing
from reporting.pdf_exporter import export_report_pdf
from utils.hashing import calculate_sha256
from utils.paths import PROJECT_ROOT, ensure_directory, resolve_project_path


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
    started = time.perf_counter()
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

    extra_raw_files = _ensure_historical_raw_files(
        raw_path,
        [str(url) for url in settings.opendatasus.historical_csv_urls],
    )
    preprocessing = run_preprocessing(
        raw_path,
        current_run_id,
        extra_raw_files=extra_raw_files,
        settings=settings,
    )
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
        news_candidates=_allowlist_source_candidates(),
    )
    _write_news_sources(state.get("news_evidence", []), run_dir / "news_sources.json")
    _write_observability(
        state.get("observability", {}),
        run_dir / "observability.json",
        started_at=started,
        rows_raw=preprocessing.rows_raw,
        rows_refined=preprocessing.rows_refined,
        extra_raw_files=extra_raw_files,
    )

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


def _ensure_historical_raw_files(raw_path: Path, historical_urls: list[str]) -> list[Path]:
    if not historical_urls or not _is_project_landing_file(raw_path):
        return []

    extra_files: list[Path] = []
    for url in historical_urls:
        filename = Path(urlparse(url).path).name
        target_path = raw_path.parent / filename
        if not target_path.is_file():
            response = requests.get(url, timeout=180)
            response.raise_for_status()
            target_path.write_bytes(response.content)
        extra_files.append(target_path)
    return extra_files


def _is_project_landing_file(raw_path: Path) -> bool:
    try:
        raw_path.resolve().relative_to((PROJECT_ROOT / "data" / "landing").resolve())
        return True
    except ValueError:
        return False


def _write_news_sources(news_evidence: list[dict], output_path: Path) -> Path:
    output_path.write_text(
        json.dumps(news_evidence, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def _write_observability(
    observability: dict,
    output_path: Path,
    *,
    started_at: float,
    rows_raw: int,
    rows_refined: int,
    extra_raw_files: list[Path],
) -> Path:
    payload = dict(observability)
    payload.update(
        {
            "generated_at": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
            "pipeline_latency_ms": int((time.perf_counter() - started_at) * 1000),
            "rows_raw": rows_raw,
            "rows_refined": rows_refined,
            "historical_raw_files_count": len(extra_raw_files),
            "historical_raw_files": [str(path) for path in extra_raw_files],
        }
    )
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def _allowlist_source_candidates() -> list[dict[str, str | None]]:
    return [
        {
            "title": "Ministério da Saúde habilita 561 leitos para SRAG",
            "url": (
                "https://www.gov.br/saude/pt-br/assuntos/noticias/2026/maio/"
                "ministerio-da-saude-habilita-561-leitos-para-reforcar-assistencia-"
                "de-pacientes-com-sindrome-respiratoria-aguda-grave-srag"
            ),
            "published_at": "2026-05-29",
            "snippet": (
                "Notícia oficial sobre abertura de 561 leitos e repasse de recursos "
                "para resposta ao aumento de casos de SRAG."
            ),
        },
        {
            "title": "Dataset oficial SRAG 2019 a 2026",
            "url": "https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026",
            "published_at": None,
            "snippet": "Portal oficial de dados abertos do SUS para SRAG.",
        },
        {
            "title": "Brasil tem alta de SRAG em bebês",
            "url": (
                "https://agenciabrasil.ebc.com.br/saude/noticia/2026-05/"
                "brasil-tem-alta-de-sindrome-respiratoria-aguda-grave-em-bebes"
            ),
            "published_at": "2026-05-14",
            "snippet": (
                "Notícia pública sobre alta de SRAG em menores de dois anos, "
                "associada ao vírus sincicial respiratório."
            ),
        },
        {
            "title": "InfoMS paineis oficiais",
            "url": "https://infoms.saude.gov.br/extensions",
            "published_at": None,
            "snippet": "Paineis oficiais de saude, vacinacao e indicadores complementares.",
        },
        {
            "title": "Busca técnica da Fiocruz sobre SRAG",
            "url": "https://portal.fiocruz.br/busca?search_api_views_fulltext=SRAG",
            "published_at": None,
            "snippet": (
                "Consulta técnica em boletins e análises de vigilância respiratória "
                "publicadas pela Fiocruz."
            ),
        },
        {
            "title": "InfoGripe GitHub",
            "url": "https://github.com/infogripe",
            "published_at": None,
            "snippet": "Repositorios publicos do InfoGripe.",
        },
        {
            "title": "Agência Gov busca pública por SRAG",
            "url": "https://agenciagov.ebc.com.br/",
            "published_at": None,
            "snippet": "Consulta ao vivo em comunicacao governamental sobre saude publica.",
        },
        {
            "title": "Agência Brasil saúde",
            "url": "https://agenciabrasil.ebc.com.br/",
            "published_at": None,
            "snippet": "Consulta ao vivo em noticias publicas brasileiras de saude.",
        },
        {
            "title": "Organizacao Pan-Americana da Saude",
            "url": "https://www.paho.org/pt",
            "published_at": None,
            "snippet": "Contexto regional das Americas sobre vigilancia respiratoria.",
        },
        {
            "title": "Organizacao Mundial da Saude",
            "url": "https://www.who.int/",
            "published_at": None,
            "snippet": "Contexto global e vigilancia respiratoria.",
        },
    ]


if __name__ == "__main__":
    main()

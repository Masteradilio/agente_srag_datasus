from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from srag_agent.agents.output_contracts import validate_report_contract
from srag_agent.config import load_news_sources, load_settings
from srag_agent.metrics.calculators import calculate_metric_summary, write_metric_summary
from srag_agent.metrics.charts import (
    generate_daily_cases_30d_chart,
    generate_monthly_cases_12m_chart,
)
from srag_agent.news.search import search_srag_news
from srag_agent.rag.retriever import retrieve_context
from srag_agent.utils.paths import ensure_directory, resolve_project_path


def get_metric_summary_tool(
    run_id: str,
    refined_dir: Path | None = None,
    artifacts_dir: Path | None = None,
) -> dict[str, Any]:
    settings = load_settings()
    resolved_refined_dir = resolve_project_path(refined_dir or settings.paths.refined_dir)
    resolved_artifacts_dir = resolve_project_path(artifacts_dir or settings.paths.artifacts_dir)
    parquet_path = _resolve_parquet_path(run_id, resolved_refined_dir)

    summary = calculate_metric_summary(parquet_path)
    write_metric_summary(summary, resolved_artifacts_dir / run_id / "metrics.json")
    return summary.model_dump(mode="json")


def generate_required_charts_tool(
    run_id: str,
    refined_dir: Path | None = None,
    artifacts_dir: Path | None = None,
) -> list[str]:
    settings = load_settings()
    resolved_refined_dir = resolve_project_path(refined_dir or settings.paths.refined_dir)
    resolved_artifacts_dir = resolve_project_path(artifacts_dir or settings.paths.artifacts_dir)
    parquet_path = _resolve_parquet_path(run_id, resolved_refined_dir)
    df = pd.read_parquet(parquet_path)

    chart_dir = ensure_directory(resolved_artifacts_dir / run_id / "charts")
    daily_path = generate_daily_cases_30d_chart(df, chart_dir / "daily_cases_30d.png")
    monthly_path = generate_monthly_cases_12m_chart(df, chart_dir / "monthly_cases_12m.png")
    return [str(daily_path), str(monthly_path)]


def search_srag_news_tool(
    query: str,
    allowed_domains: list[str] | None = None,
    max_results: int | None = None,
    candidates: list[dict[str, str | None]] | None = None,
) -> list[dict[str, Any]]:
    settings = load_settings()
    domains = allowed_domains or load_news_sources().allowed_domains
    limit = max_results or settings.news.max_sources_per_report
    results = search_srag_news(
        query=query,
        allowed_domains=domains,
        max_results=limit,
        candidates=candidates,
    )
    return [result.model_dump(mode="json") for result in results]


def retrieve_context_tool(
    query: str,
    top_k: int = 5,
    persist_dir: Path = Path("artifacts/vector_store"),
) -> list[dict[str, Any]]:
    results = retrieve_context(
        query=query,
        top_k=top_k,
        persist_dir=resolve_project_path(persist_dir),
    )
    return [result.model_dump(mode="json") for result in results]


def validate_report_contract_tool(
    report: str,
    metric_summary: dict[str, Any] | None = None,
    chart_paths: list[str] | None = None,
    news_evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    result = validate_report_contract(
        report=report,
        metric_summary=metric_summary,
        chart_paths=chart_paths,
        news_evidence=news_evidence,
    )
    return result.model_dump(mode="json")


def _resolve_parquet_path(run_id: str, refined_dir: Path) -> Path:
    candidates = [
        refined_dir / run_id / "srag_total.parquet",
        refined_dir / f"{run_id}.parquet",
        refined_dir / "srag_total.parquet",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    formatted = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"No refined parquet found for run_id={run_id}: {formatted}")


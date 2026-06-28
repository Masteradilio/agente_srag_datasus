from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

TEMPLATE_PATH = Path(__file__).parent / "templates" / "report_template.md"
DEFAULT_USAGE_NOTICE = (
    "Relatorio analitico informativo baseado em dados agregados de SRAG. "
    "Nao substitui boletins oficiais nem aconselhamento medico individualizado."
)


class ReportContext(BaseModel):
    run_id: str
    reference_date: str | None = None
    metric_summary: dict[str, Any]
    chart_paths: list[str] = Field(default_factory=list)
    news_evidence: list[dict[str, Any]] = Field(default_factory=list)
    rag_context: list[dict[str, Any]] = Field(default_factory=list)
    analytical_comments: str = ""
    limitations: list[str] = Field(default_factory=list)
    usage_notice: str = DEFAULT_USAGE_NOTICE


def build_report_markdown(context: ReportContext) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    values = {
        "executive_summary": _executive_summary(context),
        "data_used": _data_used(context),
        "metrics": _metrics(context.metric_summary),
        "charts": _charts(context.chart_paths),
        "news_context": _news_context(context.news_evidence, context.rag_context),
        "analytical_comments": context.analytical_comments
        or "Comentarios limitados aos resultados calculados por tools deterministicas.",
        "limitations": _limitations(context),
        "sources": _sources(context.news_evidence),
        "usage_notice": context.usage_notice,
    }
    report = template
    for key, value in values.items():
        report = report.replace("{{ " + key + " }}", value)
    return report


def write_report_markdown(context: ReportContext, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_report_markdown(context), encoding="utf-8")
    return output_path


def _executive_summary(context: ReportContext) -> str:
    return (
        f"Execucao `{context.run_id}` consolidada para a data de referencia "
        f"{context.reference_date or context.metric_summary.get('reference_date', 'indisponivel')}."
    )


def _data_used(context: ReportContext) -> str:
    total_cases = context.metric_summary.get("total_cases", "indisponivel")
    return f"- Total de casos na base refinada: {total_cases}"


def _metrics(metric_summary: dict[str, Any]) -> str:
    lines = []
    for key in [
        "case_growth_rate_7d",
        "known_mortality_rate",
        "crude_mortality_rate",
        "icu_case_rate",
        "registered_vaccination_case_rate",
    ]:
        metric = metric_summary.get(key, {})
        value = metric.get("value")
        formatted = "indisponivel" if value is None else f"{float(value):.4f}"
        lines.append(
            f"- {metric.get('name', key)}: {formatted} "
            f"(numerador={metric.get('numerator')}, denominador={metric.get('denominator')})"
        )
    return "\n".join(lines)


def _charts(chart_paths: list[str]) -> str:
    if not chart_paths:
        return "- Nenhum grafico gerado."
    return "\n".join(f"- {Path(chart_path).name}: `{chart_path}`" for chart_path in chart_paths)


def _news_context(news_evidence: list[dict[str, Any]], rag_context: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    if news_evidence:
        lines.extend(
            f"- {source.get('title', 'Fonte')} ({source.get('source_domain', '')})"
            for source in news_evidence
        )
    if rag_context:
        lines.extend(
            f"- Contexto documental: {item.get('source_path')}" for item in rag_context[:3]
        )
    return "\n".join(lines) if lines else "- Contexto externo nao recuperado."


def _limitations(context: ReportContext) -> str:
    limitations = context.limitations or context.metric_summary.get("limitations") or []
    if not limitations:
        limitations = ["Metricas dependem da completude, atualizacao e codificacao da base SRAG."]
    return "\n".join(f"- {limitation}" for limitation in limitations)


def _sources(news_evidence: list[dict[str, Any]]) -> str:
    if not news_evidence:
        return "- Nenhuma fonte externa consultada."
    return "\n".join(
        f"- {source.get('title', 'Fonte')}: {source.get('url')}" for source in news_evidence
    )


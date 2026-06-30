from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

TEMPLATE_PATH = Path(__file__).parent / "templates" / "report_template.md"
DEFAULT_USAGE_NOTICE = (
    "Relatório analítico informativo baseado em dados agregados de SRAG. "
    "Não substitui boletins oficiais nem aconselhamento médico individualizado."
)
DEFAULT_LIMITATIONS = (
    "Limitações (limitacoes): as métricas dependem da completude, atualização e "
    "codificação da base SRAG; o indicador de UTI representa proporção de casos "
    "SRAG com registro de UTI, e o indicador de vacinação representa proporção de "
    "casos com vacinação registrada, não a cobertura vacinal populacional completa."
)


class ReportContext(BaseModel):
    run_id: str
    metric_summary: dict[str, Any]
    chart_paths: list[str] = Field(default_factory=list)
    news_evidence: list[dict[str, Any]] = Field(default_factory=list)
    executive_sections: dict[str, Any] = Field(default_factory=dict)
    observability: dict[str, Any] = Field(default_factory=dict)
    usage_notice: str = DEFAULT_USAGE_NOTICE


def build_report_markdown(context: ReportContext) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    values = {
        "metrics_section": _section_text(context, "metrics_section"),
        "historical_chart_1_section": _section_text(context, "historical_chart_1_section"),
        "chart_1": _chart(context.chart_paths, 0),
        "historical_chart_2_section": _section_text(context, "historical_chart_2_section"),
        "chart_2": _chart(context.chart_paths, 1),
        "news_section": _section_text(context, "news_section"),
        "sources": _sources(context.news_evidence, context.observability),
        "usage_notice": context.usage_notice,
        "limitations": DEFAULT_LIMITATIONS,
    }
    report = template
    for key, value in values.items():
        report = report.replace("{{ " + key + " }}", value)
    return report


def write_report_markdown(context: ReportContext, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_report_markdown(context), encoding="utf-8")
    return output_path


def _section_text(context: ReportContext, key: str) -> str:
    text = str(context.executive_sections.get(key) or "").strip()
    if text:
        return text
    if key == "metrics_section":
        return _fallback_metrics_text(context.metric_summary)
    if key in {"historical_chart_1_section", "historical_chart_2_section"}:
        return (
            "Os graficos historicos foram gerados, mas o comentario executivo nao "
            "foi retornado pelo LLM."
        )
    return "Nao houve fontes recentes suficientes para um comentario executivo nesta execucao."


def _fallback_metrics_text(metric_summary: dict[str, Any]) -> str:
    growth = _format_rate(metric_summary, "case_growth_rate_7d")
    mortality = _format_rate(metric_summary, "known_mortality_rate")
    icu = _format_rate(metric_summary, "icu_case_rate")
    vaccination = _format_rate(metric_summary, "registered_vaccination_case_rate")
    return (
        "As metricas principais indicam taxa de aumento de casos de "
        f"{growth}, taxa de mortalidade de {mortality}, taxa de ocupacao/uso de UTI "
        f"de {icu} e taxa de vacinacao registrada da populacao analisada de {vaccination}."
    )


def _format_rate(metric_summary: dict[str, Any], key: str) -> str:
    value = metric_summary.get(key, {}).get("value")
    return "indisponivel" if value is None else f"{float(value):.2%}"


def _chart(chart_paths: list[str], index: int) -> str:
    if len(chart_paths) <= index:
        return "- Nenhum grafico gerado."
    return f"- ![Grafico {index + 1}]({_relative_project_path(Path(chart_paths[index]))})"


def _sources(news_evidence: list[dict[str, Any]], observability: dict[str, Any]) -> str:
    if not news_evidence:
        return "- Nenhuma fonte externa consultada."
    accessed_at = _accessed_at(observability)
    return "\n".join(
        (
            f"- {source.get('title', 'Fonte')}: {source.get('url')} "
            f"Acesso em {accessed_at}"
        )
        for source in news_evidence[:5]
    )


def _accessed_at(observability: dict[str, Any]) -> str:
    generated_at = observability.get("generated_at")
    if isinstance(generated_at, str):
        parsed = _parse_datetime(generated_at)
        if parsed:
            return parsed.strftime("%d/%m/%Y, %H:%M")
    return datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y, %H:%M")


def _parse_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(ZoneInfo("America/Sao_Paulo"))


def _relative_project_path(path: Path) -> str:
    resolved = path.resolve()
    parts = resolved.parts
    if "agente_srag_datasus" in parts:
        index = parts.index("agente_srag_datasus")
        return "/".join(parts[index:])
    return path.as_posix()

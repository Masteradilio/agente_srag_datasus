from typing import Any

from pydantic import BaseModel, Field

REQUIRED_METRIC_KEYS = [
    "case_growth_rate_7d",
    "known_mortality_rate",
    "crude_mortality_rate",
    "icu_case_rate",
    "registered_vaccination_case_rate",
]

REQUIRED_METRIC_TERMS = {
    "case_growth_rate_7d": ["taxa de aumento", "crescimento"],
    "known_mortality_rate": ["mortalidade conhecida"],
    "crude_mortality_rate": ["mortalidade bruta"],
    "icu_case_rate": ["uti"],
    "registered_vaccination_case_rate": ["vacinacao", "vacinação"],
}

REQUIRED_CHART_NAMES = ["daily_cases_30d.png", "monthly_cases_12m.png"]
REQUIRED_SECTIONS = ["fontes", "limitacoes", "limitações", "aviso de uso"]
FORBIDDEN_INDIVIDUAL_FIELDS = ["nu_notific", "cpf", "dt_nasc", "nome do paciente"]


class ReportContractValidation(BaseModel):
    is_valid: bool
    errors: list[str] = Field(default_factory=list)


def validate_report_contract(
    report: str,
    metric_summary: dict[str, Any] | None = None,
    chart_paths: list[str] | None = None,
    news_evidence: list[dict[str, Any]] | None = None,
) -> ReportContractValidation:
    normalized = report.casefold()
    errors: list[str] = []

    _validate_metric_summary(metric_summary, errors)
    _validate_metric_mentions(normalized, errors)
    _validate_chart_mentions(normalized, chart_paths or [], errors)
    _validate_sources(normalized, news_evidence or [], errors)
    _validate_sections(normalized, errors)
    _validate_privacy(normalized, errors)

    return ReportContractValidation(is_valid=not errors, errors=errors)


def _validate_metric_summary(metric_summary: dict[str, Any] | None, errors: list[str]) -> None:
    if not metric_summary:
        errors.append("metric_summary ausente.")
        return
    for key in REQUIRED_METRIC_KEYS:
        if key not in metric_summary:
            errors.append(f"metric_summary sem metrica obrigatoria: {key}.")


def _validate_metric_mentions(report: str, errors: list[str]) -> None:
    for key, terms in REQUIRED_METRIC_TERMS.items():
        if not any(term in report for term in terms):
            errors.append(f"relatorio nao menciona metrica obrigatoria: {key}.")


def _validate_chart_mentions(
    report: str,
    chart_paths: list[str],
    errors: list[str],
) -> None:
    joined_paths = " ".join(chart_paths).casefold()
    for chart_name in REQUIRED_CHART_NAMES:
        if chart_name not in joined_paths:
            errors.append(f"grafico obrigatorio nao foi gerado: {chart_name}.")
        if chart_name not in report:
            errors.append(f"relatorio nao referencia grafico obrigatorio: {chart_name}.")


def _validate_sources(
    report: str,
    news_evidence: list[dict[str, Any]],
    errors: list[str],
) -> None:
    if not news_evidence:
        errors.append("fontes externas ausentes.")
        return
    for source in news_evidence:
        url = str(source.get("url") or "")
        if not url:
            errors.append("fonte externa sem URL.")
            continue
        if url.casefold() not in report:
            errors.append(f"relatorio nao cita fonte externa: {url}.")


def _validate_sections(report: str, errors: list[str]) -> None:
    if "fontes" not in report:
        errors.append("secao de fontes ausente.")
    if "limitacoes" not in report and "limitações" not in report:
        errors.append("secao de limitacoes ausente.")
    if "aviso de uso" not in report:
        errors.append("aviso de uso ausente.")


def _validate_privacy(report: str, errors: list[str]) -> None:
    for field_name in FORBIDDEN_INDIVIDUAL_FIELDS:
        if field_name in report:
            errors.append(f"relatorio contem campo individual proibido: {field_name}.")


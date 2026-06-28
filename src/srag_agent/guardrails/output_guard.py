from pydantic import BaseModel, Field

INDIVIDUAL_DATA_TERMS = ["nu_notific", "cpf", "dt_nasc", "nome do paciente"]
CLINICAL_RECOMMENDATION_TERMS = [
    "voce deve tomar",
    "você deve tomar",
    "prescreva",
    "dose individual",
    "tratamento para este paciente",
]


class OutputGuardResult(BaseModel):
    allowed: bool
    reasons: list[str] = Field(default_factory=list)


def validate_output_report(
    report: str,
    requires_external_sources: bool = True,
) -> OutputGuardResult:
    normalized = report.casefold()
    reasons: list[str] = []

    for term in INDIVIDUAL_DATA_TERMS:
        if term in normalized:
            reasons.append(f"dado individual proibido presente: {term}.")
    for term in CLINICAL_RECOMMENDATION_TERMS:
        if term in normalized:
            reasons.append("recomendacao clinica individualizada presente.")
            break
    if "limitacoes" not in normalized and "limitações" not in normalized:
        reasons.append("limitacoes metodologicas ausentes.")
    if "aviso de uso" not in normalized:
        reasons.append("aviso de uso analitico ausente.")
    if requires_external_sources and ("fontes" not in normalized or "http" not in normalized):
        reasons.append("fontes externas ausentes para comentarios externos.")

    return OutputGuardResult(allowed=not reasons, reasons=reasons)


def enforce_output_guard(report: str, requires_external_sources: bool = True) -> None:
    result = validate_output_report(report, requires_external_sources=requires_external_sources)
    if not result.allowed:
        raise ValueError("Output guardrail blocked report: " + "; ".join(result.reasons))

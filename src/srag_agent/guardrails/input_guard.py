from pydantic import BaseModel, Field

INJECTION_PATTERNS = [
    "ignore as regras",
    "ignorar regras",
    "ignore previous",
    "ignore all previous",
    "desconsidere as instrucoes",
    "desconsidere as instruções",
    "system prompt",
    "prompt de sistema",
    "jailbreak",
]

OUT_OF_SCOPE_TERMS = [
    "preco de acao",
    "cotacao",
    "aposta",
    "receita culinaria",
    "codigo malicioso",
]

LINE_LEVEL_TERMS = [
    "linha a linha",
    "registro individual",
    "dados individuais",
    "nu_notific",
    "cpf",
    "nome do paciente",
]

MEDICAL_ADVICE_TERMS = [
    "diagnostico individual",
    "diagnóstico individual",
    "tratamento individual",
    "qual remedio",
    "qual remédio",
    "posso tomar",
]

SRAG_SCOPE_TERMS = [
    "srag",
    "datasus",
    "opendatasus",
    "influenza",
    "covid",
    "respiratoria",
    "respiratória",
    "relatorio",
    "relatório",
    "mortalidade",
    "uti",
    "vacinacao",
    "vacinação",
]


class GuardrailResult(BaseModel):
    allowed: bool
    reasons: list[str] = Field(default_factory=list)


def validate_input_request(user_request: str) -> GuardrailResult:
    normalized = user_request.casefold()
    reasons: list[str] = []

    if not normalized.strip():
        reasons.append("pedido vazio.")
    if _contains_any(normalized, INJECTION_PATTERNS):
        reasons.append("possivel prompt injection ou tentativa de ignorar regras.")
    if _contains_any(normalized, LINE_LEVEL_TERMS):
        reasons.append("pedido solicita dados linha a linha ou identificadores individuais.")
    if _contains_any(normalized, MEDICAL_ADVICE_TERMS):
        reasons.append("pedido solicita diagnostico ou tratamento individual.")
    if _contains_any(normalized, OUT_OF_SCOPE_TERMS) or not _contains_any(
        normalized,
        SRAG_SCOPE_TERMS,
    ):
        reasons.append("pedido fora do escopo analitico de SRAG/DataSUS.")

    return GuardrailResult(allowed=not reasons, reasons=reasons)


def enforce_input_guard(user_request: str) -> None:
    result = validate_input_request(user_request)
    if not result.allowed:
        raise ValueError("Input guardrail blocked request: " + "; ".join(result.reasons))


def _contains_any(text: str, patterns: list[str]) -> bool:
    return any(pattern in text for pattern in patterns)


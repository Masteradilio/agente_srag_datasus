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
    "developer message",
    "mensagem do desenvolvedor",
    "reveal hidden",
    "mostre as instrucoes",
    "mostre as instruções",
    "bypass",
    "roleplay",
]

OUT_OF_SCOPE_TERMS = [
    "preco de acao",
    "cotacao",
    "aposta",
    "receita culinaria",
    "codigo malicioso",
]

SECRET_EXFILTRATION_TERMS = [
    "api key",
    "apikey",
    "token",
    "senha",
    "password",
    ".env",
    "chave secreta",
    "secret key",
    "credenciais",
]

LOCAL_RESOURCE_TERMS = [
    "file://",
    "c:\\",
    "/etc/passwd",
    "localhost",
    "127.0.0.1",
    "metadata.google.internal",
    "169.254.169.254",
]

DANGEROUS_EXECUTION_TERMS = [
    "rm -rf",
    "del /f",
    "format c:",
    "powershell -enc",
    "curl | sh",
    "wget | sh",
    "subprocess",
    "os.system",
    "exec(",
    "eval(",
    "drop table",
    "delete from",
    "truncate table",
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


CHAT_CONTEXT_TERMS = [
    "dados",
    "casos",
    "aumento",
    "queda",
    "grafico",
    "gráfico",
    "fonte",
    "fontes",
    "noticia",
    "notícia",
    "qualidade",
    "metrica",
    "métrica",
    "taxa",
    "obito",
    "óbito",
    "morte",
    "periodo",
    "período",
]


def validate_input_request(
    user_request: str,
    *,
    allow_contextual_chat: bool = False,
) -> GuardrailResult:
    normalized = user_request.casefold()
    reasons: list[str] = []

    if not normalized.strip():
        reasons.append("pedido vazio.")
    if _contains_any(normalized, INJECTION_PATTERNS):
        reasons.append("possivel prompt injection ou tentativa de ignorar regras.")
    if _contains_any(normalized, SECRET_EXFILTRATION_TERMS):
        reasons.append("pedido solicita segredo, credencial ou material sensivel.")
    if _contains_any(normalized, LOCAL_RESOURCE_TERMS):
        reasons.append("pedido tenta acessar recurso local, interno ou metadados de ambiente.")
    if _contains_any(normalized, DANGEROUS_EXECUTION_TERMS):
        reasons.append("pedido contem comando, codigo ou operacao destrutiva perigosa.")
    if _contains_any(normalized, LINE_LEVEL_TERMS):
        reasons.append("pedido solicita dados linha a linha ou identificadores individuais.")
    if _contains_any(normalized, MEDICAL_ADVICE_TERMS):
        reasons.append("pedido solicita diagnostico ou tratamento individual.")
    has_domain_scope = _contains_any(normalized, SRAG_SCOPE_TERMS)
    has_contextual_scope = allow_contextual_chat and _contains_any(normalized, CHAT_CONTEXT_TERMS)
    if _contains_any(normalized, OUT_OF_SCOPE_TERMS) or not (
        has_domain_scope or has_contextual_scope
    ):
        reasons.append("pedido fora do escopo analitico de SRAG/DataSUS.")

    return GuardrailResult(allowed=not reasons, reasons=reasons)


def enforce_input_guard(user_request: str) -> None:
    result = validate_input_request(user_request)
    if not result.allowed:
        raise ValueError("Input guardrail blocked request: " + "; ".join(result.reasons))


def _contains_any(text: str, patterns: list[str]) -> bool:
    return any(pattern in text for pattern in patterns)

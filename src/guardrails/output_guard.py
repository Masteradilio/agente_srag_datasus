import re
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from config import load_news_sources
from guardrails.domain_allowlist import is_allowed_url

INDIVIDUAL_DATA_TERMS = ["nu_notific", "cpf", "dt_nasc", "nome do paciente"]
INDIVIDUAL_DATA_PATTERNS = [
    re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
]
CLINICAL_RECOMMENDATION_TERMS = [
    "voce deve tomar",
    "você deve tomar",
    "prescreva",
    "dose individual",
    "tratamento para este paciente",
]
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"nvapi-[A-Za-z0-9_-]{20,}", re.IGNORECASE),
    re.compile(r"api[_-]?key\s*[:=]\s*[A-Za-z0-9_\-]{12,}", re.IGNORECASE),
    re.compile(r"bearer\s+[A-Za-z0-9_\-.]{20,}", re.IGNORECASE),
]
LOCAL_PATH_PATTERNS = [
    re.compile(r"\b[A-Z]:\\Users\\", re.IGNORECASE),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"/etc/passwd", re.IGNORECASE),
]
INTERNAL_INSTRUCTION_TERMS = [
    "system prompt",
    "developer message",
    "mensagem do desenvolvedor",
    "prompt de sistema",
    "ignore previous",
]
DANGEROUS_CONTENT_TERMS = [
    "rm -rf",
    "powershell -enc",
    "curl | sh",
    "wget | sh",
    "drop table",
    "delete from",
    "os.system",
    "subprocess",
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
    if any(pattern.search(report) for pattern in INDIVIDUAL_DATA_PATTERNS):
        reasons.append("padrao de identificador individual ou data individual presente.")
    for term in CLINICAL_RECOMMENDATION_TERMS:
        if term in normalized:
            reasons.append("recomendacao clinica individualizada presente.")
            break
    if any(pattern.search(report) for pattern in SECRET_PATTERNS):
        reasons.append("possivel segredo ou credencial presente no relatorio.")
    if any(pattern.search(report) for pattern in LOCAL_PATH_PATTERNS):
        reasons.append("caminho local ou recurso interno presente no relatorio.")
    if any(term in normalized for term in INTERNAL_INSTRUCTION_TERMS):
        reasons.append("instrucoes internas ou prompt do sistema presentes no relatorio.")
    if any(term in normalized for term in DANGEROUS_CONTENT_TERMS):
        reasons.append("conteudo tecnico perigoso presente no relatorio.")
    if "limitacoes" not in normalized and "limitações" not in normalized:
        reasons.append("limitacoes metodologicas ausentes.")
    if "aviso de uso" not in normalized:
        reasons.append("aviso de uso analitico ausente.")
    if requires_external_sources and ("fontes" not in normalized or "http" not in normalized):
        reasons.append("fontes externas ausentes para comentarios externos.")
    reasons.extend(_validate_report_urls(report))

    return OutputGuardResult(allowed=not reasons, reasons=reasons)


def enforce_output_guard(report: str, requires_external_sources: bool = True) -> None:
    result = validate_output_report(report, requires_external_sources=requires_external_sources)
    if not result.allowed:
        raise ValueError("Output guardrail blocked report: " + "; ".join(result.reasons))


def _validate_report_urls(report: str) -> list[str]:
    allowed_domains = load_news_sources().allowed_domains
    errors: list[str] = []
    urls = re.findall(r"https?://[^\s)>\]]+", report)
    for url in urls:
        cleaned = url.rstrip(".,;")
        if not is_allowed_url(cleaned, allowed_domains):
            parsed = urlparse(cleaned)
            errors.append(f"url fora da allowlist no relatorio: {parsed.netloc or cleaned}.")
    return errors

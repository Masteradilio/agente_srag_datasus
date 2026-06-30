import re
from collections.abc import Mapping
from typing import Any

COUNT_FIELDS = ("count", "cases", "total", "n", "value")
INDIVIDUAL_FIELDS = {
    "nu_notific",
    "cpf",
    "cns",
    "cartao_sus",
    "dt_nasc",
    "data_nascimento",
    "nome",
    "nome_paciente",
    "patient_name",
}
HIGH_GRANULARITY_FIELDS = {
    "postal_code",
    "cep",
    "address",
    "endereco",
    "logradouro",
    "numero",
    "complemento",
    "bairro",
    "latitude",
    "longitude",
}
SENSITIVE_VALUE_PATTERNS = [
    re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    re.compile(r"\b(?:\+?55\s?)?\(?\d{2}\)?\s?\d{4,5}-?\d{4}\b"),
]


def enforce_min_group_size(
    records: list[dict[str, Any]],
    min_group_size: int,
) -> list[dict[str, Any]]:
    if min_group_size < 1:
        raise ValueError("min_group_size must be >= 1.")

    filtered: list[dict[str, Any]] = []
    for record in records:
        _reject_individual_or_high_granularity(record)
        count = _extract_count(record)
        if count is None:
            continue
        if count >= min_group_size:
            filtered.append(record)
    return filtered


def enforce_no_sensitive_values(record: Mapping[str, Any]) -> None:
    _reject_individual_or_high_granularity(record)


def _extract_count(record: Mapping[str, Any]) -> int | None:
    for field in COUNT_FIELDS:
        if field in record:
            try:
                return int(record[field])
            except (TypeError, ValueError):
                return None
    return None


def _reject_individual_or_high_granularity(record: Mapping[str, Any]) -> None:
    fields = {str(field).casefold() for field in record}
    individual = fields & INDIVIDUAL_FIELDS
    if individual:
        raise ValueError(
            "Privacy guardrail blocked individual-level fields: "
            + ", ".join(sorted(individual))
        )

    high_granularity = fields & HIGH_GRANULARITY_FIELDS
    if high_granularity:
        raise ValueError(
            "Privacy guardrail blocked excessive granularity: "
            + ", ".join(sorted(high_granularity))
        )

    sensitive_values = _sensitive_value_fields(record)
    if sensitive_values:
        raise ValueError(
            "Privacy guardrail blocked sensitive values in fields: "
            + ", ".join(sorted(sensitive_values))
        )


def _sensitive_value_fields(record: Mapping[str, Any]) -> set[str]:
    blocked: set[str] = set()
    for field, value in record.items():
        if value is None:
            continue
        text = str(value)
        if any(pattern.search(text) for pattern in SENSITIVE_VALUE_PATTERNS):
            blocked.add(str(field))
    return blocked

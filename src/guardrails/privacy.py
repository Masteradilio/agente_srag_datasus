from collections.abc import Mapping
from typing import Any

COUNT_FIELDS = ("count", "cases", "total", "n", "value")
INDIVIDUAL_FIELDS = {"nu_notific", "cpf", "dt_nasc", "nome", "patient_name"}
HIGH_GRANULARITY_FIELDS = {"postal_code", "cep", "address", "endereco", "logradouro"}


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


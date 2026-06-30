import pytest

from guardrails.privacy import enforce_min_group_size


def test_privacy_guard_filters_small_groups() -> None:
    records = [
        {"uf": "SP", "cases": 20},
        {"uf": "RJ", "cases": 4},
        {"uf": "MG", "cases": 10},
    ]

    filtered = enforce_min_group_size(records, min_group_size=10)

    assert filtered == [{"uf": "SP", "cases": 20}, {"uf": "MG", "cases": 10}]


def test_privacy_guard_blocks_individual_fields() -> None:
    with pytest.raises(ValueError):
        enforce_min_group_size([{"NU_NOTIFIC": "123", "cases": 1}], min_group_size=10)


@pytest.mark.parametrize(
    "record",
    [
        {"uf": "SP", "cases": 20, "observacao": "CPF 123.456.789-10"},
        {"uf": "SP", "cases": 20, "contato": "paciente@example.com"},
        {"uf": "SP", "cases": 20, "telefone": "(11) 99999-9999"},
        {"uf": "SP", "cases": 20, "cep": "01001-000"},
    ],
)
def test_privacy_guard_blocks_sensitive_values_and_granularity(record: dict) -> None:
    with pytest.raises(ValueError):
        enforce_min_group_size([record], min_group_size=10)


def test_privacy_guard_does_not_return_records_without_counts() -> None:
    assert enforce_min_group_size([{"uf": "SP"}], min_group_size=10) == []



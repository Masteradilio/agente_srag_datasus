import pytest

from guardrails.output_guard import enforce_output_guard, validate_output_report


def test_output_guard_allows_report_with_limitations_notice_and_sources() -> None:
    report = "Fontes https://www.who.int/news/srag\nLimitacoes\nAviso de uso"

    result = validate_output_report(report)

    assert result.allowed


@pytest.mark.parametrize(
    "report",
    [
        "Fontes https://www.who.int/news/srag\nAviso de uso",
        "Fontes https://www.who.int/news/srag\nLimitacoes",
        "Limitacoes\nAviso de uso sem URL",
        "Fontes https://www.who.int/news/srag\nLimitacoes\nAviso de uso\nCPF 123",
        (
            "Fontes https://www.who.int/news/srag\nLimitacoes\nAviso de uso\n"
            "Voce deve tomar este remedio"
        ),
    ],
)
def test_output_guard_blocks_invalid_report(report: str) -> None:
    with pytest.raises(ValueError):
        enforce_output_guard(report)



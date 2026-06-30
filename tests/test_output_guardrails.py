import pytest

from guardrails.output_guard import enforce_output_guard, validate_output_report


def test_output_guard_allows_report_with_limitations_notice_and_sources() -> None:
    report = "Fontes https://www.who.int/news\nLimitacoes\nAviso de uso"

    result = validate_output_report(report)

    assert result.allowed


@pytest.mark.parametrize(
    "report",
    [
        "Fontes https://www.who.int/news/srag\nAviso de uso",
        "Fontes https://www.who.int/news/srag\nLimitacoes",
        "Limitacoes\nAviso de uso sem URL",
        "Fontes https://www.who.int/news\nLimitacoes\nAviso de uso\nCPF 123",
        (
            "Fontes https://www.who.int/news\nLimitacoes\nAviso de uso\n"
            "Voce deve tomar este remedio"
        ),
        "Fontes https://evil.example/news\nLimitacoes\nAviso de uso",
        "Fontes https://www.who.int/news\nLimitacoes\nAviso de uso\napi_key=abcdef1234567890",
        "Fontes https://www.who.int/news\nLimitacoes\nAviso de uso\nC:\\Users\\adili\\.env",
        "Fontes https://www.who.int/news\nLimitacoes\nAviso de uso\nsystem prompt interno",
        "Fontes https://www.who.int/news\nLimitacoes\nAviso de uso\nrm -rf /tmp",
        "Fontes https://www.who.int/news\nLimitacoes\nAviso de uso\nCPF 123.456.789-10",
    ],
)
def test_output_guard_blocks_invalid_report(report: str) -> None:
    with pytest.raises(ValueError):
        enforce_output_guard(report)



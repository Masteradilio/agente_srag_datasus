from agents.output_contracts import validate_report_contract


def _metric_summary() -> dict:
    return {
        "case_growth_rate_7d": {},
        "known_mortality_rate": {},
        "crude_mortality_rate": {},
        "icu_case_rate": {},
        "registered_vaccination_case_rate": {},
    }


def _valid_report() -> str:
    return """
    taxa de aumento
    mortalidade conhecida
    mortalidade bruta
    UTI
    vacinacao
    daily_cases_30d.png
    monthly_cases_12m.png
    fontes https://www.who.int/news/srag
    limitacoes
    aviso de uso
    """


def test_report_contract_accepts_required_content() -> None:
    result = validate_report_contract(
        report=_valid_report(),
        metric_summary=_metric_summary(),
        chart_paths=["daily_cases_30d.png", "monthly_cases_12m.png"],
        news_evidence=[{"url": "https://www.who.int/news/srag"}],
    )

    assert result.is_valid
    assert result.errors == []


def test_report_contract_fails_when_metric_is_missing() -> None:
    result = validate_report_contract(
        report=_valid_report().replace("UTI", ""),
        metric_summary=_metric_summary(),
        chart_paths=["daily_cases_30d.png", "monthly_cases_12m.png"],
        news_evidence=[{"url": "https://www.who.int/news/srag"}],
    )

    assert not result.is_valid
    assert any("icu_case_rate" in error for error in result.errors)


def test_report_contract_fails_when_source_is_missing() -> None:
    result = validate_report_contract(
        report=_valid_report().replace("https://www.who.int/news/srag", ""),
        metric_summary=_metric_summary(),
        chart_paths=["daily_cases_30d.png", "monthly_cases_12m.png"],
        news_evidence=[{"url": "https://www.who.int/news/srag"}],
    )

    assert not result.is_valid
    assert any("fonte externa" in error for error in result.errors)



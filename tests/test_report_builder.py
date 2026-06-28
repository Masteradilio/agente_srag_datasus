from srag_agent.reporting.report_builder import ReportContext, build_report_markdown


def test_build_report_markdown_renders_required_sections() -> None:
    report = build_report_markdown(
        ReportContext(
            run_id="run-report",
            metric_summary={
                "reference_date": "2026-06-20",
                "total_cases": 100,
                "case_growth_rate_7d": {"value": 0.1, "numerator": 10, "denominator": 90},
                "known_mortality_rate": {"value": 0.2, "numerator": 20, "denominator": 100},
                "crude_mortality_rate": {"value": 0.2, "numerator": 20, "denominator": 100},
                "icu_case_rate": {"value": 0.3, "numerator": 30, "denominator": 100},
                "registered_vaccination_case_rate": {
                    "value": 0.4,
                    "numerator": 40,
                    "denominator": 100,
                },
                "limitations": ["Base sujeita a revisao."],
            },
            chart_paths=["daily_cases_30d.png", "monthly_cases_12m.png"],
            news_evidence=[
                {
                    "title": "Boletim SRAG",
                    "url": "https://www.who.int/news/srag",
                    "source_domain": "www.who.int",
                }
            ],
        )
    )

    assert "# Relatorio Automatizado de SRAG" in report
    assert "## 3. Metricas Principais" in report
    assert "daily_cases_30d.png" in report
    assert "https://www.who.int/news/srag" in report
    assert "Aviso de Uso" in report


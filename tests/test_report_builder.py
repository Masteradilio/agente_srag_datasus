from reporting.report_builder import ReportContext, build_report_markdown


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
            executive_sections={
                "metrics_section": (
                    "A taxa de aumento de casos, a mortalidade conhecida, a mortalidade bruta, "
                    "a UTI e a vacinacao indicam estabilidade operacional."
                ),
                "historical_chart_1_section": "O primeiro grafico mostra a evolucao diaria.",
                "historical_chart_2_section": "O segundo grafico mostra a evolucao mensal.",
                "news_section": "As fontes recentes reforcam a vigilancia de SRAG.",
            },
            observability={"generated_at": "2026-06-29T16:30:00-03:00"},
        )
    )

    assert "# Relatório Executivo de SRAG" in report
    assert "## 1. Métricas Principais" in report
    assert "## 2. Evolução Histórica" in report
    assert "## 3. Notícias Recentes" in report
    assert "## 4. Fontes Consultadas" in report
    assert "daily_cases_30d.png" in report
    assert "https://www.who.int/news/srag" in report
    assert "Acesso em 29/06/2026, 16:30" in report
    assert "Fontes usadas pelo LLM" not in report
    assert "Aviso de uso" in report



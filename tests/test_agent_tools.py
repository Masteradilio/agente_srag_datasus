import pandas as pd

from srag_agent.agents.tools import (
    generate_required_charts_tool,
    get_metric_summary_tool,
    search_srag_news_tool,
    validate_report_contract_tool,
)


def _write_refined_fixture(tmp_path, run_id: str) -> None:
    run_dir = tmp_path / "refined" / run_id
    run_dir.mkdir(parents=True)
    dates = pd.date_range("2026-06-01", periods=20, freq="D")
    pd.DataFrame(
        {
            "canonical_case_date": dates,
            "evolution": ["1", "2"] * 10,
            "icu": ["1", "2"] * 10,
            "vaccination": ["1", "2"] * 10,
        }
    ).to_parquet(run_dir / "srag_total.parquet", index=False)


def test_agent_metric_and_chart_tools_write_artifacts(tmp_path) -> None:
    run_id = "run-test"
    _write_refined_fixture(tmp_path, run_id)

    summary = get_metric_summary_tool(
        run_id,
        refined_dir=tmp_path / "refined",
        artifacts_dir=tmp_path / "artifacts",
    )
    charts = generate_required_charts_tool(
        run_id,
        refined_dir=tmp_path / "refined",
        artifacts_dir=tmp_path / "artifacts",
    )

    assert summary["total_cases"] == 20
    assert (tmp_path / "artifacts" / run_id / "metrics.json").is_file()
    assert len(charts) == 2
    assert all(path.endswith(".png") for path in charts)


def test_search_srag_news_tool_uses_allowlist() -> None:
    results = search_srag_news_tool(
        "SRAG",
        allowed_domains=["who.int"],
        max_results=5,
        candidates=[
            {"title": "SRAG", "url": "https://www.who.int/news/srag", "snippet": "SRAG"},
            {"title": "fora", "url": "https://example.com/srag", "snippet": "SRAG"},
        ],
    )

    assert len(results) == 1
    assert results[0]["source_domain"] == "www.who.int"


def test_validate_report_contract_tool_returns_errors_for_missing_source() -> None:
    result = validate_report_contract_tool(
        report=(
            "taxa de aumento mortalidade conhecida mortalidade bruta UTI vacinacao "
            "daily_cases_30d.png monthly_cases_12m.png fontes limitacoes aviso de uso"
        ),
        metric_summary={
            "case_growth_rate_7d": {},
            "known_mortality_rate": {},
            "crude_mortality_rate": {},
            "icu_case_rate": {},
            "registered_vaccination_case_rate": {},
        },
        chart_paths=["daily_cases_30d.png", "monthly_cases_12m.png"],
        news_evidence=[{"url": "https://www.who.int/news/srag"}],
    )

    assert not result["is_valid"]
    assert any("nao cita fonte externa" in error for error in result["errors"])


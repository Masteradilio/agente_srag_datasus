import pandas as pd

from srag_agent.pipeline import run_pipeline


def test_pipeline_smoke_generates_final_artifacts(tmp_path) -> None:
    raw_file = tmp_path / "INFLUD26-22-06-2026.csv"
    pd.DataFrame(
        {
            "DT_SIN_PRI": pd.date_range("2026-06-01", periods=40, freq="D").strftime(
                "%d/%m/%Y"
            ),
            "DT_NOTIFIC": pd.date_range("2026-06-01", periods=40, freq="D").strftime(
                "%d/%m/%Y"
            ),
            "EVOLUCAO": ["1", "2"] * 20,
            "UTI": ["1", "2"] * 20,
            "VACINA_COV": ["1", "2"] * 20,
            "SG_UF_NOT": ["SP"] * 40,
            "ID_MUNICIP": ["SAO PAULO"] * 40,
            "CLASSI_FIN": ["SRAG"] * 40,
        }
    ).to_csv(raw_file, sep=";", encoding="latin1", index=False)

    result = run_pipeline(run_id="pytest-pipeline-smoke", raw_file=raw_file)
    run_dir = result.artifacts_dir

    assert result.manifest_path.is_file()
    assert (run_dir / "data_quality_report.json").is_file()
    assert (run_dir / "metrics.json").is_file()
    assert (run_dir / "news_sources.json").is_file()
    assert (run_dir / "agent_trace.jsonl").is_file()
    assert result.report_markdown_path.is_file()
    assert result.report_pdf_path.is_file()
    assert (run_dir / "charts" / "daily_cases_30d.png").is_file()
    assert (run_dir / "charts" / "monthly_cases_12m.png").is_file()

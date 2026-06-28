import pandas as pd

from srag_agent.metrics.charts import (
    generate_daily_cases_30d_chart,
    generate_monthly_cases_12m_chart,
)


def test_generate_required_charts(tmp_path) -> None:
    df = pd.DataFrame(
        {
            "canonical_case_date": pd.date_range("2025-07-01", periods=370, freq="D"),
        }
    )

    daily_path = generate_daily_cases_30d_chart(df, tmp_path / "daily_cases_30d.png")
    monthly_path = generate_monthly_cases_12m_chart(df, tmp_path / "monthly_cases_12m.png")

    assert daily_path.is_file()
    assert monthly_path.is_file()
    assert daily_path.stat().st_size > 0
    assert monthly_path.stat().st_size > 0

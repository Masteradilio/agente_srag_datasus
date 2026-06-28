from pathlib import Path

import pandas as pd

from config import load_settings
from data.preprocessing import run_preprocessing
from metrics.calculators import calculate_metric_summary, write_metric_summary
from metrics.charts import (
    generate_daily_cases_30d_chart,
    generate_monthly_cases_12m_chart,
)


def test_aggregated_srag_preprocessing_metrics_and_charts_smoke(tmp_path: Path) -> None:
    run_id = "2026-smoke"
    raw_file = tmp_path / "data" / "landing" / run_id / "srag_total.xlsx"
    raw_file.parent.mkdir(parents=True)
    pd.DataFrame(
        {
            "Semana EpidemiolÃ³gica": [23, 23, 24, 24],
            "UF *** ContÃ©m BR - CUIDADO ***": ["SP", "RJ", "SP", "RJ"],
            "MunicÃ­pio": ["SAO PAULO", "RIO DE JANEIRO", "SAO PAULO", "RIO DE JANEIRO"],
            "Faixa EtÃ¡ria": ["15 a 49 anos", "65 anos ou +", "15 a 49 anos", "65 anos ou +"],
            "Codigo": [355030, 330455, 355030, 330455],
            "Regional de SaÃºde": ["REGIAO A", "REGIAO B", "REGIAO A", "REGIAO B"],
            "casos": [10, 5, 20, 8],
            "obitos": [1, 0, 2, 1],
        }
    ).to_excel(raw_file, index=False)

    preprocessing_result = run_preprocessing(
        raw_file,
        run_id,
        settings=load_settings(),
        project_root=tmp_path,
    )
    refined_df = pd.read_parquet(preprocessing_result.parquet_path)
    summary = calculate_metric_summary(preprocessing_result.parquet_path)
    charts_dir = tmp_path / "artifacts" / "runs" / run_id / "charts"

    metrics_path = write_metric_summary(
        summary,
        tmp_path / "artifacts" / "runs" / run_id / "metrics.json",
    )
    daily_chart = generate_daily_cases_30d_chart(refined_df, charts_dir / "daily_cases_30d.png")
    monthly_chart = generate_monthly_cases_12m_chart(
        refined_df,
        charts_dir / "monthly_cases_12m.png",
    )

    assert preprocessing_result.parquet_path.is_file()
    assert preprocessing_result.data_quality_report_path.is_file()
    assert metrics_path.is_file()
    assert daily_chart.is_file()
    assert monthly_chart.is_file()
    assert summary.total_cases == 43
    assert summary.crude_mortality_rate.numerator == 4
    assert summary.icu_case_rate.value is None
    assert summary.registered_vaccination_case_rate.value is None


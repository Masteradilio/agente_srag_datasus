from datetime import date

import pandas as pd

from metrics.calculators import (
    calculate_case_growth_rate,
    calculate_icu_rate,
    calculate_metric_summary,
    calculate_mortality_rates,
    calculate_reference_date,
    calculate_vaccination_rate,
    write_metric_summary,
)


def _metrics_dataframe() -> pd.DataFrame:
    dates = pd.date_range("2026-06-01", periods=14, freq="D")
    return pd.DataFrame(
        {
            "canonical_case_date": list(dates) + [pd.Timestamp("2026-06-14")],
            "evolution": [
                "1", "2", "1", None, "2", "1", "1", "1", "2", "1", "1", "1", "1", "1", "2",
            ],
            "icu": ["1", "2", "1", None, "2", "1", "2", "1", "2", "2", "1", "2", "2", "1", "1"],
            "vaccination": [
                "1", "2", "9", None, "1", "2", "1", "2", "9", "1", "2", "1", "2", "1", "1",
            ],
        }
    )


def test_calculate_reference_date() -> None:
    assert calculate_reference_date(_metrics_dataframe()) == date(2026, 6, 14)


def test_calculate_case_growth_rate() -> None:
    metric = calculate_case_growth_rate(_metrics_dataframe(), date(2026, 6, 14))

    assert metric.numerator == 1
    assert metric.denominator == 7
    assert metric.value == 1 / 7


def test_calculate_case_growth_rate_with_zero_denominator() -> None:
    df = pd.DataFrame({"canonical_case_date": [pd.Timestamp("2026-06-14")]})

    metric = calculate_case_growth_rate(df, date(2026, 6, 14))

    assert metric.value is None
    assert metric.limitations


def test_calculate_mortality_rates() -> None:
    rates = calculate_mortality_rates(_metrics_dataframe())

    assert rates["known"].numerator == 4
    assert rates["known"].denominator == 14
    assert rates["crude"].denominator == 15


def test_calculate_icu_rate() -> None:
    metric = calculate_icu_rate(_metrics_dataframe())

    assert metric.numerator == 7
    assert metric.denominator == 15
    assert metric.limitations


def test_calculate_vaccination_rate() -> None:
    metric = calculate_vaccination_rate(_metrics_dataframe())

    assert metric.numerator == 7
    assert metric.denominator == 12
    assert metric.limitations


def test_calculate_metric_summary_and_write_json(tmp_path) -> None:
    parquet_path = tmp_path / "srag_total.parquet"
    _metrics_dataframe().to_parquet(parquet_path, index=False)

    summary = calculate_metric_summary(parquet_path)
    output_path = write_metric_summary(summary, tmp_path / "metrics.json")

    assert summary.total_cases == 15
    assert output_path.is_file()


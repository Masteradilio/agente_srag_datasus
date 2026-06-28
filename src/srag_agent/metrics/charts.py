from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd  # type: ignore[import-untyped]

from srag_agent.utils.paths import ensure_directory


def generate_daily_cases_30d_chart(df: pd.DataFrame, output_path: Path) -> Path:
    ensure_directory(output_path.parent)
    case_dates = pd.to_datetime(df["canonical_case_date"], errors="coerce").dropna()
    weighted_df = _case_date_weights(df)
    reference_date = case_dates.max().normalize()
    start_date = reference_date - pd.Timedelta(days=29)
    daily_counts = _weighted_counts_by_date(weighted_df, start_date, reference_date)
    index = pd.date_range(start=start_date, end=reference_date, freq="D")
    daily_counts = daily_counts.reindex(index, fill_value=0)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(daily_counts.index, daily_counts.values, marker="o", linewidth=1.8)
    ax.set_title("Casos diarios de SRAG - ultimos 30 dias")
    ax.set_xlabel("Data")
    ax.set_ylabel("Casos")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def generate_monthly_cases_12m_chart(df: pd.DataFrame, output_path: Path) -> Path:
    ensure_directory(output_path.parent)
    case_dates = pd.to_datetime(df["canonical_case_date"], errors="coerce").dropna()
    weighted_df = _case_date_weights(df)
    reference_month = case_dates.max().to_period("M").to_timestamp()
    start_month = reference_month - pd.DateOffset(months=11)
    end_month = reference_month + pd.offsets.MonthEnd(0)
    monthly_counts = _weighted_counts_by_month(weighted_df, start_month, end_month)
    index = pd.period_range(start=start_month, end=reference_month, freq="M")
    monthly_counts = monthly_counts.reindex(index, fill_value=0)

    fig, ax = plt.subplots(figsize=(10, 4))
    labels = [period.strftime("%Y-%m") for period in monthly_counts.index]
    ax.bar(labels, monthly_counts.values)
    ax.set_title("Casos mensais de SRAG - ultimos 12 meses")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Casos")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def _case_date_weights(df: pd.DataFrame) -> pd.DataFrame:
    if "cases" in df.columns:
        parsed_cases = pd.to_numeric(df["cases"], errors="coerce")
        if parsed_cases.notna().sum() > 0:
            cases = parsed_cases.fillna(0)
        else:
            cases = pd.Series(1, index=df.index)
    else:
        cases = pd.Series(1, index=df.index)

    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                df["canonical_case_date"], errors="coerce", utc=True
            ).dt.tz_localize(None),
            "cases": cases,
        }
    ).dropna(subset=["date"])


def _weighted_counts_by_date(
    weighted_df: pd.DataFrame,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.Series:
    window = weighted_df[(weighted_df["date"] >= start_date) & (weighted_df["date"] <= end_date)]
    return window.groupby(window["date"].dt.normalize())["cases"].sum().sort_index()


def _weighted_counts_by_month(
    weighted_df: pd.DataFrame,
    start_month: pd.Timestamp,
    end_month: pd.Timestamp,
) -> pd.Series:
    window = weighted_df[
        (weighted_df["date"] >= start_month) & (weighted_df["date"] <= end_month)
    ]
    return window.groupby(window["date"].dt.to_period("M"))["cases"].sum().sort_index()

import json
import unicodedata
from datetime import date, timedelta
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]

from srag_agent.data.schema import MetricSummary, MetricValue
from srag_agent.metrics.definitions import (
    CASE_GROWTH_RATE_7D,
    CRUDE_MORTALITY_RATE,
    ICU_CASE_RATE,
    KNOWN_MORTALITY_RATE,
    METRIC_LIMITATIONS,
    METRIC_NAMES,
    REGISTERED_VACCINATION_CASE_RATE,
)
from srag_agent.utils.paths import ensure_directory

DEATH_CODES = {"2", "OBITO", "OBITO POR SRAG"}
KNOWN_EVOLUTION_CODES = {"1", "2", "CURA", "OBITO", "OBITO POR SRAG"}
YES_CODES = {"1", "SIM", "YES", "TRUE"}
KNOWN_STATUS_CODES = {"1", "2", "SIM", "NAO"}


def calculate_reference_date(df: pd.DataFrame) -> date:
    dates = pd.to_datetime(df["canonical_case_date"], errors="coerce").dropna()
    if dates.empty:
        raise ValueError(
            "Cannot calculate reference date without valid canonical_case_date values."
        )
    return dates.max().date()


def calculate_case_growth_rate(df: pd.DataFrame, reference_date: date) -> MetricValue:
    case_dates = pd.to_datetime(df["canonical_case_date"], errors="coerce").dt.date
    weights = _case_weights(df)
    current_start = reference_date - timedelta(days=6)
    previous_start = reference_date - timedelta(days=13)
    previous_end = reference_date - timedelta(days=7)

    current_mask = (case_dates >= current_start) & (case_dates <= reference_date)
    previous_mask = (case_dates >= previous_start) & (case_dates <= previous_end)
    current_cases = int(weights[current_mask].sum())
    previous_cases = int(weights[previous_mask].sum())
    value = _safe_ratio(current_cases - previous_cases, previous_cases)
    limitations = []
    if value is None:
        limitations.append(METRIC_LIMITATIONS[CASE_GROWTH_RATE_7D])

    return MetricValue(
        name=METRIC_NAMES[CASE_GROWTH_RATE_7D],
        value=value,
        numerator=current_cases - previous_cases,
        denominator=previous_cases,
        limitations=limitations,
    )


def calculate_mortality_rates(df: pd.DataFrame) -> dict[str, MetricValue]:
    total_cases = _total_cases(df)
    deaths_series = _numeric_column_if_present(df, "deaths")
    if deaths_series is not None:
        deaths = int(deaths_series.sum())
        return {
            "known": MetricValue(
                name=METRIC_NAMES[KNOWN_MORTALITY_RATE],
                value=_safe_ratio(deaths, total_cases),
                numerator=deaths,
                denominator=total_cases,
                limitations=[
                    (
                        "Base agregada nao possui status individual de evolucao; "
                        "taxa conhecida usa casos totais."
                    )
                ],
            ),
            "crude": MetricValue(
                name=METRIC_NAMES[CRUDE_MORTALITY_RATE],
                value=_safe_ratio(deaths, total_cases),
                numerator=deaths,
                denominator=total_cases,
                limitations=[],
            ),
        }

    evolution = _normalized_series(df.get("evolution", pd.Series(dtype=object)))
    deaths = int(evolution.isin(DEATH_CODES).sum())
    known_evolution = int(evolution.isin(KNOWN_EVOLUTION_CODES).sum())

    known_value = _safe_ratio(deaths, known_evolution)
    known_limitations = []
    if known_value is None:
        known_limitations.append(METRIC_LIMITATIONS[KNOWN_MORTALITY_RATE])

    return {
        "known": MetricValue(
            name=METRIC_NAMES[KNOWN_MORTALITY_RATE],
            value=known_value,
            numerator=deaths,
            denominator=known_evolution,
            limitations=known_limitations,
        ),
        "crude": MetricValue(
            name=METRIC_NAMES[CRUDE_MORTALITY_RATE],
            value=_safe_ratio(deaths, total_cases),
            numerator=deaths,
            denominator=total_cases,
            limitations=[],
        ),
    }


def calculate_icu_rate(df: pd.DataFrame) -> MetricValue:
    total_cases = _total_cases(df)
    if "icu" not in df.columns:
        return MetricValue(
            name=METRIC_NAMES[ICU_CASE_RATE],
            value=None,
            numerator=0,
            denominator=total_cases,
            limitations=[
                METRIC_LIMITATIONS[ICU_CASE_RATE],
                "Base agregada nao possui campo de UTI.",
            ],
        )
    icu = _normalized_series(df.get("icu", pd.Series(dtype=object)))
    cases_with_icu = int(icu.isin(YES_CODES).sum())

    return MetricValue(
        name=METRIC_NAMES[ICU_CASE_RATE],
        value=_safe_ratio(cases_with_icu, total_cases),
        numerator=cases_with_icu,
        denominator=total_cases,
        limitations=[METRIC_LIMITATIONS[ICU_CASE_RATE]],
    )


def calculate_vaccination_rate(df: pd.DataFrame) -> MetricValue:
    if "vaccination" not in df.columns:
        return MetricValue(
            name=METRIC_NAMES[REGISTERED_VACCINATION_CASE_RATE],
            value=None,
            numerator=0,
            denominator=0,
            limitations=[
                METRIC_LIMITATIONS[REGISTERED_VACCINATION_CASE_RATE],
                "Base agregada nao possui campo de vacinacao.",
            ],
        )
    vaccination = _normalized_series(df.get("vaccination", pd.Series(dtype=object)))
    registered = int(vaccination.isin(YES_CODES).sum())
    known_status = int(vaccination.isin(KNOWN_STATUS_CODES).sum())
    value = _safe_ratio(registered, known_status)
    limitations = [METRIC_LIMITATIONS[REGISTERED_VACCINATION_CASE_RATE]]
    if value is None:
        limitations.append("Status vacinal conhecido ausente no recorte analisado.")

    return MetricValue(
        name=METRIC_NAMES[REGISTERED_VACCINATION_CASE_RATE],
        value=value,
        numerator=registered,
        denominator=known_status,
        limitations=limitations,
    )


def calculate_metric_summary(parquet_path: Path) -> MetricSummary:
    df = pd.read_parquet(parquet_path)
    reference_date = calculate_reference_date(df)
    mortality_rates = calculate_mortality_rates(df)

    summary = MetricSummary(
        reference_date=reference_date.isoformat(),
        total_cases=_total_cases(df),
        case_growth_rate_7d=calculate_case_growth_rate(df, reference_date),
        known_mortality_rate=mortality_rates["known"],
        crude_mortality_rate=mortality_rates["crude"],
        icu_case_rate=calculate_icu_rate(df),
        registered_vaccination_case_rate=calculate_vaccination_rate(df),
    )
    summary.limitations = _collect_limitations(summary)
    return summary


def write_metric_summary(summary: MetricSummary, output_path: Path) -> Path:
    ensure_directory(output_path.parent)
    output_path.write_text(
        json.dumps(summary.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def _safe_ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _normalized_series(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.upper().map(_strip_accents).map(_normalize_code)


def _strip_accents(value: object) -> object:
    if not isinstance(value, str):
        return value
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _normalize_code(value: object) -> object:
    if not isinstance(value, str):
        return value
    if value.endswith(".0") and value[:-2].isdigit():
        return value[:-2]
    return value


def _case_weights(df: pd.DataFrame) -> pd.Series:
    cases = _numeric_column_if_present(df, "cases")
    if cases is not None:
        return cases.astype(int)
    return pd.Series(1, index=df.index)


def _total_cases(df: pd.DataFrame) -> int:
    return int(_case_weights(df).sum())


def _numeric_column_if_present(df: pd.DataFrame, column: str) -> pd.Series | None:
    if column not in df.columns:
        return None
    series = pd.to_numeric(df[column], errors="coerce")
    if series.notna().sum() == 0:
        return None
    return series.fillna(0)


def _collect_limitations(summary: MetricSummary) -> list[str]:
    limitations: list[str] = []
    for metric in [
        summary.case_growth_rate_7d,
        summary.known_mortality_rate,
        summary.crude_mortality_rate,
        summary.icu_case_rate,
        summary.registered_vaccination_case_rate,
    ]:
        limitations.extend(metric.limitations)
    return sorted(set(limitations))

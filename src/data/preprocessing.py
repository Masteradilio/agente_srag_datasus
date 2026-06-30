import json
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from config import Settings, load_column_mapping, load_settings
from data.schema import PreprocessingResult
from data.validation import build_data_quality_report, write_data_quality_report
from utils.paths import ensure_directory, resolve_project_path

DATE_COLUMNS = {
    "case_date",
    "notification_date",
    "evolution_date",
    "icu_start_date",
    "icu_end_date",
}

REQUIRED_CANONICAL_COLUMNS = ["case_date", "notification_date"]
AGGREGATED_REQUIRED_COLUMNS = {"epidemiological_week", "cases", "deaths"}


def load_raw_srag_excel(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Raw SRAG file not found: {path}")
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, sep=";", encoding="latin1", low_memory=False)
    return pd.read_excel(path)


def resolve_column_mapping(df: pd.DataFrame, mapping: dict[str, Any]) -> dict[str, str | None]:
    source_columns: dict[str, str] = {}
    for column in df.columns:
        column_name = str(column)
        for key in _column_match_keys(column_name):
            source_columns.setdefault(key, column_name)
    resolved: dict[str, str | None] = {}

    for canonical_name, entry in mapping.items():
        candidates = _extract_candidates(entry)
        resolved[canonical_name] = _select_source_column(source_columns, candidates)

    return resolved


def normalize_selected_columns(
    df: pd.DataFrame,
    resolved_mapping: dict[str, str | None],
) -> pd.DataFrame:
    normalized = pd.DataFrame(index=df.index)

    for canonical_name, source_column in resolved_mapping.items():
        if source_column is None:
            normalized[canonical_name] = pd.NA
        else:
            normalized[canonical_name] = df[source_column]

    return normalized


def prepare_refined_dataframe(
    df: pd.DataFrame,
    resolved_mapping: dict[str, str | None],
    epidemiological_year: int | None = None,
) -> tuple[pd.DataFrame, dict[str, int]]:
    if _is_aggregated_srag_schema(resolved_mapping):
        return prepare_aggregated_refined_dataframe(df, resolved_mapping, epidemiological_year)

    refined = normalize_selected_columns(df, resolved_mapping)
    invalid_dates: dict[str, int] = {}

    for column in DATE_COLUMNS.intersection(refined.columns):
        original_non_null = refined[column].notna()
        converted = _parse_datetime_series(refined[column])
        invalid_dates[column] = int(original_non_null.sum() - converted.notna().sum())
        refined[column] = converted

    refined["canonical_case_date"] = refined["case_date"].fillna(refined["notification_date"])
    refined = refined[refined["canonical_case_date"].notna()].copy()
    refined["canonical_case_date"] = _parse_datetime_series(refined["canonical_case_date"])
    refined = refined[refined["canonical_case_date"].notna()].copy()

    for column in ["evolution", "icu", "vaccination", "state", "city", "final_classification"]:
        if column in refined.columns:
            refined[column] = refined[column].map(_normalize_value)

    return refined.reset_index(drop=True), invalid_dates


def prepare_aggregated_refined_dataframe(
    df: pd.DataFrame,
    resolved_mapping: dict[str, str | None],
    epidemiological_year: int | None = None,
) -> tuple[pd.DataFrame, dict[str, int]]:
    normalized = normalize_selected_columns(df, resolved_mapping)
    invalid_dates: dict[str, int] = {}
    year = epidemiological_year or date.today().year

    refined = pd.DataFrame(
        {
            "epidemiological_week": pd.to_numeric(
                normalized["epidemiological_week"], errors="coerce"
            ),
            "cases": pd.to_numeric(normalized["cases"], errors="coerce").fillna(0).astype(int),
            "deaths": pd.to_numeric(normalized["deaths"], errors="coerce").fillna(0).astype(int),
            "state": _optional_series(normalized, "state", df.index).map(_normalize_value),
            "city": _optional_series(normalized, "city", df.index).map(_normalize_value),
            "city_code": normalized.get("city_code", pd.Series(pd.NA, index=df.index)),
            "age_group": _optional_series(normalized, "age_group", df.index).map(_normalize_value),
            "health_region": _optional_series(
                normalized, "health_region", df.index
            ).map(_normalize_value),
        }
    )
    invalid_week_rows = int(refined["epidemiological_week"].isna().sum())
    invalid_dates["epidemiological_week"] = invalid_week_rows
    refined = refined[refined["epidemiological_week"].notna()].copy()
    refined["epidemiological_week"] = refined["epidemiological_week"].astype(int)
    refined["canonical_case_date"] = refined["epidemiological_week"].map(
        lambda week: _epidemiological_week_start(year, int(week))
    )
    refined["source_schema"] = "aggregated"

    return refined.reset_index(drop=True), invalid_dates


def run_preprocessing(
    raw_file: Path,
    run_id: str,
    *,
    extra_raw_files: list[Path] | None = None,
    settings: Settings | None = None,
    project_root: Path | None = None,
) -> PreprocessingResult:
    loaded_settings = settings or load_settings()
    raw_files = [raw_file, *(extra_raw_files or [])]
    mapping = load_column_mapping()
    raw_frames: list[pd.DataFrame] = []
    refined_frames: list[pd.DataFrame] = []
    invalid_dates: dict[str, int] = {}
    resolved_mapping: dict[str, str | None] = {}

    for current_raw_file in raw_files:
        current_raw_df = load_raw_srag_excel(current_raw_file)
        current_mapping = resolve_column_mapping(current_raw_df, mapping)
        current_year = _infer_epidemiological_year(current_raw_file, run_id)
        current_refined_df, current_invalid_dates = prepare_refined_dataframe(
            current_raw_df,
            current_mapping,
            epidemiological_year=current_year,
        )
        raw_frames.append(current_raw_df)
        refined_frames.append(current_refined_df)
        resolved_mapping = _merge_resolved_mapping(resolved_mapping, current_mapping)
        invalid_dates = _merge_invalid_dates(invalid_dates, current_invalid_dates)

    raw_df = pd.concat(raw_frames, ignore_index=True) if raw_frames else pd.DataFrame()
    refined_df = pd.concat(refined_frames, ignore_index=True) if refined_frames else pd.DataFrame()

    refined_dir = ensure_directory(
        resolve_project_path(loaded_settings.paths.refined_dir / run_id, root=project_root)
    )
    artifacts_dir = ensure_directory(
        resolve_project_path(loaded_settings.paths.artifacts_dir / run_id, root=project_root)
    )
    parquet_path = refined_dir / "srag_total.parquet"
    report_path = artifacts_dir / "data_quality_report.json"

    refined_df.to_parquet(parquet_path, index=False)

    report = build_data_quality_report(
        raw_df=raw_df,
        refined_df=refined_df,
        resolved_mapping=resolved_mapping,
        invalid_dates=invalid_dates,
    )
    write_data_quality_report(report, report_path)

    return PreprocessingResult(
        run_id=run_id,
        refined_dir=refined_dir,
        parquet_path=parquet_path,
        data_quality_report_path=report_path,
        rows_raw=len(raw_df),
        rows_refined=len(refined_df),
    )


def _merge_resolved_mapping(
    base_mapping: dict[str, str | None],
    next_mapping: dict[str, str | None],
) -> dict[str, str | None]:
    merged = dict(base_mapping)
    for canonical_name, source_column in next_mapping.items():
        if merged.get(canonical_name) is None:
            merged[canonical_name] = source_column
    return merged


def _merge_invalid_dates(
    base_invalid_dates: dict[str, int],
    next_invalid_dates: dict[str, int],
) -> dict[str, int]:
    merged = dict(base_invalid_dates)
    for column, count in next_invalid_dates.items():
        merged[column] = merged.get(column, 0) + count
    return merged


def _is_aggregated_srag_schema(resolved_mapping: dict[str, str | None]) -> bool:
    return all(resolved_mapping.get(column) for column in AGGREGATED_REQUIRED_COLUMNS)


def _epidemiological_week_start(year: int, week: int) -> pd.Timestamp:
    try:
        return pd.Timestamp(date.fromisocalendar(year, week, 1))
    except ValueError as error:
        raise ValueError(f"Invalid epidemiological week {week} for year {year}") from error


def _infer_epidemiological_year(raw_file: Path, run_id: str) -> int:
    metadata_path = raw_file.parent / "ingestion_metadata.json"
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        selected_folder = str(metadata.get("selected_folder", ""))
        if selected_folder[:4].isdigit():
            return int(selected_folder[:4])

    if run_id[:4].isdigit():
        return int(run_id[:4])

    return date.today().year


def _parse_datetime_series(series: pd.Series) -> pd.Series:
    text = series.astype("string")
    iso_mask = text.str.contains("T", na=False)
    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    if iso_mask.any():
        parsed.loc[iso_mask] = pd.to_datetime(
            series.loc[iso_mask], errors="coerce", utc=True
        ).dt.tz_localize(None)
    if (~iso_mask).any():
        parsed.loc[~iso_mask] = pd.to_datetime(
            series.loc[~iso_mask], errors="coerce", dayfirst=True
        )
    return parsed


def _extract_candidates(entry: Any) -> list[str]:
    if hasattr(entry, "candidates"):
        return [str(candidate) for candidate in entry.candidates]
    if isinstance(entry, dict):
        return [str(candidate) for candidate in entry.get("candidates", [])]
    raise ValueError(f"Invalid column mapping entry: {entry!r}")


def _select_source_column(source_columns: dict[str, str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        for key in _column_match_keys(candidate):
            if key in source_columns:
                return source_columns[key]
    return None


def _column_match_keys(value: str) -> set[str]:
    values = {value, _repair_mojibake(value)}
    keys = {item.upper() for item in values}
    keys.update(_simplify_column_name(item) for item in values)
    return {key for key in keys if key}


def _repair_mojibake(value: str) -> str:
    try:
        return value.encode("latin1").decode("utf-8")
    except UnicodeError:
        return value


def _simplify_column_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Z0-9]+", "", ascii_text.upper())


def _optional_series(df: pd.DataFrame, column: str, index: pd.Index) -> pd.Series:
    if column in df.columns:
        return df[column]
    return pd.Series(pd.NA, index=index)


def _normalize_value(value: object) -> object:
    if pd.isna(value):
        return pd.NA
    if isinstance(value, str):
        stripped = value.strip()
        return stripped.upper() if stripped else pd.NA
    return value




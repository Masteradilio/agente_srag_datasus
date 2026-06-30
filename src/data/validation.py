import json
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]

from data.schema import DataQualityReport
from utils.paths import ensure_directory

ROW_LEVEL_REQUIRED_COLUMNS = {"case_date", "notification_date"}
AGGREGATED_REQUIRED_COLUMNS = {"epidemiological_week", "cases", "deaths"}


def build_data_quality_report(
    *,
    raw_df: pd.DataFrame,
    refined_df: pd.DataFrame,
    resolved_mapping: dict[str, str | None],
    invalid_dates: dict[str, int],
) -> DataQualityReport:
    required_columns = _required_columns_for_schema(resolved_mapping)
    missing_columns = [
        canonical_name
        for canonical_name, source_column in resolved_mapping.items()
        if source_column is None
    ]
    missing_required = [
        canonical_name
        for canonical_name in missing_columns
        if canonical_name in required_columns
    ]
    missing_optional = [
        canonical_name
        for canonical_name in missing_columns
        if canonical_name not in required_columns
    ]

    selected_columns = list(resolved_mapping)
    null_rates = {
        column: float(refined_df[column].isna().mean())
        for column in selected_columns
        if column in refined_df.columns
    }
    warnings = _build_warnings(missing_required, missing_optional, invalid_dates)

    return DataQualityReport(
        rows_raw=len(raw_df),
        rows_refined=len(refined_df),
        columns_raw=len(raw_df.columns),
        columns_selected=len(selected_columns),
        invalid_dates=invalid_dates,
        missing_required_columns=missing_required,
        missing_optional_columns=missing_optional,
        null_rate_by_selected_column=null_rates,
        discarded_rows=max(len(raw_df) - len(refined_df), 0),
        warnings=warnings,
    )


def write_data_quality_report(report: DataQualityReport, output_path: Path) -> Path:
    ensure_directory(output_path.parent)
    output_path.write_text(
        json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    output_path.with_suffix(".md").write_text(_data_quality_markdown(report), encoding="utf-8")
    return output_path


def _data_quality_markdown(report: DataQualityReport) -> str:
    missing_optional = report.missing_optional_columns or ["nenhuma"]
    missing_required = report.missing_required_columns or ["nenhuma"]
    warnings = report.warnings or ["nenhum aviso"]
    null_rates = [
        f"- `{column}`: {rate:.2%}"
        for column, rate in sorted(report.null_rate_by_selected_column.items())
    ] or ["- Nenhuma coluna selecionada para calculo de nulos."]

    return "\n".join(
        [
            "# Data Quality Report",
            "",
            "## Linhas e Colunas",
            f"- Linhas brutas: {report.rows_raw}",
            f"- Linhas refinadas: {report.rows_refined}",
            f"- Colunas brutas: {report.columns_raw}",
            f"- Colunas selecionadas: {report.columns_selected}",
            f"- Linhas descartadas: {report.discarded_rows}",
            "",
            "## Colunas Obrigatorias Ausentes",
            *(f"- `{column}`" for column in missing_required),
            "",
            "## Colunas Opcionais Ausentes",
            *(f"- `{column}`" for column in missing_optional),
            "",
            "## Datas Invalidas",
            *(
                f"- `{column}`: {count}"
                for column, count in sorted(report.invalid_dates.items())
            ),
            "",
            "## Taxa de Nulos por Coluna Selecionada",
            *null_rates,
            "",
            "## Avisos",
            *(f"- {warning}" for warning in warnings),
            "",
        ]
    )


def _build_warnings(
    missing_required: list[str],
    missing_optional: list[str],
    invalid_dates: dict[str, int],
) -> list[str]:
    warnings: list[str] = []

    if missing_required:
        warnings.append(f"Missing required columns: {', '.join(missing_required)}")
    if missing_optional:
        warnings.append(f"Missing optional columns: {', '.join(missing_optional)}")

    invalid_date_columns = [
        f"{column}={count}"
        for column, count in invalid_dates.items()
        if count > 0
    ]
    if invalid_date_columns:
        warnings.append(f"Invalid dates detected: {', '.join(invalid_date_columns)}")

    return warnings


def _required_columns_for_schema(resolved_mapping: dict[str, str | None]) -> set[str]:
    if all(resolved_mapping.get(column) for column in AGGREGATED_REQUIRED_COLUMNS):
        return AGGREGATED_REQUIRED_COLUMNS
    return ROW_LEVEL_REQUIRED_COLUMNS


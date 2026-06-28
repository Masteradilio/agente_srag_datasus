import json
from pathlib import Path

import pandas as pd

from config import load_column_mapping, load_settings
from data.preprocessing import (
    load_raw_srag_excel,
    prepare_refined_dataframe,
    resolve_column_mapping,
    run_preprocessing,
)


def _raw_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "DT_SIN_PRI": ["01/06/2026", None, "invalid"],
            "DT_NOTIFIC": ["02/06/2026", "03/06/2026", None],
            "EVOLUCAO": [1, 2, None],
            "DT_EVOLUCA": ["05/06/2026", "bad-date", None],
            "UTI": [1, 2, None],
            "VACINA_COV": [1, 9, None],
            "SG_UF_NOT": ["sp", "RJ", None],
            "ID_MUNICIP": ["Sao Paulo", "Rio de Janeiro", None],
            "CLASSI_FIN": [5, 4, None],
        }
    )


def test_load_raw_srag_excel(tmp_path: Path) -> None:
    excel_path = tmp_path / "srag_total.xlsx"
    _raw_dataframe().to_excel(excel_path, index=False)

    loaded = load_raw_srag_excel(excel_path)

    assert len(loaded) == 3
    assert "DT_SIN_PRI" in loaded.columns


def test_load_raw_srag_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "INFLUD26.csv"
    csv_path.write_text("DT_SIN_PRI;UTI;VACINA\n2026-06-01;1;2\n", encoding="latin1")

    loaded = load_raw_srag_excel(csv_path)

    assert len(loaded) == 1
    assert "UTI" in loaded.columns


def test_resolve_column_mapping_and_prepare_refined_dataframe() -> None:
    raw_df = _raw_dataframe()
    mapping = load_column_mapping()
    resolved = resolve_column_mapping(raw_df, mapping)

    refined, invalid_dates = prepare_refined_dataframe(raw_df, resolved)

    assert resolved["case_date"] == "DT_SIN_PRI"
    assert resolved["notification_date"] == "DT_NOTIFIC"
    assert len(refined) == 2
    assert refined.loc[1, "canonical_case_date"] == pd.Timestamp("2026-06-03")
    assert invalid_dates["case_date"] == 1
    assert invalid_dates["evolution_date"] == 1
    assert refined.loc[0, "state"] == "SP"


def test_run_preprocessing_writes_parquet_and_quality_report(tmp_path: Path) -> None:
    raw_file = tmp_path / "landing" / "run-1" / "srag_total.xlsx"
    raw_file.parent.mkdir(parents=True)
    _raw_dataframe().to_excel(raw_file, index=False)

    result = run_preprocessing(
        raw_file,
        "run-1",
        settings=load_settings(),
        project_root=tmp_path,
    )

    assert result.parquet_path.is_file()
    assert result.data_quality_report_path.is_file()
    assert pd.read_parquet(result.parquet_path).shape[0] == 2

    report = json.loads(result.data_quality_report_path.read_text(encoding="utf-8"))
    assert report["rows_raw"] == 3
    assert report["rows_refined"] == 2
    assert report["discarded_rows"] == 1


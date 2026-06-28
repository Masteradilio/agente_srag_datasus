import json

import pandas as pd

from data.validation import build_data_quality_report, write_data_quality_report


def test_build_data_quality_report_tracks_missing_columns_and_warnings() -> None:
    raw_df = pd.DataFrame({"DT_SIN_PRI": ["01/06/2026"]})
    refined_df = pd.DataFrame({"case_date": [pd.Timestamp("2026-06-01")]})
    resolved_mapping = {
        "case_date": "DT_SIN_PRI",
        "notification_date": None,
        "evolution": None,
    }

    report = build_data_quality_report(
        raw_df=raw_df,
        refined_df=refined_df,
        resolved_mapping=resolved_mapping,
        invalid_dates={"case_date": 0},
    )

    assert report.missing_required_columns == ["notification_date"]
    assert report.missing_optional_columns == ["evolution"]
    assert report.discarded_rows == 0
    assert report.warnings


def test_write_data_quality_report(tmp_path) -> None:
    report = build_data_quality_report(
        raw_df=pd.DataFrame({"a": [1]}),
        refined_df=pd.DataFrame({"case_date": [pd.Timestamp("2026-06-01")]}),
        resolved_mapping={"case_date": "a"},
        invalid_dates={"case_date": 0},
    )
    output_path = tmp_path / "artifacts" / "data_quality_report.json"

    write_data_quality_report(report, output_path)

    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written["rows_raw"] == 1


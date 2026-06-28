import pytest

from data.ingestion import parse_folder_version, select_latest_folder


def test_parse_folder_version() -> None:
    assert parse_folder_version("2026_24") == (2026, 24)
    assert parse_folder_version("2025") == (2025,)


def test_select_latest_folder_prefers_year_and_suffix() -> None:
    folders = ["2024", "README", "2026_02", "2026_24", "2025"]

    assert select_latest_folder(folders) == "2026_24"


def test_select_latest_folder_uses_year_when_only_years_exist() -> None:
    assert select_latest_folder(["2023", "2025", "2024"]) == "2025"


def test_select_latest_folder_fails_without_valid_folder() -> None:
    with pytest.raises(ValueError, match="No valid SRAG folders"):
        select_latest_folder(["latest", "arquivo"])


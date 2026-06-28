import json
from pathlib import Path

from config import load_settings
from data.ingestion import run_ingestion


class FakeIngestionClient:
    def list_srag_folders(self) -> list[str]:
        return ["2024", "2026_24", "invalid"]

    def download_file(self, repository_path: str) -> bytes:
        assert repository_path == "Dados unificados/Unificado Srag/2026_24/srag_total.xlsx"
        return b"fake-xlsx"

    def raw_file_url(self, repository_path: str) -> str:
        return f"https://gitlab.com/api/v4/mock/{repository_path}"


def test_run_ingestion_creates_landing_file_and_metadata(tmp_path: Path) -> None:
    settings = load_settings()

    result = run_ingestion(
        "test-run",
        client=FakeIngestionClient(),
        settings=settings,
        project_root=tmp_path,
    )

    assert result.selected_folder == "2026_24"
    assert result.bytes_downloaded == len(b"fake-xlsx")
    assert result.raw_file_path.read_bytes() == b"fake-xlsx"
    assert result.raw_file_path == tmp_path / "data" / "landing" / "test-run" / "srag_total.xlsx"

    metadata_path = result.landing_dir / "ingestion_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert metadata["run_id"] == "test-run"
    assert metadata["selected_folder"] == "2026_24"
    assert metadata["raw_file_hash"] == result.raw_file_hash


class FakeOpenDataSUSClient:
    def download_latest_csv(self) -> bytes:
        return b"col1;col2\n1;2\n"

    def source_url(self) -> str:
        return "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SRAG/2026/test.csv"


def test_run_ingestion_uses_opendatasus_primary_source(tmp_path: Path) -> None:
    result = run_ingestion(
        "csv-run",
        client=FakeOpenDataSUSClient(),
        settings=load_settings(),
        project_root=tmp_path,
    )

    assert result.raw_file_path.name == "INFLUD26-22-06-2026.csv"
    assert result.raw_file_path.read_bytes() == b"col1;col2\n1;2\n"
    assert result.selected_folder == "opendatasus-2026"


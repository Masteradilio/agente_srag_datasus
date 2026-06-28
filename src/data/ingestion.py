import json
import logging
import re
from pathlib import Path
from typing import Protocol

from config import Settings, load_settings
from data.gitlab_client import GitLabClient
from data.opendatasus_client import OpenDataSUSClient
from data.schema import IngestionResult
from utils.dates import generate_run_id, now_in_timezone
from utils.hashing import calculate_sha256
from utils.paths import ensure_directory, resolve_project_path


class IngestionClient(Protocol):
    def list_srag_folders(self) -> list[str]:
        ...

    def download_file(self, repository_path: str) -> bytes:
        ...

    def raw_file_url(self, repository_path: str) -> str:
        ...


class OpenDataSUSIngestionClient(Protocol):
    def download_latest_csv(self) -> bytes:
        ...

    def source_url(self) -> str:
        ...


def parse_folder_version(folder_name: str) -> tuple[int, ...]:
    if not re.match(r"^20\d{2}(?:\D|$)", folder_name):
        raise ValueError(f"Invalid SRAG folder name: {folder_name}")

    numbers = tuple(int(value) for value in re.findall(r"\d+", folder_name))
    if not numbers:
        raise ValueError(f"Invalid SRAG folder name: {folder_name}")
    return numbers


def select_latest_folder(folder_names: list[str]) -> str:
    valid_folders: list[tuple[tuple[int, ...], str]] = []

    for folder_name in folder_names:
        try:
            valid_folders.append((parse_folder_version(folder_name), folder_name))
        except ValueError:
            logging.getLogger(__name__).warning("Ignoring invalid SRAG folder: %s", folder_name)

    if not valid_folders:
        raise ValueError("No valid SRAG folders found.")

    return max(valid_folders, key=lambda item: item[0])[1]


def build_srag_file_repository_path(settings: Settings, selected_folder: str) -> str:
    return "/".join(
        [
            settings.gitlab.srag_tree_path.strip("/"),
            selected_folder.strip("/"),
            settings.gitlab.target_file,
        ]
    )


def run_ingestion(
    run_id: str | None = None,
    *,
    client: IngestionClient | OpenDataSUSIngestionClient | None = None,
    settings: Settings | None = None,
    project_root: Path | None = None,
) -> IngestionResult:
    loaded_settings = settings or load_settings()
    current_run_id = run_id or generate_run_id(loaded_settings.project.default_run_timezone)

    if (
        loaded_settings.data_source.primary == "opendatasus_csv"
        and (client is None or hasattr(client, "download_latest_csv"))
    ):
        return _run_opendatasus_ingestion(
            current_run_id,
            client or OpenDataSUSClient(loaded_settings.opendatasus),  # type: ignore[arg-type]
            loaded_settings,
            project_root,
        )

    ingestion_client = client or GitLabClient(loaded_settings.gitlab)
    return _run_gitlab_ingestion(
        current_run_id,
        ingestion_client,  # type: ignore[arg-type]
        loaded_settings,
        project_root,
    )


def _run_gitlab_ingestion(
    run_id: str,
    ingestion_client: IngestionClient,
    settings: Settings,
    project_root: Path | None,
) -> IngestionResult:
    folder_names = ingestion_client.list_srag_folders()
    selected_folder = select_latest_folder(folder_names)
    repository_path = build_srag_file_repository_path(settings, selected_folder)
    raw_bytes = ingestion_client.download_file(repository_path)

    landing_dir = ensure_directory(
        resolve_project_path(settings.paths.landing_dir / run_id, root=project_root)
    )
    raw_file_path = landing_dir / settings.gitlab.target_file
    raw_file_path.write_bytes(raw_bytes)

    result = IngestionResult(
        run_id=run_id,
        selected_folder=selected_folder,
        source_url=ingestion_client.raw_file_url(repository_path),
        landing_dir=landing_dir,
        raw_file_path=raw_file_path,
        raw_file_hash=calculate_sha256(raw_file_path),
        bytes_downloaded=len(raw_bytes),
        downloaded_at=now_in_timezone(settings.project.default_run_timezone).isoformat(),
    )

    _write_ingestion_metadata(result)

    return result


def _run_opendatasus_ingestion(
    run_id: str,
    ingestion_client: OpenDataSUSIngestionClient,
    settings: Settings,
    project_root: Path | None,
) -> IngestionResult:
    raw_bytes = ingestion_client.download_latest_csv()
    landing_dir = ensure_directory(
        resolve_project_path(settings.paths.landing_dir / run_id, root=project_root)
    )
    raw_file_path = landing_dir / settings.opendatasus.target_file
    raw_file_path.write_bytes(raw_bytes)

    result = IngestionResult(
        run_id=run_id,
        selected_folder="opendatasus-2026",
        source_url=ingestion_client.source_url(),
        landing_dir=landing_dir,
        raw_file_path=raw_file_path,
        raw_file_hash=calculate_sha256(raw_file_path),
        bytes_downloaded=len(raw_bytes),
        downloaded_at=now_in_timezone(settings.project.default_run_timezone).isoformat(),
    )
    _write_ingestion_metadata(result)
    return result


def _write_ingestion_metadata(result: IngestionResult) -> None:
    metadata_path = result.landing_dir / "ingestion_metadata.json"
    metadata_path.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def resolve_project_path(path: str | Path, root: Path | None = None) -> Path:
    raw_path = Path(path)
    if raw_path.is_absolute():
        return raw_path
    return (root or PROJECT_ROOT) / raw_path


def ensure_directory(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def ensure_project_directories(paths: list[str | Path], root: Path | None = None) -> list[Path]:
    return [ensure_directory(resolve_project_path(path, root=root)) for path in paths]


def load_yaml(path: str | Path) -> dict[str, Any]:
    config_path = resolve_project_path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"YAML configuration file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file)

    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError(f"YAML configuration must contain a mapping: {config_path}")
    return loaded

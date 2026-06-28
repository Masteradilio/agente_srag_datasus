from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, HttpUrl

from utils.paths import load_yaml


class ProjectConfig(BaseModel):
    name: str
    default_run_timezone: str


class PathsConfig(BaseModel):
    landing_dir: Path
    refined_dir: Path
    artifacts_dir: Path
    docs_dir: Path


class DataSourceConfig(BaseModel):
    primary: str = "opendatasus_csv"


class OpenDataSUSConfig(BaseModel):
    dataset_url: HttpUrl
    latest_csv_url: HttpUrl
    target_file: str
    csv_separator: str = ";"
    csv_encoding: str = "latin1"


class GitLabConfig(BaseModel):
    base_url: HttpUrl
    project_path: str
    srag_tree_path: str
    target_file: str


class PrivacyConfig(BaseModel):
    min_group_size: int = Field(ge=1)


class NewsConfig(BaseModel):
    max_sources_per_report: int = Field(ge=1, le=10)
    request_timeout_seconds: int = Field(ge=1)


class Settings(BaseModel):
    project: ProjectConfig
    paths: PathsConfig
    data_source: DataSourceConfig
    opendatasus: OpenDataSUSConfig
    gitlab: GitLabConfig
    privacy: PrivacyConfig
    news: NewsConfig


class NewsSourcesConfig(BaseModel):
    allowed_domains: list[str] = Field(min_length=1, max_length=10)


class ColumnMappingEntry(BaseModel):
    candidates: list[str] = Field(min_length=1)


ColumnMapping = dict[str, ColumnMappingEntry]


def load_settings(path: str | Path = "configs/settings.yaml") -> Settings:
    return Settings.model_validate(load_yaml(path))


def load_news_sources(path: str | Path = "configs/news_sources.yaml") -> NewsSourcesConfig:
    return NewsSourcesConfig.model_validate(load_yaml(path))


def load_column_mapping(path: str | Path = "configs/column_mapping.yaml") -> ColumnMapping:
    raw_mapping = load_yaml(path)
    if not isinstance(raw_mapping, dict):
        raise ValueError("Column mapping configuration must be a mapping.")
    return {
        str(concept): ColumnMappingEntry.model_validate(value)
        for concept, value in raw_mapping.items()
    }


def load_metric_catalog(path: str | Path = "configs/metric_catalog.yaml") -> dict[str, Any]:
    raw_catalog = load_yaml(path)
    if not isinstance(raw_catalog, dict):
        raise ValueError("Metric catalog configuration must be a mapping.")
    return raw_catalog


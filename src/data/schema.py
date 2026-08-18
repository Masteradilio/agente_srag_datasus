from pathlib import Path

from pydantic import BaseModel, Field


class GitLabTreeItem(BaseModel):
    id: str | None = None
    name: str
    type: str
    path: str
    mode: str | None = None


class IngestionResult(BaseModel):
    run_id: str
    selected_folder: str
    source_url: str
    landing_dir: Path
    raw_file_path: Path
    raw_file_hash: str = Field(min_length=64, max_length=64)
    bytes_downloaded: int = Field(ge=0)
    downloaded_at: str


class DataQualityReport(BaseModel):
    rows_raw: int = Field(ge=0)
    rows_refined: int = Field(ge=0)
    columns_raw: int = Field(ge=0)
    columns_selected: int = Field(ge=0)
    invalid_dates: dict[str, int]
    missing_required_columns: list[str]
    missing_optional_columns: list[str]
    null_rate_by_selected_column: dict[str, float]
    discarded_rows: int = Field(ge=0)
    warnings: list[str]


class PreprocessingResult(BaseModel):
    run_id: str
    refined_dir: Path
    parquet_path: Path
    data_quality_report_path: Path
    rows_raw: int = Field(ge=0)
    rows_refined: int = Field(ge=0)


class MetricValue(BaseModel):
    name: str
    value: float | None
    numerator: int
    denominator: int
    limitations: list[str] = Field(default_factory=list)


class EtiologyCount(BaseModel):
    etiology: str
    cases: int = Field(ge=0)
    percentage: float = Field(ge=0.0, le=1.0)


class AgeGroupCount(BaseModel):
    age_group: str
    cases: int = Field(ge=0)
    percentage: float = Field(ge=0.0, le=1.0)
    icu_rate: float | None = None
    mortality_rate: float | None = None


class AnomalyAlert(BaseModel):
    dimension: str
    category: str
    z_score: float
    current_period_cases: int
    previous_period_cases: int
    growth_rate: float | None
    severity: str = "warning"  # info, warning, critical
    description: str


class AnomalySummary(BaseModel):
    total_anomalies: int = Field(ge=0)
    alerts: list[AnomalyAlert] = Field(default_factory=list)


class MetricSummary(BaseModel):
    reference_date: str
    total_cases: int = Field(ge=0)
    case_growth_rate_7d: MetricValue
    known_mortality_rate: MetricValue
    crude_mortality_rate: MetricValue
    icu_case_rate: MetricValue
    registered_vaccination_case_rate: MetricValue
    etiology_distribution: list[EtiologyCount] = Field(default_factory=list)
    age_distribution: list[AgeGroupCount] = Field(default_factory=list)
    anomalies: AnomalySummary = Field(default_factory=lambda: AnomalySummary(total_anomalies=0, alerts=[]))
    limitations: list[str] = Field(default_factory=list)


class NewsSearchResult(BaseModel):
    title: str
    url: str
    source_domain: str
    published_at: str | None = None
    snippet: str = ""
    source_channel: str = "web"


class NewsArticle(BaseModel):
    title: str
    url: str
    source_domain: str
    published_at: str | None = None
    content: str = ""
    excerpt: str = ""
    extraction_status: str = "success"
    source_channel: str = "web"


class DocumentSource(BaseModel):
    source_path: str
    source_type: str
    content: str
    metadata: dict[str, str] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    chunk_id: str
    source_path: str
    source_type: str
    content: str
    metadata: dict[str, str] = Field(default_factory=dict)


class RetrievedDocument(BaseModel):
    chunk_id: str
    source_path: str
    source_type: str
    content: str
    score: float
    metadata: dict[str, str] = Field(default_factory=dict)

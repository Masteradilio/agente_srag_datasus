from config import (
    load_column_mapping,
    load_metric_catalog,
    load_news_sources,
    load_settings,
)


def test_load_settings() -> None:
    settings = load_settings()

    assert settings.project.name == "agente_srag_datasus"
    assert settings.data_source.primary == "opendatasus_csv"
    assert settings.opendatasus.target_file == "INFLUD26-22-06-2026.csv"
    assert settings.gitlab.project_path == "cgcovid/dados-abertos"
    assert settings.gitlab.target_file == "srag_total.xlsx"
    assert settings.privacy.min_group_size == 10


def test_news_allowlist_has_expected_limit_and_domains() -> None:
    news_sources = load_news_sources()

    assert len(news_sources.allowed_domains) <= 10
    assert "gitlab.com/cgcovid/dados-abertos" in news_sources.allowed_domains
    assert "who.int" in news_sources.allowed_domains


def test_load_column_mapping() -> None:
    mapping = load_column_mapping()

    assert mapping["case_date"].candidates == ["DT_SIN_PRI", "DT_NOTIFIC"]
    assert "vaccination" in mapping


def test_load_metric_catalog() -> None:
    catalog = load_metric_catalog()

    assert "metrics" in catalog
    assert "case_growth_rate_7d" in catalog["metrics"]
    assert "charts" in catalog


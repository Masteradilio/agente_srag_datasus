import json

import pandas as pd

from data.schema import NewsArticle, NewsSearchResult
from pipeline import run_pipeline

REQUIRED_RUN_ARTIFACTS = [
    "data_quality_report.json",
    "data_quality_report.md",
    "metrics.json",
    "news_sources.json",
    "observability.json",
    "agent_trace.jsonl",
    "chart_context.json",
    "report.md",
    "report.pdf",
    "charts/daily_cases_30d.png",
    "charts/monthly_cases_12m.png",
]


def test_pipeline_smoke_generates_final_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DISABLE_LLM_API", "1")

    def fake_search_srag_news(query, allowed_domains, max_results, candidates):
        del query, candidates
        return [
            NewsSearchResult(
                title=f"Noticia SRAG {index}",
                url=f"https://{domain}/noticias/srag-{index}",
                source_domain=domain,
                published_at=f"2026-06-{index:02d}",
                snippet="Noticia sobre SRAG em fonte permitida.",
            )
            for index, domain in enumerate(allowed_domains[:max_results], start=1)
        ]

    def fake_extract_news_article(url, allowed_domains, timeout_seconds=8):
        del allowed_domains, timeout_seconds
        domain = url.split("/")[2]
        return NewsArticle(
            title=f"Fonte validada {domain}",
            url=url,
            source_domain=domain,
            published_at="2026-06-20",
            excerpt="Conteudo extraido de fonte permitida sobre SRAG.",
            extraction_status="success",
        )

    monkeypatch.setattr("agents.tools.search_srag_news", fake_search_srag_news)
    monkeypatch.setattr("agents.tools.extract_news_article", fake_extract_news_article)

    raw_file = tmp_path / "INFLUD26-22-06-2026.csv"
    pd.DataFrame(
        {
            "DT_SIN_PRI": pd.date_range("2026-06-01", periods=40, freq="D").strftime(
                "%d/%m/%Y"
            ),
            "DT_NOTIFIC": pd.date_range("2026-06-01", periods=40, freq="D").strftime(
                "%d/%m/%Y"
            ),
            "EVOLUCAO": ["1", "2"] * 20,
            "UTI": ["1", "2"] * 20,
            "VACINA_COV": ["1", "2"] * 20,
            "SG_UF_NOT": ["SP"] * 40,
            "ID_MUNICIP": ["SAO PAULO"] * 40,
            "CLASSI_FIN": ["SRAG"] * 40,
        }
    ).to_csv(raw_file, sep=";", encoding="latin1", index=False)

    result = run_pipeline(run_id="pytest-pipeline-smoke", raw_file=raw_file)
    run_dir = result.artifacts_dir

    assert result.manifest_path.is_file()
    assert result.report_markdown_path.is_file()
    assert result.report_pdf_path.is_file()
    for artifact in REQUIRED_RUN_ARTIFACTS:
        assert (run_dir / artifact).is_file(), f"Missing required artifact: {artifact}"

    report = result.report_markdown_path.read_text(encoding="utf-8")
    news_sources = json.loads((run_dir / "news_sources.json").read_text(encoding="utf-8"))

    assert len(news_sources) == 10
    assert "prompt_rules" not in report
    assert "C:\\Users" not in report
    assert "Métricas Principais" in report
    assert "Evolução Histórica" in report
    assert "Notícias Recentes" in report
    assert "Fontes Consultadas" in report
    assert "Observabilidade e Custos" not in report

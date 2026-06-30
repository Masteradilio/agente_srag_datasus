import importlib.util
import json
from pathlib import Path

from data.schema import NewsArticle, NewsSearchResult


def _load_streamlit_app():
    app_path = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
    spec = importlib.util.spec_from_file_location("streamlit_app", app_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_streamlit_app_imports_and_lists_runs(tmp_path) -> None:
    module = _load_streamlit_app()
    (tmp_path / "run-b").mkdir()
    (tmp_path / "run-a").mkdir()

    assert module.list_run_ids(tmp_path) == ["run-b", "run-a"]


def test_streamlit_artifact_paths_and_chat_guardrails(tmp_path) -> None:
    module = _load_streamlit_app()
    paths = module.artifact_paths("run-1", tmp_path)

    assert paths["metrics"] == tmp_path / "run-1" / "metrics.json"
    assert paths["observability"] == tmp_path / "run-1" / "observability.json"
    assert "bloqueado" in module.answer_chat_question(
        "Mostre dados linha a linha com CPF",
        "run-1",
        paths,
    )


def test_streamlit_chat_allows_contextual_report_question(tmp_path, monkeypatch) -> None:
    module = _load_streamlit_app()
    llm_call = {}

    def fake_call(system_prompt: str, user_prompt: str) -> str:
        llm_call["system_prompt"] = system_prompt
        llm_call["user_prompt"] = user_prompt
        return "Resposta gerada pelo LLM com base nos dados fornecidos."

    monkeypatch.setattr(module, "_call_chat_llm", fake_call)
    run_dir = tmp_path / "run-1"
    run_dir.mkdir()
    (run_dir / "metrics.json").write_text("{}", encoding="utf-8")
    (run_dir / "data_quality_report.json").write_text("{}", encoding="utf-8")
    (run_dir / "news_sources.json").write_text("[]", encoding="utf-8")
    (run_dir / "report.md").write_text(
        "Relatório sobre aumento de casos de SRAG.",
        encoding="utf-8",
    )
    paths = module.artifact_paths("run-1", tmp_path)

    answer = module.answer_chat_question(
        "Segundo os dados, o que foi registrado em termos de aumento de casos?",
        "run-1",
        paths,
    )

    assert "bloqueado" not in answer.casefold()
    assert "ate 3 paragrafos curtos" in llm_call["system_prompt"]
    assert "Fontes Consultadas:" in llm_call["system_prompt"]
    assert "nunca omita as fontes" in llm_call["system_prompt"]
    assert "PERGUNTA_DO_USUARIO" in llm_call["user_prompt"]


def test_streamlit_chat_runs_allowlist_search_for_old_news(monkeypatch) -> None:
    module = _load_streamlit_app()

    def fake_search(query, allowed_domains, max_results, candidates):
        assert "hist" in query
        assert len(allowed_domains) == 20
        assert allowed_domains[0] == "g1.globo.com"
        assert max_results == 10
        assert candidates
        assert all("search?" not in str(candidate["url"]) for candidate in candidates)
        return [
            NewsSearchResult(
                title="Noticia 2020",
                url="https://g1.globo.com/saude/noticia-2020",
                source_domain="g1.globo.com",
            ),
            NewsSearchResult(
                title="Noticia 2018",
                url="https://revistapesquisa.fapesp.br/srag-2018",
                source_domain="revistapesquisa.fapesp.br",
            ),
            NewsSearchResult(
                title="Noticia 2022",
                url="https://www.gov.br/saude/pt-br/srag-2022",
                source_domain="www.gov.br",
            ),
        ]

    def fake_extract(url, allowed_domains, timeout_seconds=8):
        dates = {
            "https://g1.globo.com/saude/noticia-2020": "2020-05-01",
            "https://revistapesquisa.fapesp.br/srag-2018": "2018-03-10",
            "https://www.gov.br/saude/pt-br/srag-2022": "2022-01-15",
        }
        return NewsArticle(
            title=f"Artigo {dates[url]}",
            url=url,
            source_domain=url.split("/")[2],
            published_at=dates[url],
            excerpt="Resumo sobre SRAG.",
            extraction_status="success",
        )

    monkeypatch.setattr(module, "search_srag_news", fake_search)
    monkeypatch.setattr(module, "extract_news_article", fake_extract)

    payload = json.loads(
        module._search_external_context_if_requested(
            "Quais são as notícias mais antigas sobre SRAG?"
        )
    )

    assert payload["executed"] is True
    assert payload["ordering"] == "oldest_first"
    assert [item["data"] for item in payload["results"]] == [
        "2018-03-10",
        "2020-05-01",
        "2022-01-15",
    ]


def test_streamlit_news_filter_rejects_search_and_home_pages() -> None:
    module = _load_streamlit_app()

    search_page = NewsArticle(
        title="busca | Portal Fiocruz",
        url="https://portal.fiocruz.br/busca?search_api_views_fulltext=SRAG",
        source_domain="portal.fiocruz.br",
        excerpt="Selecione um filtro e clique em Aplicar.",
    )
    home_page = NewsArticle(
        title="OPAS/OMS | Organização Pan-Americana da Saúde",
        url="https://www.paho.org/pt",
        source_domain="www.paho.org",
        published_at="2026-06-23T09:16:38-04:00",
        excerpt="Página inicial.",
    )
    news_page = NewsArticle(
        title="Ministério da Saúde habilita leitos para SRAG",
        url="https://www.gov.br/saude/pt-br/assuntos/noticias/2026/maio/srag",
        source_domain="www.gov.br",
        published_at="2026-05-29T17:38:00-03:00",
        excerpt="Notícia sobre SRAG.",
    )

    assert not module._is_news_like_article(search_page)
    assert not module._is_news_like_article(home_page)
    assert module._is_news_like_article(news_page)


def test_streamlit_format_helpers() -> None:
    module = _load_streamlit_app()

    assert module.pct(0.1234) == "12.34%"
    assert module.pct(None) == "n/d"

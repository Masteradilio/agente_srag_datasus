from srag_agent.data.schema import NewsSearchResult
from srag_agent.news.rank import rank_news_results
from srag_agent.news.search import search_srag_news


def test_news_ranking_prioritizes_official_relevant_recent_sources() -> None:
    results = [
        NewsSearchResult(
            title="Blog aleatorio",
            url="https://example.com/a",
            source_domain="example.com",
            snippet="texto qualquer",
        ),
        NewsSearchResult(
            title="Boletim SRAG influenza",
            url="https://www.gov.br/saude/a",
            source_domain="www.gov.br",
            published_at="2026-06-01T00:00:00+00:00",
            snippet="SRAG e influenza",
        ),
    ]

    assert rank_news_results(results)[0].source_domain == "www.gov.br"


def test_search_srag_news_filters_candidates_by_allowlist() -> None:
    candidates = [
        {"title": "SRAG", "url": "https://www.who.int/news/srag", "snippet": "SRAG"},
        {"title": "fora", "url": "https://example.com/srag", "snippet": "SRAG"},
    ]

    results = search_srag_news("SRAG", ["who.int"], 5, candidates=candidates)

    assert len(results) == 1
    assert results[0].source_domain == "www.who.int"

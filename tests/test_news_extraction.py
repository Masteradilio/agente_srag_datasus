import json

from data.schema import NewsSearchResult
from news.extract import extract_news_article
from news.sources import persist_news_sources


class FakeResponse:
    text = "<html><head><title>Boletim SRAG</title></head><body><p>SRAG em alta.</p></body></html>"

    def raise_for_status(self) -> None:
        return None


def fake_fetcher(url, timeout=None, headers=None):
    assert timeout == 20
    assert "User-Agent" in headers
    return FakeResponse()


def test_extract_news_article_with_mocked_fetcher() -> None:
    article = extract_news_article(
        "https://www.who.int/news/srag",
        allowed_domains=["who.int"],
        fetcher=fake_fetcher,
    )

    assert article.extraction_status == "success"
    assert article.title == "Boletim SRAG"
    assert "SRAG em alta" in article.excerpt


def test_extract_news_article_blocks_domain() -> None:
    article = extract_news_article(
        "https://example.com/news",
        allowed_domains=["who.int"],
        fetcher=fake_fetcher,
    )

    assert article.extraction_status == "blocked_domain"


def test_persist_news_sources(tmp_path) -> None:
    output_path = persist_news_sources(
        "run-1",
        [
            NewsSearchResult(
                title="SRAG",
                url="https://www.who.int/news/srag",
                source_domain="www.who.int",
            )
        ],
        artifacts_dir=tmp_path,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload[0]["source_domain"] == "www.who.int"


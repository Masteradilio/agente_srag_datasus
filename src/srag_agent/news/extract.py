from collections.abc import Callable

import requests  # type: ignore[import-untyped]
from bs4 import BeautifulSoup  # type: ignore[import-untyped]

from srag_agent.config import load_news_sources
from srag_agent.data.schema import NewsArticle
from srag_agent.guardrails.domain_allowlist import extract_domain, is_allowed_url

USER_AGENT = "agente_srag_datasus/0.1 (+https://github.com/Masteradilio/agente_srag_datasus)"


def extract_news_article(
    url: str,
    allowed_domains: list[str] | None = None,
    timeout_seconds: int = 20,
    fetcher: Callable[..., requests.Response] | None = None,
) -> NewsArticle:
    domains = allowed_domains or load_news_sources().allowed_domains
    source_domain = extract_domain(url)

    if not is_allowed_url(url, domains):
        return NewsArticle(
            title="",
            url=url,
            source_domain=source_domain,
            extraction_status="blocked_domain",
        )

    get = fetcher or requests.get
    try:
        response = get(
            url,
            timeout=timeout_seconds,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
    except Exception as error:
        return NewsArticle(
            title="",
            url=url,
            source_domain=source_domain,
            extraction_status=f"error: {type(error).__name__}",
        )

    soup = BeautifulSoup(response.text, "html.parser")
    title = _extract_title(soup)
    content = _extract_content(soup)
    excerpt = content[:700]

    return NewsArticle(
        title=title,
        url=url,
        source_domain=source_domain,
        content=content,
        excerpt=excerpt,
        extraction_status="success",
    )


def _extract_title(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    heading = soup.find("h1")
    return heading.get_text(" ", strip=True) if heading else ""


def _extract_content(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    paragraphs = [paragraph.get_text(" ", strip=True) for paragraph in soup.find_all("p")]
    return "\n".join(paragraph for paragraph in paragraphs if paragraph)

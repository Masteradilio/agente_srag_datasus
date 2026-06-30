import json
from collections.abc import Callable

import requests  # type: ignore[import-untyped]
from bs4 import BeautifulSoup  # type: ignore[import-untyped]

from config import load_news_sources
from data.schema import NewsArticle
from guardrails.domain_allowlist import extract_domain, is_allowed_url

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
        if source_domain == "infoms.saude.gov.br":
            return NewsArticle(
                title="InfoMS paineis oficiais",
                url=url,
                source_domain=source_domain,
                excerpt=(
                    "Painel oficial registrado como fonte complementar para indicadores "
                    "de saude, vacinacao e leitos; o portal pode bloquear extracao HTML "
                    "automatizada."
                ),
                extraction_status="metadata_only",
            )
        return NewsArticle(
            title="",
            url=url,
            source_domain=source_domain,
            extraction_status=f"error: {type(error).__name__}",
        )

    soup = BeautifulSoup(response.text, "html.parser")
    title = _extract_title(soup)
    published_at = _extract_published_at(soup)
    content = _extract_content(soup)
    excerpt = content[:700]

    return NewsArticle(
        title=title,
        url=url,
        source_domain=source_domain,
        published_at=published_at,
        content=content,
        excerpt=excerpt,
        extraction_status="success",
    )


def _extract_title(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    heading = soup.find("h1")
    return heading.get_text(" ", strip=True) if heading else ""


def _extract_published_at(soup: BeautifulSoup) -> str | None:
    selectors = [
        ("property", "article:published_time"),
        ("property", "og:published_time"),
        ("name", "date"),
        ("name", "dcterms.date"),
        ("name", "dc.date"),
        ("name", "publication_date"),
        ("itemprop", "datePublished"),
    ]
    for attr, value in selectors:
        tag = soup.find("meta", attrs={attr: value})
        content = str(tag.get("content") or "").strip() if tag else ""
        if content:
            return content

    time_tag = soup.find("time")
    if time_tag:
        datetime_value = str(time_tag.get("datetime") or "").strip()
        if datetime_value:
            return datetime_value
        text_value = time_tag.get_text(" ", strip=True)
        if text_value:
            return text_value

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            payload = json.loads(script.get_text(strip=True))
        except json.JSONDecodeError:
            continue
        published = _extract_json_ld_date(payload)
        if published:
            return published
    return None


def _extract_json_ld_date(payload: object) -> str | None:
    if isinstance(payload, list):
        for item in payload:
            published = _extract_json_ld_date(item)
            if published:
                return published
    if not isinstance(payload, dict):
        return None
    for key in ["datePublished", "dateCreated", "dateModified"]:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    graph = payload.get("@graph")
    return _extract_json_ld_date(graph) if graph else None


def _extract_content(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    paragraphs = [paragraph.get_text(" ", strip=True) for paragraph in soup.find_all("p")]
    return "\n".join(paragraph for paragraph in paragraphs if paragraph)

from collections.abc import Iterable
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests  # type: ignore[import-untyped]
from bs4 import BeautifulSoup  # type: ignore[import-untyped]

from data.schema import NewsSearchResult
from guardrails.domain_allowlist import extract_domain, is_allowed_url
from news.extract import USER_AGENT
from news.rank import rank_news_results

DUCKDUCKGO_ENDPOINT = "https://duckduckgo.com/html/"
BING_ENDPOINT = "https://www.bing.com/search"


def search_srag_news(
    query: str,
    allowed_domains: list[str],
    max_results: int,
    candidates: Iterable[dict[str, str | None]] | None = None,
) -> list[NewsSearchResult]:
    live_results = _search_allowlisted_web(query, allowed_domains, max_results=max_results)
    fallback_candidates = (
        list(_default_institutional_candidates(query, allowed_domains))
        if candidates is None
        else list(candidates)
    )
    candidate_results = _candidate_results(fallback_candidates, allowed_domains)
    deduped = _dedupe_results([*live_results, *candidate_results])
    return rank_news_results(deduped)[:max_results]


def _search_allowlisted_web(
    query: str,
    allowed_domains: list[str],
    *,
    max_results: int,
) -> list[NewsSearchResult]:
    results: list[NewsSearchResult] = []
    per_domain_limit = 2
    for allowed_domain in allowed_domains:
        search_query = f"{query} SRAG 2026 site:{allowed_domain}"
        try:
            duckduckgo_response = requests.get(
                DUCKDUCKGO_ENDPOINT,
                params={"q": search_query},
                headers={"User-Agent": USER_AGENT},
                timeout=20,
            )
            duckduckgo_response.raise_for_status()
        except Exception:
            duckduckgo_response = None

        parsed_results = (
            _parse_duckduckgo_results(duckduckgo_response.text, allowed_domains)
            if duckduckgo_response
            else []
        )
        if not parsed_results:
            parsed_results = _search_bing_html(search_query, allowed_domains)
        results.extend(parsed_results[:per_domain_limit])
        if len(results) >= max_results * 2:
            break
    return _dedupe_results(results)


def _search_bing_html(
    search_query: str,
    allowed_domains: list[str],
) -> list[NewsSearchResult]:
    try:
        response = requests.get(
            BING_ENDPOINT,
            params={"q": search_query},
            headers={"User-Agent": USER_AGENT},
            timeout=20,
        )
        response.raise_for_status()
    except Exception:
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    results: list[NewsSearchResult] = []
    for result in soup.select("li.b_algo"):
        link = result.select_one("h2 a")
        if not link:
            continue
        url = _normalize_search_url(str(link.get("href") or ""))
        if not is_allowed_url(url, allowed_domains) or _is_search_or_home_url(url):
            continue
        snippet_node = result.select_one(".b_caption p")
        title = link.get_text(" ", strip=True) or url
        snippet = snippet_node.get_text(" ", strip=True) if snippet_node else ""
        results.append(
            NewsSearchResult(
                title=title,
                url=url,
                source_domain=extract_domain(url),
                published_at=None,
                snippet=snippet,
            )
        )
    return results


def _parse_duckduckgo_results(
    html: str,
    allowed_domains: list[str],
) -> list[NewsSearchResult]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[NewsSearchResult] = []
    for result in soup.select(".result"):
        link = result.select_one("a.result__a")
        if not link:
            continue
        url = _normalize_search_url(str(link.get("href") or ""))
        if not is_allowed_url(url, allowed_domains) or _is_search_or_home_url(url):
            continue
        snippet_node = result.select_one(".result__snippet")
        title = link.get_text(" ", strip=True) or url
        snippet = snippet_node.get_text(" ", strip=True) if snippet_node else ""
        results.append(
            NewsSearchResult(
                title=title,
                url=url,
                source_domain=extract_domain(url),
                published_at=None,
                snippet=snippet,
            )
        )
    return results


def _candidate_results(
    candidates: Iterable[dict[str, str | None]],
    allowed_domains: list[str],
) -> list[NewsSearchResult]:
    results: list[NewsSearchResult] = []
    for candidate in candidates:
        url = str(candidate.get("url") or "")
        if not is_allowed_url(url, allowed_domains):
            continue
        results.append(
            NewsSearchResult(
                title=str(candidate.get("title") or url),
                url=url,
                source_domain=extract_domain(url),
                published_at=candidate.get("published_at"),
                snippet=str(candidate.get("snippet") or ""),
            )
        )
    return results


def _normalize_search_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.path.startswith("/l/"):
        uddg = parse_qs(parsed.query).get("uddg", [])
        if uddg:
            return unquote(uddg[0])
    if parsed.scheme:
        return url
    if url.startswith("//"):
        return f"https:{url}"
    return url


def _is_search_or_home_url(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if path in {"", "/pt-br", "/pt"}:
        return True
    if "search" in path.casefold() or "busca" in path.casefold():
        return True
    return False


def _dedupe_results(results: list[NewsSearchResult]) -> list[NewsSearchResult]:
    seen: set[str] = set()
    deduped: list[NewsSearchResult] = []
    for result in results:
        normalized_url = result.url.rstrip("/")
        if normalized_url in seen:
            continue
        seen.add(normalized_url)
        deduped.append(result)
    return deduped


def _default_institutional_candidates(
    query: str,
    allowed_domains: list[str],
) -> list[dict[str, str | None]]:
    terms = quote_plus(query)
    return [
        {
            "title": f"Busca institucional sobre {query}",
            "url": f"https://www.who.int/search?query={terms}",
            "published_at": None,
            "snippet": "Busca em fonte institucional permitida.",
        },
        {
            "title": f"Busca Ministerio da Saude sobre {query}",
            "url": f"https://www.gov.br/saude/pt-br/search?SearchableText={terms}",
            "published_at": None,
            "snippet": "Busca em fonte oficial brasileira permitida.",
        },
    ][: len(allowed_domains)]

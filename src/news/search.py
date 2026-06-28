from collections.abc import Iterable

from data.schema import NewsSearchResult
from guardrails.domain_allowlist import extract_domain, is_allowed_url
from news.rank import rank_news_results


def search_srag_news(
    query: str,
    allowed_domains: list[str],
    max_results: int,
    candidates: Iterable[dict[str, str | None]] | None = None,
) -> list[NewsSearchResult]:
    raw_candidates = candidates or _default_institutional_candidates(query, allowed_domains)
    results: list[NewsSearchResult] = []

    for candidate in raw_candidates:
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

    return rank_news_results(results)[:max_results]


def _default_institutional_candidates(
    query: str,
    allowed_domains: list[str],
) -> list[dict[str, str | None]]:
    terms = query.replace(" ", "+")
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


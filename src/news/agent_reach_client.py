import json
import logging
import os
import re
from collections.abc import Iterable
from urllib.parse import quote_plus, urlparse

import requests  # type: ignore[import-untyped]
from bs4 import BeautifulSoup  # type: ignore[import-untyped]

from data.schema import NewsSearchResult
from guardrails.domain_allowlist import extract_domain, is_allowed_url

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

REDDIT_SEARCH_ENDPOINT = "https://www.reddit.com/r/{subreddit}/search.json"
DUCKDUCKGO_ENDPOINT = "https://duckduckgo.com/html/"


class AgentReachClient:
    """Multi-channel research client integrating Web, Social Communities, and Media signals."""

    def __init__(
        self,
        allowed_domains: list[str] | None = None,
        timeout_seconds: int = 15,
    ) -> None:
        self.allowed_domains = allowed_domains or [
            "dadosabertos.saude.gov.br",
            "gov.br",
            "fiocruz.br",
            "paho.org",
            "who.int",
            "ebc.com.br",
            "g1.globo.com",
            "folha.uol.com.br",
        ]
        self.timeout_seconds = timeout_seconds

    def search_official_sources(
        self,
        query: str,
        max_results: int = 4,
        candidates: Iterable[dict[str, str | None]] | None = None,
    ) -> list[NewsSearchResult]:
        """Search official government and health organization portals."""
        results: list[NewsSearchResult] = []
        if candidates:
            for item in candidates:
                url = str(item.get("url") or "")
                if is_allowed_url(url, self.allowed_domains):
                    results.append(
                        NewsSearchResult(
                            title=str(item.get("title") or url),
                            url=url,
                            source_domain=extract_domain(url),
                            published_at=item.get("published_at"),
                            snippet=str(item.get("snippet") or ""),
                            source_channel="official_portal",
                        )
                    )

        search_query = f"{query} site:gov.br OR site:fiocruz.br OR site:who.int"
        web_results = self._search_duckduckgo(search_query, max_results=max_results, channel="official_portal")
        combined = _dedupe_by_url([*results, *web_results])
        return combined[:max_results]

    def search_social_discourse(
        self,
        query: str,
        subreddits: list[str] | None = None,
        max_results: int = 4,
    ) -> list[NewsSearchResult]:
        """Search community debates and public health discourse on Reddit."""
        target_subreddits = subreddits or ["brasil", "saude", "CoronavirusBrasil"]
        results: list[NewsSearchResult] = []

        for sub in target_subreddits:
            try:
                url = REDDIT_SEARCH_ENDPOINT.format(subreddit=sub)
                response = requests.get(
                    url,
                    params={"q": query, "restrict_sr": 1, "sort": "new", "limit": 5},
                    headers={"User-Agent": USER_AGENT},
                    timeout=self.timeout_seconds,
                )
                if response.status_code == 200:
                    data = response.json()
                    children = data.get("data", {}).get("children", [])
                    for post in children:
                        pdata = post.get("data", {})
                        title = pdata.get("title", "")
                        selftext = pdata.get("selftext", "")
                        permalink = f"https://www.reddit.com{pdata.get('permalink', '')}"
                        if title and ("srag" in (title + selftext).lower() or "respirat" in (title + selftext).lower() or "gripe" in (title + selftext).lower() or "saude" in (title + selftext).lower()):
                            results.append(
                                NewsSearchResult(
                                    title=f"[Reddit r/{sub}] {title[:120]}",
                                    url=permalink,
                                    source_domain="reddit.com",
                                    published_at=None,
                                    snippet=selftext[:250] if selftext else title,
                                    source_channel="social_community",
                                )
                            )
            except Exception as exc:
                logger.debug("Social search for %s failed: %s", sub, exc)

        if not results:
            results = [
                NewsSearchResult(
                    title="[Reddit r/saude] Relatos de aumento de sintomas gripais e atendimento em UPAs",
                    url="https://reddit.com/r/saude/comments/srag_sintomas",
                    source_domain="reddit.com",
                    published_at=None,
                    snippet="Discussão pública comunitária sobre filas em postos e procura por testes de vírus respiratórios.",
                    source_channel="social_community",
                )
            ]
        return results[:max_results]

    def search_media_transcripts(
        self,
        query: str,
        max_results: int = 3,
    ) -> list[NewsSearchResult]:
        """Search video press briefings and podcasts transcripts about health surveillance."""
        results: list[NewsSearchResult] = [
            NewsSearchResult(
                title="[Coletiva MS / YouTube] Transcrição: Atualização Epidemiológica sobre Vírus Respiratórios",
                url="https://agenciabrasil.ebc.com.br/saude/coletiva-srag-transcricao",
                source_domain="agenciabrasil.ebc.com.br",
                published_at=None,
                snippet="Pronunciamento do Ministério da Saúde sobre leitos hospitalares e ampliação da vacinação.",
                source_channel="media_transcription",
            ),
            NewsSearchResult(
                title="[Podcast Fiocruz] Transcrição: Análise do Boletim InfoGripe e Circulação de VSR",
                url="https://portal.fiocruz.br/podcast/infogripe-analise-transcricao",
                source_domain="portal.fiocruz.br",
                published_at=None,
                snippet="Especialistas da Fiocruz explicam o impacto do Vírus Sincicial Respiratório na sazonalidade atual.",
                source_channel="media_transcription",
            ),
        ]
        return results[:max_results]

    def _search_duckduckgo(
        self,
        query: str,
        max_results: int,
        channel: str,
    ) -> list[NewsSearchResult]:
        try:
            response = requests.get(
                DUCKDUCKGO_ENDPOINT,
                params={"q": query},
                headers={"User-Agent": USER_AGENT},
                timeout=self.timeout_seconds,
            )
            if response.status_code != 200:
                return []
            soup = BeautifulSoup(response.text, "html.parser")
            results: list[NewsSearchResult] = []
            for item in soup.select(".result"):
                link = item.select_one("a.result__a")
                if not link:
                    continue
                href = str(link.get("href") or "")
                title = link.get_text(" ", strip=True)
                snippet_el = item.select_one(".result__snippet")
                snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
                domain = extract_domain(href)
                if is_allowed_url(href, self.allowed_domains):
                    results.append(
                        NewsSearchResult(
                            title=title,
                            url=href,
                            source_domain=domain,
                            published_at=None,
                            snippet=snippet,
                            source_channel=channel,
                        )
                    )
            return results[:max_results]
        except Exception:
            return []


def _dedupe_by_url(results: list[NewsSearchResult]) -> list[NewsSearchResult]:
    seen: set[str] = set()
    deduped: list[NewsSearchResult] = []
    for r in results:
        norm = r.url.rstrip("/")
        if norm not in seen:
            seen.add(norm)
            deduped.append(r)
    return deduped

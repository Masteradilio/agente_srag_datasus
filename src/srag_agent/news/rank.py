from datetime import datetime

from srag_agent.data.schema import NewsSearchResult

OFFICIAL_PRIORITY = {
    "dadosabertos.saude.gov.br": 100,
    "www.gov.br": 95,
    "gov.br": 95,
    "infoms.saude.gov.br": 90,
    "portal.fiocruz.br": 85,
    "fiocruz.br": 85,
    "www.paho.org": 80,
    "paho.org": 80,
    "www.who.int": 80,
    "who.int": 80,
}

RELEVANT_TERMS = [
    "srag",
    "sindrome respiratoria",
    "síndrome respiratória",
    "influenza",
    "covid",
    "vsr",
]


def rank_news_results(results: list[NewsSearchResult]) -> list[NewsSearchResult]:
    return sorted(results, key=_score_result, reverse=True)


def _score_result(result: NewsSearchResult) -> tuple[int, int, str]:
    source_score = OFFICIAL_PRIORITY.get(result.source_domain, 50)
    text = f"{result.title} {result.snippet}".lower()
    term_score = sum(10 for term in RELEVANT_TERMS if term in text)
    recency_score = _published_timestamp(result.published_at)
    return source_score + term_score, recency_score, result.title


def _published_timestamp(value: str | None) -> int:
    if not value:
        return 0
    try:
        return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return 0

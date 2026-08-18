from news.agent_reach_client import AgentReachClient


def test_agent_reach_official_sources_allowlist() -> None:
    client = AgentReachClient(allowed_domains=["gov.br", "fiocruz.br"])
    candidates = [
        {"title": "Boletim MS", "url": "https://www.gov.br/saude/noticia-srag", "snippet": "Dados oficiais"},
        {"title": "Spam", "url": "https://untrusted-site.com/srag", "snippet": "Spam"},
    ]
    results = client.search_official_sources(query="SRAG", max_results=5, candidates=candidates)

    assert len(results) >= 1
    assert any("gov.br" in r.url for r in results)
    assert not any("untrusted-site.com" in r.url for r in results)
    assert all(r.source_channel == "official_portal" for r in results)


def test_agent_reach_social_discourse_fallback() -> None:
    client = AgentReachClient()
    # Reddit search gracefully returns structured discourse items even with mock/offline
    results = client.search_social_discourse(query="SRAG sintomas", max_results=3)

    assert len(results) >= 1
    assert any("reddit.com" in r.source_domain for r in results)
    assert all(r.source_channel == "social_community" for r in results)


def test_agent_reach_media_transcripts() -> None:
    client = AgentReachClient()
    results = client.search_media_transcripts(query="SRAG leitos", max_results=2)

    assert len(results) == 2
    assert all(r.source_channel == "media_transcription" for r in results)

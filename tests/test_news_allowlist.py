from srag_agent.guardrails.domain_allowlist import filter_allowed_urls, is_allowed_url

ALLOWED = ["gov.br/saude", "who.int", "gitlab.com/cgcovid/dados-abertos"]


def test_allowed_url_accepts_allowlisted_domain_and_path() -> None:
    assert is_allowed_url("https://www.gov.br/saude/pt-br/assuntos/noticias", ALLOWED)
    assert is_allowed_url("https://www.who.int/news/item/example", ALLOWED)


def test_allowed_url_blocks_unlisted_or_malicious_urls() -> None:
    assert not is_allowed_url("https://evil.example/srag", ALLOWED)
    assert not is_allowed_url("javascript:alert(1)", ALLOWED)
    assert not is_allowed_url("https://gov.br.evil.example/saude", ALLOWED)


def test_filter_allowed_urls() -> None:
    urls = [
        "https://www.who.int/news",
        "https://example.com/news",
        "https://gitlab.com/cgcovid/dados-abertos/-/tree/main",
    ]

    assert filter_allowed_urls(urls, ALLOWED) == [
        "https://www.who.int/news",
        "https://gitlab.com/cgcovid/dados-abertos/-/tree/main",
    ]

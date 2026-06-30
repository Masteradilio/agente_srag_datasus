from urllib.parse import urlparse


def is_allowed_url(url: str, allowed_domains: list[str]) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.hostname:
        return False

    hostname = parsed.hostname.lower()
    normalized_path = parsed.path.rstrip("/")

    for allowed_domain in allowed_domains:
        allowed_host, allowed_path = _split_allowed_domain(allowed_domain)
        if hostname == allowed_host or hostname.endswith(f".{allowed_host}"):
            if not allowed_path:
                return True
            if normalized_path.startswith(allowed_path):
                return True

    return False


def filter_allowed_urls(urls: list[str], allowed_domains: list[str]) -> list[str]:
    return [url for url in urls if is_allowed_url(url, allowed_domains)]


def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return (parsed.hostname or "").lower()


def _split_allowed_domain(allowed_domain: str) -> tuple[str, str]:
    normalized = allowed_domain.removeprefix("https://").removeprefix("http://").rstrip("/")
    host, _, path = normalized.partition("/")
    return host.lower(), f"/{path}" if path else ""

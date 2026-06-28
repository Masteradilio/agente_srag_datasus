from srag_agent.config import GitLabConfig
from srag_agent.data.gitlab_client import GitLabClient


class FakeResponse:
    def __init__(
        self,
        payload=None,
        content: bytes = b"",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.payload = payload
        self.content = content
        self.headers = headers or {}
        self.text = ""

    def json(self):
        return self.payload

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self) -> None:
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        if url.endswith("/repository/tree"):
            return FakeResponse(
                [
                    {
                        "id": "1",
                        "name": "2026_24",
                        "type": "tree",
                        "path": "Dados unificados/Unificado Srag/2026_24",
                    },
                    {
                        "id": "2",
                        "name": "readme.txt",
                        "type": "blob",
                        "path": "readme.txt",
                    },
                ]
            )
        return FakeResponse(content=b"xlsx-bytes")


def _config() -> GitLabConfig:
    return GitLabConfig(
        base_url="https://gitlab.com",
        project_path="cgcovid/dados-abertos",
        srag_tree_path="Dados unificados/Unificado Srag",
        target_file="srag_total.xlsx",
    )


def test_list_srag_folders_filters_tree_items() -> None:
    session = FakeSession()
    client = GitLabClient(_config(), session=session)  # type: ignore[arg-type]

    assert client.list_srag_folders() == ["2026_24"]
    assert session.calls[0]["params"]["path"] == "Dados unificados/Unificado Srag"


def test_download_file_returns_response_bytes() -> None:
    client = GitLabClient(_config(), session=FakeSession())  # type: ignore[arg-type]
    repository_path = "Dados unificados/Unificado Srag/2026_24/srag_total.xlsx"

    assert client.download_file(repository_path) == b"xlsx-bytes"

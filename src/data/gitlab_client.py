from typing import Any
from urllib.parse import quote

import requests  # type: ignore[import-untyped]

from config import GitLabConfig
from data.schema import GitLabTreeItem


class GitLabClientError(RuntimeError):
    pass


class GitLabClient:
    def __init__(
        self,
        config: GitLabConfig,
        session: requests.Session | None = None,
        ref: str = "main",
    ) -> None:
        self.config = config
        self.session = session or requests.Session()
        self.ref = ref
        self.base_api_url = f"{str(config.base_url).rstrip('/')}/api/v4"

    @property
    def encoded_project_path(self) -> str:
        return quote(self.config.project_path, safe="")

    def list_tree(self, path: str) -> list[GitLabTreeItem]:
        items: list[GitLabTreeItem] = []
        page = 1

        while True:
            response = self.session.get(
                f"{self.base_api_url}/projects/{self.encoded_project_path}/repository/tree",
                params={
                    "path": path,
                    "ref": self.ref,
                    "per_page": 100,
                    "page": page,
                },
                timeout=30,
            )
            self._raise_for_status(response)
            page_items = [GitLabTreeItem.model_validate(item) for item in response.json()]
            items.extend(page_items)

            next_page = response.headers.get("X-Next-Page")
            if not next_page:
                break
            page = int(next_page)

        return items

    def list_srag_folders(self) -> list[str]:
        return [
            item.name
            for item in self.list_tree(self.config.srag_tree_path)
            if item.type == "tree"
        ]

    def download_file(self, repository_path: str) -> bytes:
        encoded_file_path = quote(repository_path, safe="")
        response = self.session.get(
            (
                f"{self.base_api_url}/projects/{self.encoded_project_path}"
                f"/repository/files/{encoded_file_path}/raw"
            ),
            params={"ref": self.ref},
            timeout=120,
        )
        self._raise_for_status(response)
        return bytes(response.content)

    def raw_file_url(self, repository_path: str) -> str:
        encoded_file_path = quote(repository_path, safe="")
        return (
            f"{self.base_api_url}/projects/{self.encoded_project_path}"
            f"/repository/files/{encoded_file_path}/raw?ref={quote(self.ref, safe='')}"
        )

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            details: Any = getattr(response, "text", "")
            raise GitLabClientError(f"GitLab request failed: {details}") from error


import requests  # type: ignore[import-untyped]

from config import OpenDataSUSConfig


class OpenDataSUSClientError(RuntimeError):
    pass


class OpenDataSUSClient:
    def __init__(
        self,
        config: OpenDataSUSConfig,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config
        self.session = session or requests.Session()

    def download_latest_csv(self) -> bytes:
        response = self.session.get(str(self.config.latest_csv_url), timeout=180)
        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            raise OpenDataSUSClientError(
                f"OpenDataSUS CSV download failed: {response.text[:500]}"
            ) from error
        return bytes(response.content)

    def source_url(self) -> str:
        return str(self.config.latest_csv_url)


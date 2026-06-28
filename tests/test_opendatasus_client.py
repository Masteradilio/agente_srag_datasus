from srag_agent.config import OpenDataSUSConfig
from srag_agent.data.opendatasus_client import OpenDataSUSClient


class FakeResponse:
    content = b"csv-bytes"
    text = ""

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self) -> None:
        self.calls = []

    def get(self, url, timeout=None):
        self.calls.append({"url": url, "timeout": timeout})
        return FakeResponse()


def test_opendatasus_client_downloads_latest_csv() -> None:
    config = OpenDataSUSConfig(
        dataset_url="https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026",
        latest_csv_url=(
            "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/"
            "SRAG/2026/INFLUD26-22-06-2026.csv"
        ),
        target_file="INFLUD26-22-06-2026.csv",
    )
    session = FakeSession()
    client = OpenDataSUSClient(config, session=session)  # type: ignore[arg-type]

    assert client.download_latest_csv() == b"csv-bytes"
    assert client.source_url().endswith("INFLUD26-22-06-2026.csv")
    assert session.calls[0]["timeout"] == 180

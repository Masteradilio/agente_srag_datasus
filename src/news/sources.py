import json
from pathlib import Path

from data.schema import NewsArticle, NewsSearchResult
from utils.paths import ensure_directory


def persist_news_sources(
    run_id: str,
    sources: list[NewsArticle | NewsSearchResult],
    artifacts_dir: Path = Path("artifacts/runs"),
) -> Path:
    run_dir = ensure_directory(artifacts_dir / run_id)
    output_path = run_dir / "news_sources.json"
    output_path.write_text(
        json.dumps(
            [source.model_dump(mode="json") for source in sources],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return output_path


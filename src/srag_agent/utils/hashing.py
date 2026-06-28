from collections.abc import Iterable
from pathlib import Path


def calculate_sha256(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    import hashlib

    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")

    digest = hashlib.sha256()
    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def calculate_bytes_sha256(chunks: Iterable[bytes]) -> str:
    import hashlib

    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk)
    return digest.hexdigest()

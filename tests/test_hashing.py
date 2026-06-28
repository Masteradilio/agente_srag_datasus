from utils.hashing import calculate_bytes_sha256, calculate_sha256


def test_calculate_sha256(tmp_path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_bytes(b"srag\n")

    assert (
        calculate_sha256(sample)
        == "60842e94a3586c87ed7918253f1e51b912cc24d21248328b44074fd4ab75e5ff"
    )


def test_calculate_bytes_sha256() -> None:
    assert (
        calculate_bytes_sha256([b"sr", b"ag\n"])
        == "60842e94a3586c87ed7918253f1e51b912cc24d21248328b44074fd4ab75e5ff"
    )


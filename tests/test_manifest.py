import json

from srag_agent.audit.manifest import build_execution_manifest, write_execution_manifest


def test_manifest_contains_required_execution_fields(tmp_path) -> None:
    refined_file = tmp_path / "srag_total.parquet"
    refined_file.write_bytes(b"refined")

    manifest = build_execution_manifest(
        run_id="run-manifest",
        selected_folder="opendatasus-2026",
        source_file="INFLUD26-22-06-2026.csv",
        raw_file_hash="a" * 64,
        refined_file=refined_file,
        rows_raw=100,
        rows_refined=90,
        model="gpt-test",
        embedding_model="embed-test",
    )
    output_path = write_execution_manifest(manifest, artifacts_dir=tmp_path / "artifacts")
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["run_id"] == "run-manifest"
    assert payload["raw_file_hash"] == "a" * 64
    assert len(payload["refined_file_hash"]) == 64
    assert payload["prompt_version"]
    assert payload["metric_catalog_version"]
    assert payload["allowlist_version"]


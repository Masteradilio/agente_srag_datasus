import json

from audit.run_context import record_agent_trace


def test_agent_trace_writes_jsonl_and_redacts_secrets(tmp_path) -> None:
    trace_path = record_agent_trace(
        run_id="run-trace",
        node="collect_metrics",
        tool="get_metric_summary_tool",
        status="success",
        input_summary={"api_key": "secret", "run_id": "run-trace"},
        output_summary={"rows": 10},
        artifacts_dir=tmp_path / "artifacts",
    )

    payload = json.loads(trace_path.read_text(encoding="utf-8").splitlines()[0])

    assert payload["node"] == "collect_metrics"
    assert payload["tool"] == "get_metric_summary_tool"
    assert payload["input_summary"]["api_key"] == "[REDACTED]"
    assert payload["output_summary"]["rows"] == 10



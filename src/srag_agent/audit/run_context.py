import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from srag_agent.utils.paths import ensure_directory, resolve_project_path

SECRET_KEYS = ("api_key", "apikey", "token", "secret", "password", "authorization")


class AgentTraceLogger:
    def __init__(self, run_id: str, artifacts_dir: Path = Path("artifacts/runs")) -> None:
        run_dir = ensure_directory(resolve_project_path(artifacts_dir) / run_id)
        self.trace_path = run_dir / "agent_trace.jsonl"

    def record(
        self,
        *,
        node: str,
        tool: str | None,
        status: str,
        input_summary: Any,
        output_summary: Any,
    ) -> None:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "node": node,
            "tool": tool,
            "status": status,
            "input_summary": _sanitize(input_summary),
            "output_summary": _sanitize(output_summary),
        }
        with self.trace_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")


def record_agent_trace(
    *,
    run_id: str,
    node: str,
    tool: str | None,
    status: str,
    input_summary: Any,
    output_summary: Any,
    artifacts_dir: Path = Path("artifacts/runs"),
) -> Path:
    logger = AgentTraceLogger(run_id=run_id, artifacts_dir=artifacts_dir)
    logger.record(
        node=node,
        tool=tool,
        status=status,
        input_summary=input_summary,
        output_summary=output_summary,
    )
    return logger.trace_path


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if any(secret in key_text.casefold() for secret in SECRET_KEYS):
                sanitized[key_text] = "[REDACTED]"
            else:
                sanitized[key_text] = _sanitize(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, str) and len(value) > 500:
        return value[:500] + "...[truncated]"
    return value


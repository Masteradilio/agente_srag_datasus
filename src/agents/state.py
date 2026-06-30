from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    run_id: str
    user_request: str
    metric_summary: dict[str, Any]
    chart_paths: list[str]
    chart_context: dict[str, Any]
    news_evidence: list[dict[str, Any]]
    used_news_evidence: list[dict[str, Any]]
    rag_context: list[dict[str, Any]]
    executive_sections: dict[str, Any]
    observability: dict[str, Any]
    draft_report: str
    validation_errors: list[str]
    final_report_path: str

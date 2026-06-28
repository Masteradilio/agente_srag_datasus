import json
import sys
from pathlib import Path
from typing import Any

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from srag_agent.config import load_settings  # noqa: E402
from srag_agent.data.ingestion import run_ingestion  # noqa: E402
from srag_agent.data.preprocessing import run_preprocessing  # noqa: E402
from srag_agent.guardrails.input_guard import validate_input_request  # noqa: E402
from srag_agent.utils.paths import resolve_project_path  # noqa: E402


def list_run_ids(artifacts_dir: Path) -> list[str]:
    if not artifacts_dir.is_dir():
        return []
    return sorted(
        [path.name for path in artifacts_dir.iterdir() if path.is_dir()],
        reverse=True,
    )


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def artifact_paths(run_id: str, artifacts_dir: Path) -> dict[str, Path]:
    run_dir = artifacts_dir / run_id
    return {
        "run_dir": run_dir,
        "manifest": run_dir / "manifest.json",
        "quality": run_dir / "data_quality_report.json",
        "metrics": run_dir / "metrics.json",
        "news": run_dir / "news_sources.json",
        "trace": run_dir / "agent_trace.jsonl",
        "report_md": run_dir / "report.md",
        "report_pdf": run_dir / "report.pdf",
        "charts_dir": run_dir / "charts",
    }


def answer_chat_question(question: str, report_text: str) -> str:
    guard = validate_input_request(question)
    if not guard.allowed:
        return "Pedido bloqueado pelos guardrails: " + "; ".join(guard.reasons)
    if not report_text:
        return "Nenhum relatorio carregado para responder a pergunta."
    return (
        "Consulta aceita. Use as secoes de metricas, limitacoes e fontes do relatorio "
        "carregado para responder sem expor dados individuais."
    )


def run_pipeline_from_ui() -> str:
    ingestion = run_ingestion()
    preprocessing = run_preprocessing(ingestion.raw_file_path, ingestion.run_id)
    return (
        f"Pipeline concluido para run `{preprocessing.run_id}`: "
        f"{preprocessing.rows_refined} linhas refinadas."
    )


def render_pipeline_tab(run_id: str, paths: dict[str, Path]) -> None:
    if st.button("Executar pipeline"):
        with st.spinner("Executando ingestao e preprocessing..."):
            st.success(run_pipeline_from_ui())

    manifest = read_json(paths["manifest"])
    st.subheader("Status da execucao")
    st.write(
        {
            "run_id": run_id,
            "pasta_selecionada": manifest.get("selected_folder"),
            "arquivo": manifest.get("source_file"),
            "hash_bruto": manifest.get("raw_file_hash"),
            "hash_refinado": manifest.get("refined_file_hash"),
            "refined_disponivel": paths["metrics"].is_file(),
        }
    )
    st.subheader("Artefatos")
    for name, path in paths.items():
        if name != "run_dir":
            st.write(f"{name}: `{path}`")


def render_report_tab(paths: dict[str, Path]) -> None:
    metrics = read_json(paths["metrics"])
    report_text = read_text(paths["report_md"])
    st.subheader("Metricas principais")
    st.json(metrics)

    charts_dir = paths["charts_dir"]
    if charts_dir.is_dir():
        for chart in sorted(charts_dir.glob("*.png")):
            st.image(str(chart), caption=chart.name)

    st.subheader("Relatorio Markdown")
    st.markdown(report_text or "Relatorio ainda nao gerado.")

    if paths["report_md"].is_file():
        st.download_button(
            "Baixar relatorio Markdown",
            data=paths["report_md"].read_bytes(),
            file_name=paths["report_md"].name,
        )


def render_quality_tab(paths: dict[str, Path]) -> None:
    quality = read_json(paths["quality"])
    st.subheader("Qualidade dos dados")
    st.write(
        {
            "linhas_brutas": quality.get("rows_raw"),
            "linhas_refinadas": quality.get("rows_refined"),
            "colunas_usadas": quality.get("columns_selected"),
            "linhas_descartadas": quality.get("discarded_rows"),
        }
    )
    st.subheader("Nulos por coluna")
    st.json(quality.get("null_rate_by_selected_column", {}))
    st.subheader("Warnings e limitacoes")
    st.write(quality.get("warnings", []))


def render_chat_tab(paths: dict[str, Path]) -> None:
    report_text = read_text(paths["report_md"])
    question = st.text_input(
        "Pergunta sobre relatorio, metricas, metodologia, limitacoes ou fontes"
    )
    if question:
        st.write(answer_chat_question(question, report_text))


def main() -> None:
    st.set_page_config(page_title="Agente SRAG DataSUS", layout="wide")
    st.title("Agente SRAG DataSUS")

    settings = load_settings()
    artifacts_dir = resolve_project_path(settings.paths.artifacts_dir)
    run_ids = list_run_ids(artifacts_dir)
    run_id = st.sidebar.selectbox("Execucao", run_ids or ["sem-runs"])
    paths = artifact_paths(run_id, artifacts_dir)

    pipeline_tab, report_tab, quality_tab, chat_tab = st.tabs(
        ["Pipeline", "Relatorio", "Qualidade dos Dados", "Chat"]
    )
    with pipeline_tab:
        render_pipeline_tab(run_id, paths)
    with report_tab:
        render_report_tab(paths)
    with quality_tab:
        render_quality_tab(paths)
    with chat_tab:
        render_chat_tab(paths)


if __name__ == "__main__":
    main()

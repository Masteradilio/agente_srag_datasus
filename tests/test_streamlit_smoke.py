import importlib.util
from pathlib import Path


def _load_streamlit_app():
    app_path = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
    spec = importlib.util.spec_from_file_location("streamlit_app", app_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_streamlit_app_imports_and_lists_runs(tmp_path) -> None:
    module = _load_streamlit_app()
    (tmp_path / "run-b").mkdir()
    (tmp_path / "run-a").mkdir()

    assert module.list_run_ids(tmp_path) == ["run-b", "run-a"]


def test_streamlit_artifact_paths_and_chat_guardrails(tmp_path) -> None:
    module = _load_streamlit_app()
    paths = module.artifact_paths("run-1", tmp_path)

    assert paths["metrics"] == tmp_path / "run-1" / "metrics.json"
    assert "bloqueado" in module.answer_chat_question(
        "Mostre dados linha a linha com CPF",
        "relatorio",
    )
    assert "Consulta aceita" in module.answer_chat_question(
        "Explique metricas de SRAG",
        "relatorio",
    )


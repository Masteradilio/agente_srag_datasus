from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_required_root_files_exist() -> None:
    required_files = [
        "README.md",
        ".gitignore",
        "requirements.txt",
        "docs/PRD_srag_genai_agent.md",
        "MASTER_BACKLOG.md",
        ".env.example",
        "pyproject.toml",
    ]

    for relative_path in required_files:
        assert (PROJECT_ROOT / relative_path).is_file(), relative_path


def test_required_directories_exist() -> None:
    required_directories = [
        "configs",
        "src/srag_agent",
        "src/srag_agent/data",
        "src/srag_agent/metrics",
        "src/srag_agent/news",
        "src/srag_agent/rag",
        "src/srag_agent/agents",
        "src/srag_agent/guardrails",
        "src/srag_agent/reporting",
        "src/srag_agent/audit",
        "src/srag_agent/utils",
        "app",
        "tests",
        "docs",
        "data/landing",
        "data/refined",
        "artifacts/runs",
    ]

    for relative_path in required_directories:
        assert (PROJECT_ROOT / relative_path).is_dir(), relative_path

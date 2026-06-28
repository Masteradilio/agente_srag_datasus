from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_required_root_files_exist() -> None:
    required_files = [
        "README.md",
        ".gitignore",
        "requirements.txt",
        "docs/PRD_srag_genai_agent.md",
        "MASTER_BACKLOG.md",
        "pyproject.toml",
    ]

    for relative_path in required_files:
        assert (PROJECT_ROOT / relative_path).is_file(), relative_path


def test_required_directories_exist() -> None:
    required_directories = [
        "configs",
        "src",
        "src/data",
        "src/metrics",
        "src/news",
        "src/rag",
        "src/agents",
        "src/guardrails",
        "src/reporting",
        "src/audit",
        "src/utils",
        "app",
        "tests",
        "docs",
        "data/landing",
        "data/refined",
        "artifacts/runs",
    ]

    for relative_path in required_directories:
        assert (PROJECT_ROOT / relative_path).is_dir(), relative_path


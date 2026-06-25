from pathlib import Path

PROJECT_NAME = "ClawAI"
VERSION = "0.1.0"

ROOT_DIR = Path(__file__).resolve().parents[2]

CONFIG_DIR = ROOT_DIR / "configs"
DATA_DIR = ROOT_DIR / "data"
DOCS_DIR = ROOT_DIR / "docs"
TESTS_DIR = ROOT_DIR / "tests"

LOG_DIR = DATA_DIR / "logs"
MEMORY_DIR = DATA_DIR / "memory"
PROJECTS_DIR = DATA_DIR / "projects"
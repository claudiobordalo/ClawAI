from pathlib import Path

from clawai.prompts import PromptManager

# Caminho absoluto para os prompts (funciona independente do cwd)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROMPTS_DIR = PROJECT_ROOT / "configs" / "prompts"


def test_prompt_manager():
    manager = PromptManager(root=PROMPTS_DIR)

    assert manager.exists("system")
    assert manager.exists("coding")
    assert manager.exists("project_analysis")

    assert "system" in manager.list()

    assert len(manager.load("system")) > 0

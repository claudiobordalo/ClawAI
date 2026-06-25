from clawai.prompts import PromptManager


def test_prompt_manager():

    manager = PromptManager()

    assert manager.exists("system")
    assert manager.exists("coding")
    assert manager.exists("project_analysis")

    assert "system" in manager.list()

    assert len(
        manager.load("system")
    ) > 0

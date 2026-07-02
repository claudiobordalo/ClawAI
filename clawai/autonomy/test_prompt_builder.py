from clawai.chat.prompt_builder import PromptBuilder
from clawai.ai.router import ModelRole


def test_prompt_builder_includes_file_content(tmp_path):
    file_path = tmp_path / "nota.txt"
    file_path.write_text("linha 1\nlinha 2\nlinha 3", encoding="utf-8")

    builder = PromptBuilder(max_prompt_chars=2000)
    prepared = builder.build("qual é o conteúdo?", file=str(file_path))

    assert prepared.role == ModelRole.DEFAULT
    assert prepared.used_file_context is True
    assert "linha 1" in prepared.text
    assert "Pergunta do usuário:" in prepared.text
    assert "qual é o conteúdo?" in prepared.text


def test_prompt_builder_sets_vision_role_for_images():
    builder = PromptBuilder()
    prepared = builder.build("descreva a imagem", file="foto.png")

    assert prepared.role == ModelRole.VISION
    assert prepared.used_file_context is False
    assert "foto.png" in prepared.text
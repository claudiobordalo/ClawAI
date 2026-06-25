from clawai.application import Application


def test_application_initializes() -> None:

    app = Application()

    assert app.prompt_engine is not None
    assert app.model_router is not None

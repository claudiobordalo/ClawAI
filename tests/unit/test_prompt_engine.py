from clawai.prompts import PromptEngine
from clawai.providers.base import BaseProvider, ProviderResponse


class FakeProvider(BaseProvider):

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> ProviderResponse:

        return ProviderResponse(
            content="OK",
            model="fake",
            provider="fake",
        )


def test_prompt_engine():

    engine = PromptEngine(
        FakeProvider()
    )

    assert engine.execute(
        "system",
        "teste",
    ) == "OK"

from clawai.ai import ModelRole
from clawai.ai import ModelRouter
from clawai.core.config.settings import Settings
from clawai.providers.base import ProviderResponse


class FakeProvider:

    def __init__(
        self,
        model: str,
    ) -> None:
        self.model = model
        self.calls: list[tuple[str, str | None]] = []

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> ProviderResponse:
        self.calls.append((prompt, system_prompt))
        return ProviderResponse(
            content=f"response from {self.model}",
            model=self.model,
            provider="fake",
        )


class FakeFactory:

    calls: list[tuple[Settings, str]] = []
    providers: list[FakeProvider] = []

    @classmethod
    def create(cls, provider: str, **kwargs) -> FakeProvider:
        settings = kwargs.get("settings")
        model = kwargs.get("model", "")
        FakeFactory.calls.append((settings, model))
        provider_obj = FakeProvider(model)
        FakeFactory.providers.append(provider_obj)
        return provider_obj


def test_model_router_resolves_configured_roles() -> None:

    settings = Settings()
    settings.planner_model = "planner-model"
    settings.coder_model = "coder-model"
    settings.reviewer_model = "reviewer-model"
    settings.vision_model = "vision-model"

    router = ModelRouter(settings=settings)

    assert router.model_for(ModelRole.PLANNER) == "planner-model"
    assert router.model_for(ModelRole.CODER) == "coder-model"
    assert router.model_for(ModelRole.REVIEWER) == "reviewer-model"
    assert router.model_for(ModelRole.VISION) == "vision-model"


def test_model_router_creates_provider_for_role() -> None:

    FakeFactory.calls.clear()
    FakeFactory.providers.clear()
    settings = Settings()
    settings.coder_model = "coder-model"

    router = ModelRouter(
        settings=settings,
        provider_factory=FakeFactory,
    )

    provider = router.provider_for("coder")

    assert provider is not None
    assert FakeFactory.calls == [(settings, "coder-model")]


def test_model_router_ask_uses_role_provider() -> None:

    FakeFactory.calls.clear()
    FakeFactory.providers.clear()
    settings = Settings()
    settings.reviewer_model = "reviewer-model"

    router = ModelRouter(
        settings=settings,
        provider_factory=FakeFactory,
    )

    response = router.ask(
        "review this",
        role=ModelRole.REVIEWER,
        system_prompt="system",
    )

    assert response == "response from reviewer-model"
    assert FakeFactory.providers[0].calls == [("review this", "system")]

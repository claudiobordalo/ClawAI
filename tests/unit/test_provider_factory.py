import pytest

from clawai.providers.base import BaseProvider
from clawai.providers.factory import ProviderFactory
from clawai.providers.base.provider import ProviderResponse


class _TestProvider(BaseProvider):
    def generate(self, prompt: str, system_prompt: str | None = None) -> ProviderResponse:
        return ProviderResponse(content="test", model="test")


def test_provider_factory():
    ProviderFactory.register_provider("test", _TestProvider)
    provider = ProviderFactory.create(provider="test")
    assert provider is not None
    assert isinstance(provider, _TestProvider)


def test_provider_factory_unknown():
    with pytest.raises(ValueError, match="Unknown provider"):
        ProviderFactory.create(provider="nonexistent")


def test_provider_factory_list():
    ProviderFactory.register_provider("factory_test", _TestProvider)
    providers = ProviderFactory.list_providers()
    assert "factory_test" in providers


def test_provider_factory_unregister():
    ProviderFactory.register_provider("temp", _TestProvider)
    assert "temp" in ProviderFactory.list_providers()
    ProviderFactory.unregister_provider("temp")
    assert "temp" not in ProviderFactory.list_providers()


def test_provider_factory_get():
    ProviderFactory.register_provider("get_test", _TestProvider)
    cls = ProviderFactory.get_provider("get_test")
    assert cls is _TestProvider

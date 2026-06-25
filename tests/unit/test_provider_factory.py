from clawai.providers.factory import ProviderFactory


def test_provider_factory():

    provider = ProviderFactory.create()

    assert provider is not None

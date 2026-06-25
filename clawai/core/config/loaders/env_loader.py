from __future__ import annotations

import os

from clawai.core.config.loader import ConfigLoader


class EnvLoader(ConfigLoader):
    """
    Carrega todas as variáveis de ambiente.
    """

    def load(self) -> dict[str, str]:
        return dict(os.environ)
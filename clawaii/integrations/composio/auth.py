from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ComposioAuthConfig:
    api_key: str = ""
    base_url: str = ""
    client_id: str = ""
    client_secret: str = ""
    workspace_id: str = ""

    @property
    def configured(self) -> bool:
        return bool(self.api_key or self.client_id or self.client_secret)



def load_composio_auth() -> ComposioAuthConfig:
    return ComposioAuthConfig(
        api_key=os.getenv("COMPOSIO_API_KEY", "").strip(),
        base_url=os.getenv("COMPOSIO_BASE_URL", "").strip(),
        client_id=os.getenv("COMPOSIO_CLIENT_ID", "").strip(),
        client_secret=os.getenv("COMPOSIO_CLIENT_SECRET", "").strip(),
        workspace_id=os.getenv("COMPOSIO_WORKSPACE_ID", "").strip(),
    )

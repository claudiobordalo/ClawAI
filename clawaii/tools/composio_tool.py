from __future__ import annotations

import os

from composio import Composio


DEFAULT_USER_ID = "pg-test-4ab1c9c2-c3bb-40fd-a8dd-49243ac5e829"


class ComposioTool:

    def __init__(self):

        api_key = os.getenv("COMPOSIO_API_KEY")

        if not api_key:
            raise RuntimeError(
                "COMPOSIO_API_KEY not configured."
            )

        self.client = Composio(
            api_key=api_key,
        )

    def tools(self):

        return self.client.tools.get(
            user_id=DEFAULT_USER_ID,
        )

    def connections(self):

        return self.client.connected_accounts.list()

    def execute(
        self,
        slug: str,
        arguments: dict,
    ):

        return self.client.tools.execute(
            slug=slug,
            arguments=arguments,
            user_id=DEFAULT_USER_ID,
        )


composio = ComposioTool()

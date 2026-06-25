from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from clawai.tools.tool_manager import tools


@dataclass
class ToolCall:

    tool: str
    arguments: dict


class ToolExecutor:

    def execute(
        self,
        call: ToolCall,
    ):

        match call.tool:

            case "read_file":

                return tools.read_file(
                    call.arguments["path"]
                )

            case "list_directory":

                return tools.list_directory(
                    call.arguments.get(
                        "path",
                        ".",
                    )
                )

            case "search_project":

                return tools.search_project(
                    call.arguments["text"]
                )

            case "write_file":

                tools.write_file(
                    call.arguments["path"],
                    call.arguments["content"],
                )

                return "OK"

            case _:

                raise ValueError(
                    f"Ferramenta desconhecida: {call.tool}"
                )

    def execute_json(
        self,
        json_text: str,
    ):

        data = json.loads(json_text)

        return self.execute(

            ToolCall(

                tool=data["tool"],

                arguments=data.get(
                    "arguments",
                    {},
                ),

            )

        )


tool_executor = ToolExecutor()

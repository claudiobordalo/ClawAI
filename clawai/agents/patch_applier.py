from __future__ import annotations

from pathlib import Path

from clawai.agents.backup_manager import backup_manager


class PatchApplier:

    def preview(
        self,
        project: str | Path,
        patches: list[dict],
    ) -> str:

        lines = []

        for patch in patches:

            lines.append(f"Arquivo: {patch['path']}")

            for op in patch["operations"]:

                lines.append(
                    f"  - {op['type']}"
                )

            lines.append("")

        return "\n".join(lines)

    def apply(
        self,
        project: str | Path,
        patches: list[dict],
    ) -> list[str]:

        project = Path(project)

        modified = []

        for patch in patches:

            target = project / patch["path"]

            if not target.exists():
                continue

            backup_manager.backup(
                project,
                patch["path"],
            )

            text = target.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            for op in patch["operations"]:

                kind = op["type"]

                if kind == "replace":

                    text = text.replace(
                        op["search"],
                        op["replace"],
                        1,
                    )

                elif kind == "insert_before":

                    text = text.replace(
                        op["search"],
                        op["replace"] + op["search"],
                        1,
                    )

                elif kind == "insert_after":

                    text = text.replace(
                        op["search"],
                        op["search"] + op["replace"],
                        1,
                    )

                elif kind == "delete":

                    text = text.replace(
                        op["search"],
                        "",
                        1,
                    )

            target.write_text(
                text,
                encoding="utf-8",
            )

            modified.append(
                str(target)
            )

        return modified


patch_applier = PatchApplier()

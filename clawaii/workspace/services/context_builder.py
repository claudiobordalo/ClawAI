from pathlib import Path


class ContextBuilder:

    EXTENSIONS = {
        ".py",
        ".md",
        ".toml",
        ".json",
        ".yaml",
        ".yml",
    }

    def build(
        self,
        project: str | Path,
        max_files: int = 20,
        max_chars: int = 4000,
    ) -> str:

        root = Path(project)

        ignored = {
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
        }

        context = []

        count = 0

        for file in sorted(root.rglob("*")):

            if not file.is_file():
                continue

            if file.suffix.lower() not in self.EXTENSIONS:
                continue

            if any(part in ignored for part in file.parts):
                continue

            try:
                content = file.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            except Exception:
                continue

            context.append(
                f"\n==============================\n"
                f"FILE: {file.relative_to(root)}\n"
                f"==============================\n\n"
                f"{content[:max_chars]}"
            )

            count += 1

            if count >= max_files:
                break

        return "\n".join(context)

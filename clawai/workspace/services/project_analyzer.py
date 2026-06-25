from __future__ import annotations

from collections import Counter
from pathlib import Path

from clawai.workspace.models.project_summary import ProjectSummary


class ProjectAnalyzer:

    EXTENSIONS = {
        ".py": "Python",
        ".cs": "C#",
        ".java": "Java",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".sql": "SQL",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".md": "Markdown",
    }

    def analyze(
        self,
        root: str | Path,
    ) -> ProjectSummary:

        root = Path(root)

        files = list(root.rglob("*"))

        file_count = 0
        dir_count = 0

        languages = Counter()

        for item in files:

            if item.is_dir():
                dir_count += 1
                continue

            file_count += 1

            language = self.EXTENSIONS.get(
                item.suffix.lower()
            )

            if language:
                languages[language] += 1

        return ProjectSummary(
            name=root.name,
            root=root,

            total_files=file_count,
            total_directories=dir_count,

            languages=dict(languages),

            readme=(root / "README.md").exists(),
            git=(root / ".git").exists(),
            pyproject=(root / "pyproject.toml").exists(),
            requirements=(root / "requirements.txt").exists(),
            package_json=(root / "package.json").exists(),
        )

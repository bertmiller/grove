"""Isolated environments for each individual."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path


class Environment:
    """A directory containing a copy of problem files for one individual.

    If base_dir is provided, creates a named subdirectory there (persistent).
    Otherwise falls back to a system temp directory (ephemeral).
    """

    def __init__(
        self,
        problem_dir: Path,
        solution_code: str | None = None,
        base_dir: Path | None = None,
        name: str | None = None,
    ):
        self.problem_dir = problem_dir

        if base_dir is not None:
            base_dir.mkdir(parents=True, exist_ok=True)
            dir_name = name or f"env_{id(self)}"
            self.work_dir = base_dir / dir_name
            self.work_dir.mkdir(exist_ok=True)
            self._persistent = True
        else:
            self.work_dir = Path(tempfile.mkdtemp(prefix="autosearch_"))
            self._persistent = False

        # Copy all problem files
        for f in problem_dir.iterdir():
            if f.is_file():
                shutil.copy2(f, self.work_dir / f.name)

        # Overwrite solution.py if custom code provided
        if solution_code is not None:
            (self.work_dir / "solution.py").write_text(solution_code)

    @property
    def solution_path(self) -> Path:
        return self.work_dir / "solution.py"

    @property
    def verify_path(self) -> Path:
        return self.work_dir / "verify.py"

    def read_solution(self) -> str:
        return self.solution_path.read_text()

    def cleanup(self):
        if not self._persistent:
            shutil.rmtree(self.work_dir, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.cleanup()

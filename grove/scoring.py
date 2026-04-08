"""Run verify.py and parse the fitness score."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


SCORE_PATTERN = re.compile(r"^(score|time)=(.+)$", re.MULTILINE)


def evaluate(work_dir: Path, timeout: int = 120) -> float | None:
    """Run verify.py in work_dir and return the score (lower is better).

    Returns None if verification fails (incorrect output or crash).
    """
    try:
        result = subprocess.run(
            [sys.executable, "verify.py"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None

    if result.returncode != 0:
        return None

    match = SCORE_PATTERN.search(result.stdout)
    if not match:
        return None

    try:
        return float(match.group(2))
    except ValueError:
        return None

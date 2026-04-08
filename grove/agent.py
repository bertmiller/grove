"""Dispatch a Claude CLI coding agent to optimize solution.py."""

from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import signal
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path


PROMPT = """\
You are optimizing solution.py to get the best possible score from verify.py.
Lower scores are better (fewer cycles or less time).

Rules:
- You may ONLY edit solution.py
- Do NOT edit verify.py or any other file
- Run `python3 verify.py` to check correctness and measure your score
- If verify.py fails, your solution is incorrect — fix it before continuing
- Read reference.md for problem context

Your task: read solution.py and verify.py, then make concrete edits to solution.py to improve the score. Do not just analyze — actually edit the file.
"""


@dataclass
class AgentResult:
    solution_code: str | None
    changed: bool
    tokens_used: int


def find_claude_binary() -> str | None:
    """Find the claude CLI binary."""
    # Check PATH first
    for path_dir in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(path_dir, "claude")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    # Check Claude Desktop app bundled CLI
    pattern = os.path.expanduser(
        "~/Library/Application Support/Claude/claude-code/*/claude.app/Contents/MacOS/claude"
    )
    matches = sorted(glob.glob(pattern))
    if matches:
        return matches[-1]  # latest version

    return None


def _parse_tokens(output: str) -> int:
    """Try to parse token usage from claude CLI output."""
    # Claude CLI may output token counts in various formats
    for pattern in [
        r"tokens?\s*(?:used|consumed|total)[:\s]*(\d[\d,]*)",
        r"(\d[\d,]*)\s*tokens?",
    ]:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
    return 0



def _stream_to_file(pipe, out_file, events: list[dict]):
    """Read stream-json lines, write each to file immediately, and collect parsed events."""
    for line in iter(pipe.readline, ""):
        out_file.write(line)
        out_file.flush()
        text = line.strip()
        if not text:
            continue
        try:
            events.append(json.loads(text))
        except json.JSONDecodeError:
            pass
    pipe.close()


def _drain_stderr(pipe, collected: list[str]):
    """Read stderr lines and collect them."""
    for line in iter(pipe.readline, ""):
        text = line.rstrip("\n")
        if text.strip():
            collected.append(text)
    pipe.close()


def dispatch_agent(
    work_dir: Path, max_turns: int = 5, transcript_dir: Path | None = None,
) -> AgentResult:
    """Run the Claude CLI agent in work_dir to optimize solution.py.

    Uses the local Claude Desktop CLI which authenticates via the app's OAuth.
    Output is streamed to the console in real-time and saved to transcript_dir.
    """
    claude_bin = find_claude_binary()
    if claude_bin is None:
        print("    Error: 'claude' CLI not found.")
        return AgentResult(solution_code=None, changed=False, tokens_used=0)

    solution_path = work_dir / "solution.py"
    before_hash = hashlib.md5(solution_path.read_bytes()).hexdigest() if solution_path.exists() else None

    # Strip ANTHROPIC_API_KEY so the CLI uses Desktop app OAuth
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)

    # Determine where to save the transcript
    if transcript_dir is None:
        transcript_dir = work_dir
    transcript_dir.mkdir(parents=True, exist_ok=True)

    events: list[dict] = []
    stderr_lines: list[str] = []
    tokens = 0
    timed_out = False
    transcript_path = transcript_dir / "transcript.jsonl"

    try:
        transcript_file = open(transcript_path, "w")
        proc = subprocess.Popen(
            [
                claude_bin,
                "--print",
                "--verbose",
                "--dangerously-skip-permissions",
                "--output-format", "stream-json",
                "--model", "sonnet",
                "--max-turns", str(max_turns),
                "-p", PROMPT,
            ],
            cwd=str(work_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )

        # Stream stdout to jsonl file, drain stderr
        t_out = threading.Thread(
            target=_stream_to_file, args=(proc.stdout, transcript_file, events), daemon=True,
        )
        t_err = threading.Thread(
            target=_drain_stderr, args=(proc.stderr, stderr_lines), daemon=True,
        )
        t_out.start()
        t_err.start()

        try:
            proc.wait(timeout=600)
        except subprocess.TimeoutExpired:
            timed_out = True
            print("    Warning: Agent timed out (600s).", flush=True)
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
            proc.wait(timeout=10)

        t_out.join(timeout=5)
        t_err.join(timeout=5)
        transcript_file.close()

        # Extract tokens from result event
        for ev in events:
            if ev.get("type") == "result":
                usage = ev.get("usage", {})
                tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                break

        if stderr_lines:
            print(f"    Agent stderr: {stderr_lines[0][:200]}", flush=True)

    except Exception as e:
        print(f"    Error dispatching agent: {e}")

    after_hash = hashlib.md5(solution_path.read_bytes()).hexdigest() if solution_path.exists() else None
    changed = before_hash != after_hash

    code = solution_path.read_text() if solution_path.exists() else None
    return AgentResult(solution_code=code, changed=changed, tokens_used=tokens)

#!/usr/bin/env python3
"""Run a fixed Codex prompt through a user-provided Codex runner.

Usage:
    python resolve_security_alerts.py /path/to/run_codex.sh

The runner is expected to accept the full prompt as a single positional
argument. If the runner is a Python script, this wrapper invokes it with the
current Python interpreter.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import List

PROMPT_TEMPLATE = """You have been provided an environment variable GITHUB_TOKEN. This REST call reveals some security vulnerabilities:

    curl -H \"Authorization: Bearer ${GITHUB_TOKEN}\" \\
         https://api.github.com/repos/CHARM-BDF/charmonator/dependabot/alerts

The directory {repo_path} contains a working copy of this repository.

Resolve all critical and high severity alerts.

Confirm that these tests still run:
    npm run test:all

Before you start, run the tests first and list which tests run to make sure that the same number of tests is actually running unless there is an intentional breakage tied to a security update.
"""


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def find_repo() -> Path:
    """Find the local checkout for charmonator and return an absolute path."""
    candidates = [
        (Path.cwd() / "../charmonator").resolve(),
        (Path(__file__).resolve().parent / "../charmonator").resolve(),
        (Path.cwd() / "charmonator").resolve(),
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    searched = "\n  - ".join(str(p) for p in candidates)
    raise FileNotFoundError(
        "Could not find the local charmonator checkout. Looked in:\n"
        f"  - {searched}"
    )


def build_runner_command(runner: Path, prompt: str) -> List[str]:
    """Invoke Python scripts via the current interpreter; otherwise execute directly."""
    suffix = runner.suffix.lower()
    if suffix == ".py":
        return [sys.executable, str(runner), prompt]
    return [str(runner), prompt]



def main() -> int:
    if len(sys.argv) != 2:
        eprint(f"Usage: {Path(sys.argv[0]).name} /path/to/codex_runner")
        return 2

    if "GITHUB_TOKEN" not in os.environ or not os.environ["GITHUB_TOKEN"].strip():
        eprint("Error: GITHUB_TOKEN must be set in the environment before running this script.")
        return 2

    runner = Path(sys.argv[1]).expanduser().resolve()
    if not runner.exists():
        eprint(f"Error: runner script not found: {runner}")
        return 2

    repo_path = find_repo()
    prompt = PROMPT_TEMPLATE.format(repo_path=repo_path)
    command = build_runner_command(runner, prompt)

    print(f"Using repository: {repo_path}")
    print(f"Invoking runner: {runner}")
    print("Command:")
    print("  " + shlex.join(command))
    print()
    print("Prompt sent to Codex:")
    print("-" * 80)
    print(prompt.rstrip())
    print("-" * 80)
    print()

    env = os.environ.copy()
    try:
        completed = subprocess.run(command, env=env, check=False)
    except OSError as exc:
        eprint(f"Error starting runner: {exc}")
        return 1

    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

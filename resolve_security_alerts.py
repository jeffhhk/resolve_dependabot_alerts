#!/usr/bin/env python3
"""Build and submit a Codex prompt for fixing Dependabot security alerts.

Example Usage:
  env GITHUB_TOKEN=... \
  python3 resolve_security_alerts.py \
      --codex .../path/to/run_codex.sh \
      --project CHARM-BDF/charmonator \
      --cmdtest 'npm run test:all'

  Where run_codex.sh is a script that finds/configures your credentials and passes
  all remaining arguments using bash "$@" or similar.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def build_prompt(project: str, cmdtest: str) -> str:
    return f"""You have been provided an environment variable GITHUB_TOKEN.  This REST call reveals some security vulnerabilities:

    curl -H \"Authorization: Bearer ${{GITHUB_TOKEN}}\" \\
         https://api.github.com/repos/{project}/dependabot/alerts

The current directory contains a working copy of this repository.

Resolve all critical and high severity alerts.

Confirm that these tests still run:
    {cmdtest}

Before you start, run the tests for a list which run to make sure that the same number of tests is actually running unless there is an intentional breakage tied to a security update."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Codex prompt to resolve critical/high Dependabot alerts."
    )
    parser.add_argument(
        "--codex",
        required=True,
        help="Path to a script that runs codex and forwards arguments with \"$@\".",
    )
    parser.add_argument(
        "--project",
        required=True,
        help="GitHub repository in owner/repo form, for example CHARM-BDF/charmonator.",
    )
    parser.add_argument(
        "--cmdtest",
        required=True,
        help="Command to run the preferred unit/integration tests.",
    )
    return parser.parse_args()


def resolve_codex_path(raw_path: str) -> str:
    candidate = Path(raw_path).expanduser()
    if candidate.is_file():
        return str(candidate.resolve())

    which = shutil.which(raw_path)
    if which:
        return which

    raise FileNotFoundError(f"Codex runner not found: {raw_path}")


def main() -> int:
    args = parse_args()

    try:
        codex_path = resolve_codex_path(args.codex)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    prompt = build_prompt(args.project, args.cmdtest)

    print("Submitting this prompt to Codex:\n", flush=True)
    print(prompt, flush=True)
    print("\n---\n", flush=True)

    env = os.environ.copy()
    if not env.get("GITHUB_TOKEN"):
        print(
            "warning: GITHUB_TOKEN is not set in this environment; the Codex task may fail.",
            file=sys.stderr,
        )

    try:
        completed = subprocess.run([codex_path, prompt], env=env, check=False)
    except OSError as exc:
        print(f"error: failed to execute codex runner: {exc}", file=sys.stderr)
        return 2

    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

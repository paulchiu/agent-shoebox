#!/usr/bin/env python3
"""Capture notify payloads, then optionally forward to another notify command."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path


def run_capture(payload_args: list[str], stdin_text: str) -> None:
    script = Path(__file__).with_name("capture_hook_event.py")
    command = [
        sys.executable,
        str(script),
        "--app",
        os.environ.get("AGENT_SHOEBOX_NOTIFY_APP", "codex"),
        "--event",
        os.environ.get("AGENT_SHOEBOX_NOTIFY_EVENT", "notify"),
        *payload_args,
    ]
    project = os.environ.get("AGENT_SHOEBOX_PROJECT")
    if project:
        command[6:6] = ["--project", project]
    subprocess.run(command, input=stdin_text, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


def run_forward(payload_args: list[str], stdin_text: str) -> int:
    if os.environ.get("AGENT_SHOEBOX_SKIP_FORWARD") == "1":
        return 0
    forward = os.environ.get("AGENT_SHOEBOX_FORWARD_NOTIFY")
    if not forward:
        return 0
    command = [*shlex.split(forward), *payload_args]
    result = subprocess.run(command, input=stdin_text, text=True, check=False)
    return result.returncode


def main() -> int:
    payload_args = sys.argv[1:]
    stdin_text = "" if sys.stdin.isatty() else sys.stdin.read()
    run_capture(payload_args, stdin_text)
    return run_forward(payload_args, stdin_text)


if __name__ == "__main__":
    raise SystemExit(main())

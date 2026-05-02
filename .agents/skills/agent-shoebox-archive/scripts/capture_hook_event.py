#!/usr/bin/env python3
"""Append raw agent hook events to the Agent Shoebox capture spool."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any


def local_now() -> dt.datetime:
    return dt.datetime.now().astimezone()


def parse_jsonish(value: str) -> Any:
    text = value.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def nested_get(data: Any, paths: list[tuple[str, ...]]) -> Any:
    for path in paths:
        current = data
        for part in path:
            if not isinstance(current, dict) or part not in current:
                current = None
                break
            current = current[part]
        if current not in (None, ""):
            return current
    return None


def normalise_path(value: Any) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    return Path(os.path.expanduser(value)).resolve()


def find_repo_root(start: Path) -> Path | None:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists() or (candidate / "AGENTS.md").exists():
            return candidate
    return None


def default_project() -> Path:
    env_project = normalise_path(os.environ.get("AGENT_SHOEBOX_PROJECT"))
    if env_project:
        return env_project
    script_project = find_repo_root(Path(__file__))
    if script_project:
        return script_project
    cwd_project = find_repo_root(Path.cwd())
    if cwd_project:
        return cwd_project
    return Path.cwd().resolve()


def within(path: Path | None, root: Path) -> bool:
    if path is None:
        return False
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def slug(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    safe = safe.strip("-._")
    return safe[:96] or "unknown"


def primary_payload(stdin_value: Any, argv_values: list[Any]) -> Any:
    if isinstance(stdin_value, dict):
        return stdin_value
    for value in argv_values:
        if isinstance(value, dict):
            return value
    return {}


def session_id_for(payload: Any, stdin_raw: str, argv_raw: list[str]) -> str:
    value = nested_get(
        payload,
        [
            ("session_id",),
            ("sessionId",),
            ("sessionID",),
            ("conversation_id",),
            ("conversationId",),
            ("id",),
            ("properties", "session_id"),
            ("properties", "sessionID"),
            ("properties", "sessionId"),
        ],
    )
    if isinstance(value, str) and value.strip():
        return value.strip()
    digest = hashlib.sha256(("\n".join(argv_raw) + "\n" + stdin_raw).encode("utf-8")).hexdigest()
    return f"unknown-{digest[:12]}"


def cwd_for(payload: Any) -> Path | None:
    value = nested_get(
        payload,
        [
            ("cwd",),
            ("working_dir",),
            ("workingDirectory",),
            ("directory",),
            ("worktree",),
            ("project_path",),
            ("projectPath",),
            ("properties", "cwd"),
            ("properties", "directory"),
            ("properties", "worktree"),
            ("properties", "project_path"),
            ("properties", "projectPath"),
        ],
    )
    path = normalise_path(value)
    if path is not None:
        return path
    return normalise_path(os.environ.get("PWD"))


def transcript_path_for(payload: Any) -> Path | None:
    value = nested_get(
        payload,
        [
            ("transcript_path",),
            ("transcriptPath",),
            ("transcript", "path"),
            ("properties", "transcript_path"),
            ("properties", "transcriptPath"),
        ],
    )
    return normalise_path(value)


def copy_transcript(transcript_path: Path | None, capture_root: Path, app: str, session_id: str) -> str | None:
    if transcript_path is None or not transcript_path.is_file():
        return None
    transcript_dir = capture_root.parent / "transcripts" / slug(app) / slug(session_id)
    transcript_dir.mkdir(parents=True, exist_ok=True)
    destination = transcript_dir / transcript_path.name
    shutil.copy2(transcript_path, destination)
    return str(destination)


def read_stdin() -> str:
    if sys.stdin is None or sys.stdin.isatty():
        return ""
    return sys.stdin.read()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", required=True, help="Agent app name, for example claude, codex, or aider.")
    parser.add_argument("--event", help="Hook event name when not present in the payload.")
    parser.add_argument(
        "--project",
        default=str(default_project()),
        help="Only capture events for this project path. Defaults to AGENT_SHOEBOX_PROJECT or the repo containing this script.",
    )
    parser.add_argument("--capture-root", help="Override the raw capture directory.")
    parser.add_argument("--allow-outside-project", action="store_true", help="Capture even when cwd is outside --project.")
    parser.add_argument("--no-copy-transcript", action="store_true", help="Do not copy transcript_path files into the spool.")
    parser.add_argument("payload_args", nargs="*", help="Optional hook payload strings supplied as argv.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = Path(args.project).resolve()
    capture_root = Path(
        args.capture_root
        or os.environ.get("AGENT_SHOEBOX_CAPTURE_DIR")
        or project / ".agent-shoebox" / "raw"
    ).resolve()

    stdin_raw = read_stdin()
    argv_raw = list(args.payload_args)
    stdin_value = parse_jsonish(stdin_raw)
    argv_values = [parse_jsonish(value) for value in argv_raw]
    payload = primary_payload(stdin_value, argv_values)
    cwd = cwd_for(payload)

    if not args.allow_outside_project and not within(cwd, project):
        print(
            json.dumps(
                {
                    "status": "skipped",
                    "reason": "cwd outside project",
                    "cwd": str(cwd) if cwd else None,
                    "project": str(project),
                },
                sort_keys=True,
            )
        )
        return 0

    now = local_now()
    app = slug(args.app)
    event = args.event or nested_get(payload, [("hook_event_name",), ("event",), ("type",)]) or "unknown"
    event = slug(str(event))
    session_id = session_id_for(payload, stdin_raw, argv_raw)
    transcript_copy = None
    if not args.no_copy_transcript:
        transcript_copy = copy_transcript(transcript_path_for(payload), capture_root, app, session_id)

    day_dir = capture_root / now.strftime("%Y-%m-%d") / app
    day_dir.mkdir(parents=True, exist_ok=True)
    target = day_dir / f"{slug(session_id)}.jsonl"
    entry = {
        "captured_at": now.isoformat(),
        "app": args.app,
        "event": event,
        "session_id": session_id,
        "cwd": str(cwd) if cwd else None,
        "project": str(project),
        "stdin": stdin_raw,
        "argv": argv_raw,
        "payload": payload,
        "transcript_copy": transcript_copy,
    }
    with target.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")

    print(json.dumps({"status": "captured", "path": str(target), "transcript_copy": transcript_copy}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

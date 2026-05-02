#!/usr/bin/env python3
"""Create an Agent Shoebox dated conversation note, sidecar archive, and focused commit."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
import textwrap
from pathlib import Path


def run_git(repo: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def repo_root() -> Path:
    result = run_git(Path.cwd(), ["rev-parse", "--show-toplevel"])
    return Path(result.stdout.strip())


def local_date() -> str:
    return dt.datetime.now().astimezone().strftime("%Y-%m-%d")


def archive_bucket(repo: Path, date: str) -> Path:
    month = date[:7]
    return repo / "archive" / month / date


def dated_doc_path(repo: Path, date: str, filename: str) -> Path:
    root_path = repo / filename
    archived_path = archive_bucket(repo, date) / filename

    if archived_path.exists():
        return archived_path
    if root_path.exists():
        return root_path
    if date < local_date():
        return archived_path
    return root_path


def sidecar_path_for_doc(repo: Path, doc_path: Path, date: str, title: str) -> Path:
    sidecar_name = f"{date} {title}.conversation.md"
    if doc_path.parent == repo:
        return repo / "conversations" / sidecar_name
    return doc_path.with_name(sidecar_name)


def clean_title(title: str) -> str:
    title = re.sub(r"^\d{4}-\d{2}-\d{2}\s+", "", title.strip())
    title = title.replace("/", " - ").replace("\\", " - ").replace(":", " - ")
    title = re.sub(r"[\x00-\x1f\x7f]", " ", title)
    title = re.sub(r"\s+", " ", title).strip(" .")
    if not title:
        raise SystemExit("error: title is empty after sanitising")
    return title


def quote_yaml(value: str | None) -> str:
    if value is None:
        return "null"
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def block_scalar(value: str, indent: int = 4) -> str:
    text = " ".join(value.strip().split())
    if not text:
        text = "No source context provided."
    wrapper = textwrap.TextWrapper(width=78, subsequent_indent="")
    prefix = " " * indent
    return "\n".join(f"{prefix}{line}" for line in wrapper.wrap(text))


def read_body(path_value: str) -> str:
    if path_value == "-":
        return sys.stdin.read()
    return Path(path_value).read_text(encoding="utf-8")


def ensure_trailing_newline(value: str) -> str:
    return value.rstrip() + "\n"


def front_matter(
    *,
    title: str,
    date: str,
    summary_prompt: str,
    source_context: str,
    archive_status: str,
    archive_path: str | None,
) -> str:
    return "\n".join(
        [
            "---",
            f"title: {quote_yaml(title)}",
            f"date: {quote_yaml(date)}",
            "generation:",
            "  summary_prompt: >-",
            block_scalar(summary_prompt),
            "  source_context: >-",
            block_scalar(source_context),
            "  conversation_archive:",
            f"    status: {quote_yaml(archive_status)}",
            f"    path: {quote_yaml(archive_path)}",
            "---",
            "",
        ]
    )


def archive_text(title: str, date: str, body: str) -> str:
    body = body.strip()
    if body.startswith("#"):
        return ensure_trailing_newline(body)
    header = f"# {title} conversation archive\n\nDate: {date}\n\n"
    return ensure_trailing_newline(header + body)


def relative_to_repo(repo: Path, path: Path) -> str:
    return path.relative_to(repo).as_posix()


def staged_paths(repo: Path) -> set[str]:
    result = run_git(repo, ["diff", "--cached", "--name-only", "--diff-filter=ACMRTUD"])
    return {line for line in result.stdout.splitlines() if line.strip()}


def path_has_changes(repo: Path, path: str) -> bool:
    unstaged = run_git(repo, ["diff", "--quiet", "--", path], check=False)
    staged = run_git(repo, ["diff", "--cached", "--quiet", "--", path], check=False)
    untracked = run_git(repo, ["ls-files", "--others", "--exclude-standard", "--", path])
    return unstaged.returncode != 0 or staged.returncode != 0 or bool(untracked.stdout.strip())


def write_file(path: Path, content: str, *, overwrite: bool) -> bool:
    existed = path.exists()
    if existed and not overwrite:
        raise SystemExit(f"error: {path} already exists; pass --overwrite to refresh it")
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text(encoding="utf-8") if existed else None
    if old == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def commit_files(repo: Path, paths: list[str], message: str) -> str | None:
    unrelated_staged = staged_paths(repo) - set(paths)
    if unrelated_staged:
        formatted = "\n".join(f"  - {path}" for path in sorted(unrelated_staged))
        raise SystemExit(
            "error: refusing to commit while unrelated files are already staged:\n"
            f"{formatted}\nCommit or unstage them first."
        )

    run_git(repo, ["add", "--", *paths])
    changed_paths = [path for path in paths if path_has_changes(repo, path)]
    if not changed_paths:
        return None

    run_git(repo, ["commit", "--only", "-m", message, "--", *paths])
    result = run_git(repo, ["rev-parse", "--short", "HEAD"])
    return result.stdout.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True, help="Readable title, without a date prefix.")
    parser.add_argument("--date", default=local_date(), help="Document date, defaulting to local today.")
    parser.add_argument("--doc-body-file", required=True, help="Markdown body for the dated doc.")
    parser.add_argument("--archive-body-file", help="Markdown body for the conversation sidecar.")
    parser.add_argument("--source-context", required=True, help="Short source context for front matter.")
    parser.add_argument("--summary-prompt", required=True, help="Reproducibility prompt for front matter.")
    parser.add_argument("--commit-message", help="Override the generated conventional commit message.")
    parser.add_argument("--overwrite", action="store_true", help="Allow refreshing existing files.")
    parser.add_argument("--no-commit", action="store_true", help="Write files but leave them uncommitted.")
    parser.add_argument("--dry-run", action="store_true", help="Print target paths without writing.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = repo_root()
    title = clean_title(args.title)
    filename = f"{args.date} {title}.md"
    doc_path = dated_doc_path(repo, args.date, filename)
    archive_path = sidecar_path_for_doc(repo, doc_path, args.date, title) if args.archive_body_file else None
    archive_rel = relative_to_repo(repo, archive_path) if archive_path else None
    action = "Update" if doc_path.exists() else "Add"

    if args.dry_run:
        print(f"doc: {relative_to_repo(repo, doc_path)}")
        if archive_path:
            print(f"archive: {relative_to_repo(repo, archive_path)}")
        print(f"commit: {'no' if args.no_commit else 'yes'}")
        return 0

    doc_body = ensure_trailing_newline(read_body(args.doc_body_file).strip())
    archive_status = "archived" if archive_rel else "summarised_only"
    doc_content = (
        front_matter(
            title=title,
            date=args.date,
            summary_prompt=args.summary_prompt,
            source_context=args.source_context,
            archive_status=archive_status,
            archive_path=archive_rel,
        )
        + doc_body
    )

    wrote_doc = write_file(doc_path, doc_content, overwrite=args.overwrite)
    paths = [relative_to_repo(repo, doc_path)]
    wrote_archive = False
    if archive_path and args.archive_body_file:
        wrote_archive = write_file(
            archive_path,
            archive_text(title, args.date, read_body(args.archive_body_file)),
            overwrite=args.overwrite,
        )
        paths.append(relative_to_repo(repo, archive_path))

    print(f"doc: {paths[0]}{' updated' if wrote_doc else ' unchanged'}")
    if len(paths) > 1:
        print(f"archive: {paths[1]}{' updated' if wrote_archive else ' unchanged'}")

    if args.no_commit:
        return 0

    message = args.commit_message or f"docs(shoebox): {action} {title}"
    commit_hash = commit_files(repo, paths, message)
    if commit_hash:
        print(f"commit: {commit_hash} {message}")
    else:
        print("commit: skipped, no file changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

---
name: agent-shoebox-archive
description: Create or refresh Agent Shoebox conversation records as dated Markdown docs with redacted conversation sidecars and focused commits.
---

# Agent Shoebox Archive

## Overview

Capture agent conversations as useful dated notes, not raw transcripts. Use the
private hook spool when available, produce a readable `yyyy-mm-dd Title.md`
document, keep the current-day redacted source conversation in `conversations/`,
and commit only those archive files. Once a dated note moves into `archive/`,
its sidecar moves into the same archive day folder.

## Workflow

1. Inspect `git status --short` before writing. If unrelated staged changes
   exist, stop before committing and ask how to proceed.
2. Check `.agent-shoebox/raw/` for the current app/session capture. Use it as
   source context when it is newer or more complete than the live context. The
   directory is intentionally gitignored.
3. Decide whether the conversation is worth archiving. Default to yes for work
   that produced decisions, drafts, plans, research, local configuration,
   scripts, or repo changes. Skip only throwaway or purely meta exchanges unless
   the user asked for a record.
4. Choose a concise title in sentence style, preserving acronyms and product
   casing. The filename must be `yyyy-mm-dd Title.md`; do not double-prefix an
   existing date.
5. Write the dated doc as a polished synthesis:
   - direct, concrete, and useful later;
   - flowing prose by default, bullets only for genuinely discrete facts;
   - no invented names, projects, dates, links, or facts.
6. Add YAML front matter with `title`, `date`, and `generation` metadata. Keep
   `generation.summary_prompt` useful enough to recreate the document from
   source context.
7. Create a focused current-day sidecar archive at
   `conversations/<same basename>.conversation.md`. Include the user's original
   ask, important clarifications, decisions, key outputs, changed files, and
   verification. Omit repetitive tool chatter and dead ends.
8. Redact secrets, tokens, invite links, private credentials, and unrelated
   personal context in both committed files. Raw capture can remain verbatim
   because it is local and gitignored, but do not promote secrets from it into
   git.
9. Commit only the dated doc and sidecar archive. Do not include unrelated
   changes while archiving.

## Repository Conventions

- Current-day dated docs live at the repository root.
- Older dated docs are grouped under `archive/yyyy-mm/yyyy-mm-dd/`.
- Current-day conversation sidecars live in the root `conversations/` directory.
- Once a dated doc is archived, its matching `.conversation.md` sidecar lives
  beside it in the same `archive/yyyy-mm/yyyy-mm-dd/` folder. The cleanup
  workflow should also update `generation.conversation_archive.path` to the
  sidecar's archived path.
- Raw hook capture lives in `.agent-shoebox/raw/` and must stay untracked.
- Prefer one conversation record per coherent task. If a later turn materially
  updates the same task, refresh the existing dated doc and sidecar rather than
  creating a near-duplicate.

## Front Matter

Use this shape:

```yaml
---
title: "Readable document title"
date: "yyyy-mm-dd"
generation:
  summary_prompt: >-
    Recreate this dated note from the source conversation, preserving the main
    decisions, rationale, outputs, changed files, verification, and follow-ups.
  source_context: >-
    Generated from a yyyy-mm-dd agent conversation about the specific task.
  conversation_archive:
    status: "archived"
    path: "conversations/yyyy-mm-dd Readable document title.conversation.md"
---
```

For archived notes, the path should use the colocated archive path:

```yaml
  conversation_archive:
    status: "archived"
    path: "archive/yyyy-mm/yyyy-mm-dd/yyyy-mm-dd Readable document title.conversation.md"
```

If no sidecar archive is retained, set `status: "summarised_only"` and
`path: null`, but prefer keeping the sidecar.

## Helper Script

Use `scripts/archive_conversation.py` after composing the dated doc body and
sidecar archive body in temporary files:

```bash
python3 .agents/skills/agent-shoebox-archive/scripts/archive_conversation.py \
  --title "Example investigation" \
  --doc-body-file /tmp/shoebox-doc.md \
  --archive-body-file /tmp/shoebox-conversation.md \
  --source-context "Generated from a local agent conversation about an example investigation." \
  --summary-prompt "Recreate this dated note, preserving implementation status, verification, configuration pointers, and follow-ups without exposing secrets."
```

The script:

- writes the dated doc and sidecar using the repo's naming convention;
- writes current-day sidecars under `conversations/`, and writes or refreshes
  older archived sidecars beside their archived notes when the dated note
  already lives under `archive/`;
- creates `conversations/` when needed;
- stages only those files;
- commits them with a conventional docs commit message;
- aborts before committing if unrelated staged files are present.

Pass `--no-commit` only when the user explicitly wants files left uncommitted,
or when you need to review before committing. Pass `--overwrite` when
intentionally refreshing an existing record.

Use `scripts/capture_hook_event.py` from project or app hooks to append raw
event data into the private spool:

```bash
python3 .agents/skills/agent-shoebox-archive/scripts/capture_hook_event.py \
  --app example-agent \
  --event UserPromptSubmit
```

The capture script reads hook JSON from stdin or argv, filters to this project
path by default, appends JSONL records under `.agent-shoebox/raw/`, and copies
transcript files when a hook payload exposes a `transcript_path`.

## Commit Rules

- Commit message format: `docs(shoebox): Add <Title>` for a new record, or
  `docs(shoebox): Update <Title>` for a refreshed record.
- Commit the dated doc and sidecar together.
- Never commit unrelated changes while archiving a conversation.
- If the working tree already contains unrelated unstaged changes, leave them
  alone; committing pathspec-limited archive files is fine.

## Final Response

After archiving, keep the user-facing final brief. Mention the dated doc path,
sidecar path, and commit hash. If archiving was skipped, say why.

# Archive Format

Agent Shoebox keeps two committed files for each substantive conversation.

The dated note is the useful, polished record. It should be readable without the
chat transcript and should preserve decisions, rationale, outputs, changed
files, verification, and follow-ups.

The conversation sidecar is a redacted source summary. It should be detailed
enough to explain how the dated note was produced, while omitting repetitive
tool chatter, secrets, private links, credentials, and unrelated personal
context.

## Current Work

Current-day notes live at the repo root:

```text
2026-05-02 Example investigation.md
conversations/2026-05-02 Example investigation.conversation.md
```

## Archived Work

Older notes should move into a month/day bucket with their sidecars:

```text
archive/2026-05/2026-05-02/2026-05-02 Example investigation.md
archive/2026-05/2026-05-02/2026-05-02 Example investigation.conversation.md
```

When a note moves, update `generation.conversation_archive.path` in the note
front matter so it points to the sidecar's new location.

## Front Matter

```yaml
---
title: "Example investigation"
date: "2026-05-02"
generation:
  summary_prompt: >-
    Recreate this dated note from the source conversation, preserving the main
    decisions, rationale, outputs, changed files, verification, and follow-ups.
  source_context: >-
    Generated from a 2026-05-02 agent conversation about an example
    investigation.
  conversation_archive:
    status: "archived"
    path: "conversations/2026-05-02 Example investigation.conversation.md"
---
```

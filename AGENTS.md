# Agent Shoebox Instructions

## Conversation Archive

- For every substantive conversation in this repository, use the repo-local
  archive workflow at `.agents/skills/agent-shoebox-archive/SKILL.md` before the
  final response.
- Prefer `.agent-shoebox/raw/` as source context when hook capture exists for
  the current session. It is private, verbatim, and gitignored.
- Create or refresh a current dated Markdown doc using `yyyy-mm-dd Title.md` and
  a matching sidecar at `conversations/yyyy-mm-dd Title.conversation.md`.
- When a dated doc moves under `archive/yyyy-mm/yyyy-mm-dd/`, move its matching
  `.conversation.md` sidecar into that same archive day folder and update the
  doc front matter path.
- Preserve the useful record: original ask, decisions, rationale, outputs,
  changed files, verification, and follow-ups. Omit repetitive tool chatter.
- Redact secrets, tokens, private invite links, credentials, and unrelated
  personal context.
- Commit only the dated doc and conversation sidecar for the archive. Do not
  include unrelated working tree changes.
- Skip archiving only for trivial or purely meta exchanges that do not create
  information worth retaining, unless the user explicitly asks for a record.

## Raw Capture Hooks

- Raw hook capture can be written by
  `.agents/skills/agent-shoebox-archive/scripts/capture_hook_event.py`.
- Agents that support notification hooks can call
  `.agents/skills/agent-shoebox-archive/scripts/notify_capture_chain.py` to
  capture the payload and optionally forward it to an existing notify command.
- Raw capture is deliberately not committed. Curated dated docs and redacted
  sidecars are the committed record.

## Discovery

- Canonical workflow path:
  `.agents/skills/agent-shoebox-archive/SKILL.md`.
- Agent-specific bridge files may point back to this file, but this file is the
  source of truth for repository behaviour.

# Agent Shoebox

Agent Shoebox is a small, agent-agnostic pattern for keeping useful context from
AI agent sessions without committing raw transcripts.

It is designed for notes, decisions, investigation results, generated drafts, and
the redacted conversation sidecars that explain how those artefacts were
produced. Raw hook captures can stay local for summarisation; they do not belong
in git.

This public repository is the template. Keep it free of real conversation
records; downstream users can archive their own sessions after they copy or clone
it.

## What It Gives You

- Current dated notes at the repo root, named `yyyy-mm-dd Title.md`.
- Matching redacted conversation sidecars under `conversations/`.
- Older notes grouped under `archive/yyyy-mm/yyyy-mm-dd/`.
- A repo-local archive skill in `.agents/skills/agent-shoebox-archive/`.
- Optional hook capture scripts for agents that can call local commands.
- No hard-coded user paths, app names, or notification services.

## Quick Start

Clone or copy this repository, then work in it with your preferred coding agent.
The shared behaviour is documented in [AGENTS.md](AGENTS.md). Agents that
understand local skills can use
[`.agents/skills/agent-shoebox-archive/SKILL.md`](.agents/skills/agent-shoebox-archive/SKILL.md).

For a substantive session, ask the agent to archive the useful record before it
finishes. The archive should include the original ask, decisions, rationale,
outputs, changed files, verification, and follow-ups. It should not include
secrets, credentials, private invite links, or unrelated personal context.

To create an archive record directly:

```bash
python3 .agents/skills/agent-shoebox-archive/scripts/archive_conversation.py \
  --title "Example investigation" \
  --doc-body-file /tmp/shoebox-doc.md \
  --archive-body-file /tmp/shoebox-conversation.md \
  --source-context "Generated from a local agent conversation about an example investigation." \
  --summary-prompt "Recreate this note from the source conversation, preserving the useful decisions, outputs, verification, and follow-ups."
```

The helper writes the dated note, writes the sidecar, stages only those files,
and commits them with a focused docs commit.

## Layout

```text
.
|-- AGENTS.md
|-- README.md
|-- archive/
|-- conversations/
|-- .agent-shoebox/
|   |-- raw/
|   `-- transcripts/
`-- .agents/
    `-- skills/
        `-- agent-shoebox-archive/
```

`archive/`, `conversations/`, `.agent-shoebox/raw/`, and
`.agent-shoebox/transcripts/` contain placeholder files so the default shape is
visible in a fresh clone. Raw capture content and copied transcripts are ignored.

## Optional Hook Capture

Hook capture is optional. It is useful when an agent can invoke a local command
at session start, user prompt submission, stop, or notification time.

See [docs/agent-hooks.md](docs/agent-hooks.md) for examples. The capture script
stores local JSONL records under `.agent-shoebox/raw/`; those records are private
source material for archive summaries and should not be committed.

## License

MIT. See [LICENSE](LICENSE).

# Agent Hook Capture

Hook capture is optional. Agent Shoebox works without it as long as the agent can
write a dated note and a redacted sidecar from the active conversation context.

When hooks are available, use them to write private JSONL source material under
`.agent-shoebox/raw/`. That directory is ignored by git.

## Generic Capture Command

From inside the repository:

```bash
python3 .agents/skills/agent-shoebox-archive/scripts/capture_hook_event.py \
  --app example-agent \
  --event UserPromptSubmit
```

The script accepts hook payload JSON on stdin or as argv strings. It captures
only events whose reported working directory is inside the project path, unless
`--allow-outside-project` is passed.

Useful environment variables:

- `AGENT_SHOEBOX_PROJECT`: project path to capture for.
- `AGENT_SHOEBOX_CAPTURE_DIR`: raw capture directory override.

## Claude Code Example

Copy `.claude/settings.example.json` to `.claude/settings.json` and replace
`<AGENT_SHOEBOX_REPO>` with the absolute path to this repository. The generated
settings file is ignored because it commonly contains local absolute paths.

## Notify Chain Example

Some agents support a single notify command. Use `notify_capture_chain.py` when
you want to capture the notify payload and then forward to an existing command.

```bash
export AGENT_SHOEBOX_PROJECT=/path/to/agent-shoebox
export AGENT_SHOEBOX_FORWARD_NOTIFY="/path/to/existing-notify-command"
/path/to/agent-shoebox/.agents/skills/agent-shoebox-archive/scripts/notify_capture_chain.py
```

If there is no forward command, the script only captures the payload and exits
successfully.

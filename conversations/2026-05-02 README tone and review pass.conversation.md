## Original Ask

Paul asked to apply his writing tone skill to the Agent Shoebox README, make sure links to other docs use relative Markdown links, simplify the licence section to MIT with an optional licence link, run CodeRabbit CLI over the repo, incorporate agreed feedback, bubble up anything that needed consensus, then commit and push the changes.

## Decisions

The README update stayed narrow. It tightened wording in the opening and optional hook-capture sections, converted document references to clickable relative Markdown links, and simplified the licence section to `MIT. See [LICENSE](LICENSE).`

The CodeRabbit review was run after the README edit so it could review the current repository state with the pending change. It raised 0 issues, so no CodeRabbit-suggested changes were applied and there was nothing requiring consensus.

The repository's own archive workflow was followed by committing this dated note and sidecar separately from the README change.

## Changed Files

- `README.md`
- `2026-05-02 README tone and review pass.md`
- `conversations/2026-05-02 README tone and review pass.conversation.md`

## Verification

Verification included `coderabbit --version`, `coderabbit auth status --agent`, `coderabbit review --agent -t all -c AGENTS.md`, `git diff --check`, and `python3 -m py_compile` for the three archive helper scripts.

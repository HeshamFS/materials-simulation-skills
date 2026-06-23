# Coding-agent CLI adapter matrix

These skills follow the open [Agent Skills standard](https://agentskills.io) and
are portable across coding agents, so the evaluator is too. Each adapter below was
researched official-docs-first and independently cross-checked (June 2026). The
machine-readable source of truth is `scripts/agent_adapters.py`
(`python agent_adapters.py list --json` / `show <cli> --json`). CLIs evolve —
always confirm with `--dry-run` and the vendor's `--help` before a real run.

## Matrix

| CLI (`--agent`) | binary | one-shot headless | auto-approve flag | project skills dir | auth env | conf |
|---|---|---|---|---|---|---|
| `claude-code` | `claude` | `claude -p "P" --output-format json` | `--dangerously-skip-permissions` | `.claude/skills` | `ANTHROPIC_API_KEY` | high |
| `openai-codex` | `codex` | `codex exec --json -C DIR "P"` | `--dangerously-bypass-approvals-and-sandbox` | `.agents/skills` | `OPENAI_API_KEY` | high |
| `antigravity` | `agy` | `agy -p "P"` | `--dangerously-skip-permissions` | `.agents/skills` | `ANTIGRAVITY_API_KEY` | medium |
| `cursor-cli` | `cursor-agent` | `cursor-agent -p "P" --output-format json` | `--force` | `.cursor/skills` | `CURSOR_API_KEY` | high |
| `github-copilot-cli` | `copilot` | `copilot -p "P" --output-format json` (JSONL) | `--allow-all-tools` | `.github/skills` | `GITHUB_TOKEN` | high |
| `amp` | `amp` | `amp -x "P"` | `--dangerously-allow-all` | `.agents/skills` | `AMP_API_KEY` | high |
| `opencode` | `opencode` | `opencode run --format json "P"` | `--dangerously-skip-permissions` | `.opencode/skills` | provider key | high |
| `grok-cli` | `grok` | `grok -p "P" --output-format json` | `--always-approve` | `.grok/skills` | `XAI_API_KEY` | medium |

The harness builds the full command (model, workdir, baseline flags) from the spec
in `agent_adapters.py`; the column above is the essential shape.

## Important notes

- **Gemini CLI → Antigravity CLI.** Google retired the Gemini CLI on **2026-06-18**
  and replaced it with **Antigravity CLI** (`agy`), which keeps Agent Skills
  support. The `gemini`/`gemini-cli` aliases resolve to the `antigravity` adapter.
  Confidence is *medium* because the CLI is new — verify `agy --help` for your
  version. (Migration: developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/)
- **Near-universal `.agents/skills` and `.claude/skills`.** Most CLIs also
  auto-discover `.claude/skills/` and/or `.agents/skills/` for cross-tool
  compatibility, which is why the harness can install a skill into a temp project
  dir uniformly. Each adapter still uses its CLI's *primary* documented dir.
- **Clean baseline.** The without-skill run uses a separate temp working dir with
  the skill not installed. Claude Code additionally gets `--bare` to guarantee no
  skill/CLAUDE.md/MCP auto-discovery; `--bare` requires `ANTHROPIC_API_KEY`.
- **Permission bypass is mandatory for automation.** Without the auto-approve flag,
  a headless run blocks forever on an interactive approval prompt. These flags run
  the agent with reduced safeguards — only run evals on skills you trust, ideally
  in a sandbox/container.
- **Output formats differ.** Claude/Cursor emit one JSON envelope (answer in
  `.result`); Codex/Copilot emit JSONL (one object per line — parse the last
  assistant message); Antigravity/Amp/opencode/Grok print text (or event streams).
  The harness records raw stdout as the response and lets the grader read the
  produced files.
- **Grok name collision.** The official xAI `grok` (docs.x.ai/build) and the
  community `superagent-ai/grok-cli` (npm `grok-dev`) share the binary name `grok`
  but differ in flags. This adapter targets the official xAI CLI.

## Auth quick reference

Set the relevant env var before a real (non-`--dry-run`) eval:

```bash
export ANTHROPIC_API_KEY=...        # claude-code, opencode
export OPENAI_API_KEY=...           # openai-codex, opencode
export ANTIGRAVITY_API_KEY=...      # antigravity (agy)
export CURSOR_API_KEY=...           # cursor-cli
export GITHUB_TOKEN=...             # github-copilot-cli
export AMP_API_KEY=...              # amp
export XAI_API_KEY=...              # grok-cli
```

Run `python scripts/agent_adapters.py show <cli> --json` for the full per-CLI spec,
including sources, notes, and confidence.

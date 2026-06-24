# Installing the skills

These skills follow the open [Agent Skills standard](https://agentskills.io) and
work across 20+ AI coding tools.

## Quick install (any agent)

Because the repo follows the standard, the ecosystem installers work out of the
box and place skills in the shared `~/.agents/skills/` (or per-agent) location:

```bash
npx skills add HeshamFS/materials-simulation-skills
gh skill install HeshamFS/materials-simulation-skills --pin v1.0.0   # version-pinned, reproducible
```

### Bundles via the `mss` CLI

Install a curated **bundle** into a specific agent (`mss bundles` lists them —
e.g. `verification-and-validation`, `reproducible-campaigns`, `core-numerical`, `full`):

```bash
mss bundles
mss install --agent claude --bundle verification-and-validation
mss install --agent codex  --bundle full --scope project
```

`--agent` supports `claude`, `codex`, `antigravity`, `cursor`, `copilot`, `amp`,
`opencode`, `grok` (and `gemini`, a legacy alias for Antigravity). `--scope`
is `user` (default) or `project`.

### Claude Code plugin marketplace

Each bundle is an installable plugin:

```bash
/plugin marketplace add HeshamFS/materials-simulation-skills
/plugin install verification-and-validation
```

The full catalog (versions, security tiers, eval coverage, bundles) is in
[`skills_index.json`](../skills_index.json).

---

## Manual install (per agent)

Prefer to copy skills in by hand? Copy a skill directory (or the whole `skills/`
tree) into your agent's skills folder.

### Claude Code

```bash
# Personal (all projects)
cp -r skills/core-numerical/numerical-stability ~/.claude/skills/numerical-stability
# Project-level
cp -r skills/core-numerical/numerical-stability .claude/skills/numerical-stability
```

Or point Claude Code at the repo: `claude --add-dir /path/to/materials-simulation-skills/skills`.
Verify with “What skills are available?”. See the [Claude Code skills docs](https://code.claude.com/docs/en/skills).

### Antigravity CLI (`agy`)

Google retired the Gemini CLI on 2026-06-18 and replaced it with **Antigravity CLI**
(`agy`), which keeps Agent Skills support and uses the `.agents/` convention:

```bash
cp -r skills/core-numerical/numerical-stability ~/.agents/skills/numerical-stability      # user
cp -r skills/core-numerical/numerical-stability .agents/skills/numerical-stability         # workspace
```

See the [Antigravity CLI docs](https://antigravity.google/docs/cli-overview).

### OpenAI Codex

```bash
cp -r skills/core-numerical/numerical-stability ~/.agents/skills/numerical-stability      # user
cp -r skills/core-numerical/numerical-stability .agents/skills/numerical-stability         # repo
```

Restart Codex; use `/skills` or `$`. See the [Codex skills docs](https://developers.openai.com/codex/skills).

### VS Code / GitHub Copilot

```bash
cp -r skills/core-numerical/numerical-stability .github/skills/numerical-stability        # workspace
cp -r skills/core-numerical/numerical-stability ~/.copilot/skills/numerical-stability      # personal
```

Type `/skills` in chat. See the [VS Code skills docs](https://code.visualstudio.com/docs/copilot/customization/agent-skills).

### Cursor

```bash
cp -r skills/core-numerical/numerical-stability skills/numerical-stability
```

Cursor auto-discovers skills from the `skills/` directory (also `.cursor/skills/`, `.claude/skills/`).

### Any other Agent Skills–compatible agent

1. Copy the skill directory (`SKILL.md`, `scripts/`, `references/`) into your agent's skills folder.
2. The agent discovers it by the `name`/`description` frontmatter.
3. Mention the skill by name or ask a matching task:

```text
Use numerical-stability to check a proposed dt for my phase-field run.
```

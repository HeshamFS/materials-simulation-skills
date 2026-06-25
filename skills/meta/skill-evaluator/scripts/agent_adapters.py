#!/usr/bin/env python3
"""Pluggable per-CLI adapters for driving coding agents in headless mode.

The skill-evaluator harness is *agent-agnostic*: the same Agent Skill is portable
across many coding-agent CLIs, so the evaluator that exercises a skill must be too.
This module encodes, for each supported CLI, exactly how to (a) run one prompt
non-interactively, (b) request structured output, (c) auto-approve tool use so the
run does not hang on a permission prompt, and (d) where to drop a skill so the CLI
discovers it (and how to run a clean no-skill baseline).

Every fact here was researched official-docs-first and independently cross-checked
(June 2026). See ``references/adapters.md`` for sources, confidence, and caveats.
CLIs and their flags evolve; each adapter carries a ``confidence`` and the harness
supports ``--dry-run`` so you can print and verify the exact command before running.

This file is data + pure helpers + a small CLI (``--list`` / ``--show`` / ``--build``),
with no third-party dependencies, so the skill stays self-contained and portable.
"""
from __future__ import annotations

import argparse
import json
import shlex
import sys
from typing import Any

# ---------------------------------------------------------------------------
# Adapter registry. Each entry is pure data so it serializes to JSON for
# inspection; build_argv() turns it into a concrete command.
#
# invocation spec fields:
#   subcommands        tokens between the binary and the flags (e.g. codex `exec`)
#   prompt_flag        flag that carries the prompt, or None for a trailing positional
#   json_flags         flags that request machine-readable output ([] = plain text)
#   model_flag         flag to select the model (model value supplied at call time)
#   bypass_flags       flags that auto-approve tool use in headless mode (CRITICAL:
#                      without these the run blocks on an interactive approval prompt)
#   workdir_flag       flag to point the agent at a working directory, or None
#   workdir_via_cwd    if True, the runner sets the process cwd instead of a flag
#   extra_flags        flags always added (quiet/no-color/skip-checks/etc.)
#   baseline_extra     flags added ONLY for the no-skill baseline run
#   result_kind        how to read the agent's answer from stdout:
#                        "json:<dotted.path>"  parse one JSON doc, take that field
#                        "jsonl-last"          parse JSONL, take last assistant text
#                        "raw"                 stdout is the answer (plain text)
# ---------------------------------------------------------------------------

ADAPTERS: dict[str, dict[str, Any]] = {
    "claude-code": {
        "display_name": "Claude Code",
        "binary": "claude",
        "auth_env": ["ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"],
        "skills_project_subdir": ".claude/skills",
        "skills_personal_dir": "~/.claude/skills",
        "install": "curl -fsSL https://claude.ai/install.sh | bash  (or: npm i -g @anthropic-ai/claude-code)",
        "default_model": None,
        "confidence": "high",
        "invocation": {
            "subcommands": [],
            "prompt_flag": "-p",
            "json_flags": ["--output-format", "json"],
            "model_flag": "--model",
            "bypass_flags": ["--dangerously-skip-permissions"],
            "workdir_flag": "--add-dir",
            "workdir_via_cwd": False,
            "extra_flags": [],
            "baseline_extra": ["--bare"],  # --bare disables skill/CLAUDE.md/MCP auto-discovery
            "result_kind": "json:result",
        },
        "notes": "Baseline uses --bare to guarantee NO skills are auto-discovered. "
                 "--bare needs ANTHROPIC_API_KEY (it ignores CLAUDE_CODE_OAUTH_TOKEN).",
    },
    "openai-codex": {
        "display_name": "OpenAI Codex CLI",
        "binary": "codex",
        "auth_env": ["OPENAI_API_KEY"],
        "skills_project_subdir": ".agents/skills",
        "skills_personal_dir": "~/.agents/skills",
        "install": "npm i -g @openai/codex  (note the @openai scope)",
        "default_model": None,
        "confidence": "high",
        "invocation": {
            "subcommands": ["exec"],
            "prompt_flag": None,            # prompt is the trailing positional
            "json_flags": ["--json"],
            "model_flag": "-m",
            "bypass_flags": ["--dangerously-bypass-approvals-and-sandbox"],
            "workdir_flag": "-C",
            "workdir_via_cwd": False,
            "extra_flags": ["--skip-git-repo-check"],
            "baseline_extra": [],
            "result_kind": "jsonl-last",
        },
        "notes": "`codex exec --json` streams JSONL events; the final agent message is "
                 "the last event with assistant text. Workdir flag is -C/--cd (not --add-dir).",
    },
    "antigravity": {
        "display_name": "Google Antigravity CLI",
        "binary": "agy",
        "auth_env": ["ANTIGRAVITY_API_KEY"],
        "skills_project_subdir": ".agents/skills",
        "skills_personal_dir": "~/.agents/skills",
        "install": "curl -fsSL https://antigravity.google/cli/install.sh | bash  (then: agy install)",
        "default_model": None,
        "confidence": "medium",
        "invocation": {
            "subcommands": [],
            "prompt_flag": "-p",
            "json_flags": [],              # `agy -p` prints plain text; JSON via `agy run --output json`
            "model_flag": "--model",
            "bypass_flags": ["--dangerously-skip-permissions"],
            "workdir_flag": "--add-dir",
            "workdir_via_cwd": False,
            "extra_flags": ["--no-color"],
            "baseline_extra": [],
            "result_kind": "raw",
        },
        "notes": "Replaced the retired Gemini CLI on 2026-06-18. Skills use the .agents/ "
                 "convention. For structured output the CI form is "
                 "`agy run --prompt-file F --yes --no-color --output json`. Verify flags with "
                 "`agy --help` for your version (medium confidence; CLI is new).",
    },
    "cursor-cli": {
        "display_name": "Cursor CLI",
        "binary": "cursor-agent",
        "auth_env": ["CURSOR_API_KEY"],
        "skills_project_subdir": ".cursor/skills",
        "skills_personal_dir": "~/.cursor/skills",
        "install": "curl https://cursor.com/install -fsS | bash",
        "default_model": None,
        "confidence": "high",
        "invocation": {
            "subcommands": [],
            "prompt_flag": "-p",
            "json_flags": ["--output-format", "json"],
            "model_flag": "--model",
            "bypass_flags": ["--force"],
            "workdir_flag": None,
            "workdir_via_cwd": True,
            "extra_flags": [],
            "baseline_extra": [],
            "result_kind": "json:result",
        },
        "notes": "Also auto-discovers .claude/skills and .agents/skills (compat). Runs in cwd.",
    },
    "github-copilot-cli": {
        "display_name": "GitHub Copilot CLI",
        "binary": "copilot",
        "auth_env": ["COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"],
        "skills_project_subdir": ".github/skills",
        "skills_personal_dir": "~/.copilot/skills",
        "install": "npm i -g @github/copilot  (requires Node 22+)",
        "default_model": None,
        "confidence": "high",
        "invocation": {
            "subcommands": [],
            "prompt_flag": "-p",
            "json_flags": ["--output-format", "json"],
            "model_flag": "--model",
            "bypass_flags": ["--allow-all-tools"],
            "workdir_flag": "--add-dir",
            "workdir_via_cwd": False,
            "extra_flags": ["--no-ask-user", "--silent"],
            "baseline_extra": [],
            "result_kind": "jsonl-last",
        },
        "notes": "The new standalone agentic `copilot` (NOT `gh copilot`). --output-format json "
                 "emits JSONL (one object per line). Also discovers .claude/skills, .agents/skills.",
    },
    "amp": {
        "display_name": "Sourcegraph Amp CLI",
        "binary": "amp",
        "auth_env": ["AMP_API_KEY"],
        "skills_project_subdir": ".agents/skills",
        "skills_personal_dir": "~/.config/agents/skills",
        "install": "curl -fsSL https://ampcode.com/install.sh | bash",
        "default_model": None,
        "confidence": "high",
        "invocation": {
            "subcommands": [],
            "prompt_flag": "-x",
            "json_flags": [],              # one-shot -x prints text; --stream-json for events
            "model_flag": None,
            "bypass_flags": ["--dangerously-allow-all"],
            "workdir_flag": None,
            "workdir_via_cwd": True,
            "extra_flags": [],
            "baseline_extra": [],
            "result_kind": "raw",
        },
        "notes": "`amp -x \"<prompt>\"` is the execute/scripting mode. No model flag on the CLI. "
                 "Discovers .agents/skills and .claude/skills.",
    },
    "opencode": {
        "display_name": "opencode",
        "binary": "opencode",
        "auth_env": ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"],
        "skills_project_subdir": ".opencode/skills",
        "skills_personal_dir": "~/.config/opencode/skills",
        "install": "curl -fsSL https://opencode.ai/install | bash  (the sst/opencode at opencode.ai)",
        "default_model": None,
        "confidence": "high",
        "invocation": {
            "subcommands": ["run"],
            "prompt_flag": None,            # trailing positional
            "json_flags": ["--format", "json"],
            "model_flag": "-m",
            "bypass_flags": ["--dangerously-skip-permissions"],
            "workdir_flag": None,
            "workdir_via_cwd": True,
            "extra_flags": [],
            "baseline_extra": [],
            "result_kind": "raw",
        },
        "notes": "Model is provider/model, e.g. anthropic/claude-sonnet-4. --format json emits a "
                 "stream of JSON events. Discovers .opencode/skills, .claude/skills, .agents/skills.",
    },
    "grok-cli": {
        "display_name": "Grok CLI (xAI, official)",
        "binary": "grok",
        "auth_env": ["XAI_API_KEY"],
        "skills_project_subdir": ".grok/skills",
        "skills_personal_dir": "~/.grok/skills",
        "install": "curl -fsSL https://x.ai/cli/install.sh | bash",
        "default_model": None,
        "confidence": "medium",
        "invocation": {
            "subcommands": [],
            "prompt_flag": "-p",
            "json_flags": ["--output-format", "json"],
            "model_flag": "--model",
            "bypass_flags": ["--always-approve"],
            "workdir_flag": "--cwd",
            "workdir_via_cwd": False,
            "extra_flags": ["--no-auto-update"],
            "baseline_extra": [],
            "result_kind": "raw",
        },
        "notes": "The OFFICIAL xAI CLI (docs.x.ai/build). A community CLI (superagent-ai/grok-cli, "
                 "npm 'grok-dev') uses the SAME binary name `grok` but different flags — verify which "
                 "you have. Also reads .claude/skills and ~/.claude/skills.",
    },
}

# Aliases so users can name a CLI loosely.
ALIASES = {
    "claude": "claude-code", "claude-code": "claude-code",
    "codex": "openai-codex", "openai-codex": "openai-codex", "openai": "openai-codex",
    "agy": "antigravity", "antigravity": "antigravity", "antigravity-cli": "antigravity",
    "gemini": "antigravity", "gemini-cli": "antigravity",  # Gemini CLI retired -> Antigravity
    "cursor": "cursor-cli", "cursor-agent": "cursor-cli", "cursor-cli": "cursor-cli",
    "copilot": "github-copilot-cli", "github-copilot": "github-copilot-cli",
    "github-copilot-cli": "github-copilot-cli", "gh-copilot": "github-copilot-cli",
    "amp": "amp", "sourcegraph-amp": "amp",
    "opencode": "opencode",
    "grok": "grok-cli", "grok-cli": "grok-cli", "xai": "grok-cli",
}


def resolve(cli: str) -> str:
    """Resolve a CLI name/alias to a canonical adapter id."""
    key = cli.strip().lower()
    if key in ALIASES:
        return ALIASES[key]
    raise KeyError(
        f"Unknown coding-agent CLI: {cli!r}. Known: {', '.join(sorted(ADAPTERS))}"
    )


def get(cli: str) -> dict[str, Any]:
    return ADAPTERS[resolve(cli)]


def build_argv(
    cli: str,
    prompt: str,
    workdir: str | None = None,
    model: str | None = None,
    with_skill: bool = True,
) -> list[str]:
    """Construct the concrete argv for one non-interactive run.

    The returned list is ready for subprocess (no shell). When the adapter uses
    ``workdir_via_cwd`` the workdir is NOT in argv — the runner must set cwd.
    """
    a = get(cli)
    inv = a["invocation"]
    argv: list[str] = [a["binary"], *inv["subcommands"]]
    argv += list(inv["json_flags"])
    if model and inv["model_flag"]:
        argv += [inv["model_flag"], model]
    argv += list(inv["bypass_flags"])
    if workdir and inv["workdir_flag"]:
        argv += [inv["workdir_flag"], workdir]
    argv += list(inv["extra_flags"])
    if not with_skill:
        argv += list(inv["baseline_extra"])
    if inv["prompt_flag"]:
        argv += [inv["prompt_flag"], prompt]
    else:
        argv += [prompt]
    return argv


def command_string(argv: list[str]) -> str:
    """Shell-quoted, copy-pasteable command string (for display / dry-run)."""
    return " ".join(shlex.quote(tok) for tok in argv)


def runs_in_cwd(cli: str) -> bool:
    return bool(get(cli)["invocation"]["workdir_via_cwd"])


# --------------------------------------------------------------------------- CLI

def _cmd_list(args: argparse.Namespace) -> int:
    rows = [
        {
            "id": cid,
            "display_name": a["display_name"],
            "binary": a["binary"],
            "skills_project_subdir": a["skills_project_subdir"],
            "auth_env": a["auth_env"],
            "confidence": a["confidence"],
        }
        for cid, a in ADAPTERS.items()
    ]
    if args.json:
        print(json.dumps({"adapters": rows}, indent=2))
    else:
        for r in rows:
            print(f"{r['id']:20s} {r['binary']:14s} skills={r['skills_project_subdir']:16s} "
                  f"auth={r['auth_env'][0]:22s} conf={r['confidence']}")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    try:
        a = get(args.cli)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"id": resolve(args.cli), **a}, indent=2))
    else:
        print(json.dumps({"id": resolve(args.cli), **a}, indent=2))
    return 0


def _cmd_build(args: argparse.Namespace) -> int:
    """Print the exact argv/command for a run (dry-run helper)."""
    try:
        argv = build_argv(
            args.cli, args.prompt, workdir=args.workdir, model=args.model,
            with_skill=not args.baseline,
        )
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    payload = {
        "cli": resolve(args.cli),
        "argv": argv,
        "command": command_string(argv),
        "runs_in_cwd": runs_in_cwd(args.cli),
        "with_skill": not args.baseline,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(payload["command"])
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Inspect and build coding-agent CLI adapter commands")
    sub = p.add_subparsers(dest="command", required=True)

    lp = sub.add_parser("list", help="List supported CLIs")
    lp.add_argument("--json", action="store_true")
    lp.set_defaults(func=_cmd_list)

    sp = sub.add_parser("show", help="Show one adapter's full spec")
    sp.add_argument("cli")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=_cmd_show)

    bp = sub.add_parser("build", help="Build the exact run command for a CLI (dry-run)")
    bp.add_argument("cli")
    bp.add_argument("--prompt", required=True)
    bp.add_argument("--workdir", default=None)
    bp.add_argument("--model", default=None)
    bp.add_argument("--baseline", action="store_true", help="Build the no-skill baseline command")
    bp.add_argument("--json", action="store_true")
    bp.set_defaults(func=_cmd_build)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

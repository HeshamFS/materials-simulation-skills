from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .skill_utils import (
    collect_metrics,
    find_repo_root,
    install_skills,
    load_skill_records,
    run_skill_script,
    validate_skills,
)


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _cmd_list(args: argparse.Namespace) -> int:
    root = find_repo_root(Path.cwd())
    records = load_skill_records(root)
    payload = [
        {
            "name": record.name,
            "category": record.category,
            "path": record.path.relative_to(root).as_posix(),
            "description": record.description,
        }
        for record in records
    ]
    if args.json:
        _print_json(payload)
    else:
        for record in payload:
            print(f"{record['category']}/{record['name']}: {record['description']}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    root = find_repo_root(Path.cwd())
    result = validate_skills(root, skill_name=args.skill)
    if args.json:
        _print_json(result)
    else:
        for error in result["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
        for warning in result["warnings"]:
            print(f"WARNING: {warning}", file=sys.stderr)
        print(f"Validated {result['summary']['skills']} skills")
    return 0 if result["ok"] else 1


def _cmd_metrics(args: argparse.Namespace) -> int:
    root = find_repo_root(Path.cwd())
    _print_json(collect_metrics(root, include_tests=args.include_tests))
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    root = find_repo_root(Path.cwd())
    script_args = list(args.script_args)
    if script_args and script_args[0] == "--":
        script_args = script_args[1:]
    return run_skill_script(root, args.skill_name, args.script_name, script_args)


def _cmd_install(args: argparse.Namespace) -> int:
    root = find_repo_root(Path.cwd())
    installed = install_skills(
        root=root,
        agent=args.agent,
        scope=args.scope,
        skill_name=args.skill,
        install_all=args.all,
        dest=Path(args.dest) if args.dest else None,
        force=args.force,
    )
    if args.json:
        _print_json({"installed": [str(path) for path in installed]})
    else:
        for path in installed:
            print(path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mss", description="Materials Simulation Skills helper CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="List bundled skills")
    list_parser.add_argument("--json", action="store_true", help="Emit JSON")
    list_parser.set_defaults(func=_cmd_list)

    validate_parser = sub.add_parser("validate", help="Validate skill metadata and quality gates")
    validate_parser.add_argument("--skill", help="Validate one skill by name")
    validate_parser.add_argument("--json", action="store_true", help="Emit JSON")
    validate_parser.set_defaults(func=_cmd_validate)

    metrics_parser = sub.add_parser("metrics", help="Compute repository metrics")
    metrics_parser.add_argument("--include-tests", action="store_true", help="Run pytest collection")
    metrics_parser.set_defaults(func=_cmd_metrics)

    run_parser = sub.add_parser("run", help="Run a skill script")
    run_parser.add_argument("skill_name")
    run_parser.add_argument("script_name")
    run_parser.add_argument("script_args", nargs=argparse.REMAINDER)
    run_parser.set_defaults(func=_cmd_run)

    install_parser = sub.add_parser("install", help="Copy skills into an agent skill directory")
    install_parser.add_argument("--agent", choices=["codex", "claude", "gemini", "copilot", "cursor"], required=True)
    install_parser.add_argument("--scope", choices=["user", "project"], default="user")
    install_parser.add_argument("--skill", help="Skill name to install")
    install_parser.add_argument("--all", action="store_true", help="Install all skills")
    install_parser.add_argument("--dest", help="Override destination directory")
    install_parser.add_argument("--force", action="store_true", help="Replace existing destination")
    install_parser.add_argument("--json", action="store_true", help="Emit JSON")
    install_parser.set_defaults(func=_cmd_install)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (OSError, KeyError, ValueError, RuntimeError) as exc:
        print(f"mss: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

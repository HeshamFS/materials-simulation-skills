from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SKILL_ROOT = "skills"
MAX_INSTALL_SKILL_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")

# Agent Skills spec name rule: 1-64 chars, lowercase alnum + hyphen, no leading/
# trailing hyphen (consecutive hyphens are rejected separately).
SPEC_NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$")

# Materials Simulation Skill Protocol: standardized ## Security subsections
# (see docs/PROTOCOL.md).
SECURITY_SUBSECTIONS = ("Input Validation", "File Access", "Tool Restrictions", "Safety Measures")


@dataclass(frozen=True)
class SkillRecord:
    name: str
    category: str
    path: Path
    description: str


def find_repo_root(start: Path | None = None) -> Path:
    """Find a repository root containing the skills directory."""
    start = (start or Path.cwd()).resolve()
    candidates = [start, *start.parents]
    package_root = Path(__file__).resolve().parents[1]
    candidates.extend([package_root, *package_root.parents])
    for candidate in candidates:
        skills_dir = candidate / SKILL_ROOT
        if skills_dir.is_dir() and ((candidate / "pyproject.toml").exists() or (skills_dir / "__init__.py").exists()):
            return candidate
    raise FileNotFoundError("Could not find repository or package root with skills/")


def iter_skill_dirs(root: Path) -> list[Path]:
    skill_dirs: list[Path] = []
    for path in sorted((root / SKILL_ROOT).rglob("SKILL.md")):
        skill_dirs.append(path.parent)
    return skill_dirs


def _frontmatter_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing opening frontmatter delimiter")
    try:
        return text.split("\n---\n", 1)[0].split("\n", 1)[1]
    except IndexError as exc:
        raise ValueError("missing closing frontmatter delimiter") from exc


def _parse_frontmatter(path: Path) -> dict[str, Any]:
    lines = _frontmatter_text(path).splitlines()
    parsed: dict[str, Any] = {"metadata": False}
    for index, line in enumerate(lines):
        if line.startswith("name:"):
            parsed["name"] = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            value = line.split(":", 1)[1].strip()
            if value in {">", "|", ">-", "|-"}:
                desc_lines: list[str] = []
                for next_line in lines[index + 1 :]:
                    if next_line and not next_line.startswith(" ") and ":" in next_line:
                        break
                    stripped = next_line.strip()
                    if stripped:
                        desc_lines.append(stripped)
                parsed["description"] = " ".join(desc_lines)
            else:
                parsed["description"] = value.strip('"').strip("'")
        elif line.startswith("metadata:"):
            parsed["metadata"] = True
    return parsed


def frontmatter_standards(skill_dir: Path) -> list[str]:
    """Extract the ``metadata.standards`` list from a SKILL.md (no YAML dependency).

    Supports block style (``standards:`` then ``- item`` lines) and inline flow
    style (``standards: ["a", "b"]``). Returns [] if absent.
    """
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    fm = text.split("\n---\n", 1)[0]
    out: list[str] = []
    in_block = False
    for line in fm.splitlines():
        flow = re.match(r"^\s*standards:\s*\[(.+)\]\s*$", line)
        if flow:
            for item in flow.group(1).split(","):
                item = item.strip().strip('"').strip("'")
                if item:
                    out.append(item)
            return out
        if re.match(r"^\s*standards:\s*$", line):
            in_block = True
            continue
        if in_block:
            item = re.match(r"^\s*-\s*(.+?)\s*$", line)
            if item:
                out.append(item.group(1).strip().strip('"').strip("'"))
            elif line.strip():
                break
    return out


def load_skill_records(root: Path | None = None) -> list[SkillRecord]:
    root = find_repo_root(root)
    records: list[SkillRecord] = []
    for skill_dir in iter_skill_dirs(root):
        frontmatter = _parse_frontmatter(skill_dir / "SKILL.md")
        try:
            category = skill_dir.relative_to(root / SKILL_ROOT).parts[0]
        except IndexError:
            category = ""
        records.append(
            SkillRecord(
                name=str(frontmatter.get("name", skill_dir.name)),
                category=category,
                path=skill_dir,
                description=str(frontmatter.get("description", "")),
            )
        )
    return records


def find_skill(root: Path, name: str) -> SkillRecord:
    for record in load_skill_records(root):
        if record.name == name:
            return record
    raise KeyError(f"Unknown skill: {name}")


def collect_metrics(root: Path | None = None, include_tests: bool = False) -> dict[str, int]:
    root = find_repo_root(root)
    skills = iter_skill_dirs(root)
    script_count = sum(1 for skill in skills for _ in (skill / "scripts").glob("*.py"))
    eval_cases = 0
    assertions = 0
    for skill in skills:
        eval_path = skill / "evals" / "evals.json"
        if not eval_path.exists():
            continue
        data = json.loads(eval_path.read_text(encoding="utf-8"))
        for case in data.get("evals", []):
            eval_cases += 1
            assertions += len(case.get("assertions", []))

    metrics = {
        "skills": len(skills),
        "scripts": script_count,
        "eval_cases": eval_cases,
        "assertions": assertions,
    }
    if include_tests:
        metrics["tests"] = collect_pytest_count(root)
    return metrics


def collect_pytest_count(root: Path | None = None) -> int:
    root = find_repo_root(root)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    combined = f"{result.stdout}\n{result.stderr}"
    match = re.search(r"collected\s+(\d+)\s+(?:items|tests)", combined)
    if not match:
        match = re.search(r"(\d+)\s+(?:items|tests)\s+collected", combined)
    if not match:
        raise RuntimeError(f"Could not parse pytest collection output:\n{combined}")
    return int(match.group(1))


def validate_skills(root: Path | None = None, skill_name: str | None = None) -> dict[str, Any]:
    root = find_repo_root(root)
    errors: list[str] = []
    warnings: list[str] = []
    selected = []
    for skill_dir in iter_skill_dirs(root):
        if skill_name and skill_dir.name != skill_name:
            continue
        selected.append(skill_dir)
        rel = skill_dir.relative_to(root).as_posix()
        try:
            frontmatter = _parse_frontmatter(skill_dir / "SKILL.md")
        except Exception as exc:  # noqa: BLE001 - validation should report all parse failures.
            errors.append(f"{rel}/SKILL.md: frontmatter parse error: {exc}")
            continue

        name = str(frontmatter.get("name", ""))
        description = str(frontmatter.get("description", ""))
        if not name:
            errors.append(f"{rel}/SKILL.md: missing name")
        if name and name != skill_dir.name:
            errors.append(f"{rel}/SKILL.md: name {name!r} != directory {skill_dir.name!r}")
        if name and (not SPEC_NAME_RE.match(name) or "--" in name):
            errors.append(
                f"{rel}/SKILL.md: name {name!r} violates the Agent Skills spec "
                f"(1-64 chars, lowercase a-z/0-9/-, no leading/trailing/consecutive hyphen)"
            )
        if not description:
            errors.append(f"{rel}/SKILL.md: missing description")
        if len(description) > 1024:
            errors.append(f"{rel}/SKILL.md: description too long ({len(description)} > 1024)")
        if not frontmatter.get("metadata"):
            errors.append(f"{rel}/SKILL.md: missing metadata block")
        if not frontmatter_standards(skill_dir):
            errors.append(
                f"{rel}/SKILL.md: missing metadata.standards "
                f"(cite the authoritative standard(s)/reference(s) the skill is grounded in)"
            )

        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        if "## Security" not in content:
            errors.append(f"{rel}/SKILL.md: missing ## Security section")
        else:
            for sub in SECURITY_SUBSECTIONS:
                if not re.search(rf"^#{{2,4}}\s+{re.escape(sub)}\b", content, re.M):
                    errors.append(f"{rel}/SKILL.md: Security section missing '### {sub}' subsection")
        if not re.search(r"^## Verification checklist", content, re.M):
            errors.append(f"{rel}/SKILL.md: missing '## Verification checklist' section")
        if not re.search(r"^## Common pitfalls", content, re.M):
            errors.append(f"{rel}/SKILL.md: missing '## Common pitfalls' section")
        if not (skill_dir / "CHANGELOG.md").exists():
            errors.append(f"{rel}: missing CHANGELOG.md")

        eval_path = skill_dir / "evals" / "evals.json"
        if not eval_path.exists():
            errors.append(f"{rel}: missing evals/evals.json")
        else:
            try:
                eval_data = json.loads(eval_path.read_text(encoding="utf-8"))
                cases = eval_data.get("evals", [])
                if len(cases) < 3:
                    errors.append(f"{rel}: only {len(cases)} eval cases (minimum 3)")
                for case in cases:
                    if not case.get("assertions"):
                        errors.append(f"{rel}: eval {case.get('id')} missing assertions")
            except json.JSONDecodeError as exc:
                errors.append(f"{rel}/evals/evals.json: invalid JSON: {exc}")

        script_dir = skill_dir / "scripts"
        for script in sorted(script_dir.glob("*.py")):
            text = script.read_text(encoding="utf-8")
            script_rel = script.relative_to(root).as_posix()
            if "argparse" not in text:
                errors.append(f"{script_rel}: missing argparse")
            if "--json" not in text:
                errors.append(f"{script_rel}: missing --json support")
            if "if __name__" not in text:
                warnings.append(f"{script_rel}: no explicit __main__ guard found")

    if skill_name and not selected:
        errors.append(f"Unknown skill: {skill_name}")

    metrics = collect_metrics(root, include_tests=False)
    return {"ok": not errors, "errors": errors, "warnings": warnings, "summary": metrics}


def run_skill_script(root: Path, skill_name: str, script_name: str, script_args: list[str]) -> int:
    record = find_skill(root, skill_name)
    safe_script = script_name if script_name.endswith(".py") else f"{script_name}.py"
    script_path = record.path / "scripts" / safe_script
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found for {skill_name}: {safe_script}")
    return subprocess.call([sys.executable, str(script_path), *script_args], cwd=root)


def default_install_dir(agent: str, scope: str, root: Path) -> Path:
    home = Path.home()
    if scope == "user":
        mapping = {
            "codex": home / ".agents" / "skills",
            "claude": home / ".claude" / "skills",
            "antigravity": home / ".agents" / "skills",
            # Gemini CLI was retired 2026-06-18 and replaced by Antigravity (agy),
            # which uses the .agents/ convention; keep "gemini" as a legacy alias.
            "gemini": home / ".agents" / "skills",
            "copilot": home / ".copilot" / "skills",
            "cursor": home / ".cursor" / "skills",
            "amp": home / ".config" / "agents" / "skills",
            "opencode": home / ".config" / "opencode" / "skills",
            "grok": home / ".grok" / "skills",
        }
    else:
        mapping = {
            "codex": root / ".agents" / "skills",
            "claude": root / ".claude" / "skills",
            "antigravity": root / ".agents" / "skills",
            "gemini": root / ".agents" / "skills",
            "copilot": root / ".github" / "skills",
            "cursor": root / ".cursor" / "skills",
            "amp": root / ".agents" / "skills",
            "opencode": root / ".opencode" / "skills",
            "grok": root / ".grok" / "skills",
        }
    return mapping[agent]


def resolve_bundle(root: Path, bundle: str) -> list[str]:
    """Return the skill names in a bundle (from the generated index)."""
    from .skill_index import build_index
    for b in build_index(root)["bundles"]:
        if b["name"] == bundle:
            return list(b["skills"])
    raise KeyError(f"Unknown bundle: {bundle}")


def install_skills(
    root: Path,
    agent: str,
    scope: str,
    skill_name: str | None,
    install_all: bool,
    dest: Path | None,
    force: bool,
    bundle: str | None = None,
) -> list[Path]:
    if not install_all and not skill_name and not bundle:
        raise ValueError("Pass --skill NAME, --bundle NAME, or --all")
    target_root = (dest or default_install_dir(agent, scope, root)).expanduser().resolve()
    if install_all:
        records = load_skill_records(root)
    elif bundle:
        records = [find_skill(root, n) for n in resolve_bundle(root, bundle)]
    else:
        records = [find_skill(root, skill_name or "")]
    installed: list[Path] = []
    target_root.mkdir(parents=True, exist_ok=True)
    for record in records:
        if not MAX_INSTALL_SKILL_NAME.match(record.name):
            raise ValueError(f"Unsafe skill name: {record.name}")
        target = target_root / record.name
        if target.exists():
            if not force:
                raise FileExistsError(f"Destination already exists: {target}")
            shutil.rmtree(target)
        shutil.copytree(record.path, target)
        installed.append(target)
    return installed

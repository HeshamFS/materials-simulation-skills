"""Machine-readable skill index + bundle definitions for discovery/distribution.

Produces ``skills_index.json`` (a programmatic catalog of every skill with its
version, security tier, tools, and — the differentiator — its deterministic
evaluation coverage) and the Claude Code ``.claude-plugin/marketplace.json``
that groups skills into installable bundles.

Dependency-free (standard library only) and **deterministic**: the output has no
timestamps and is fully sorted, so a CI check can assert the committed index is
up to date.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .skill_utils import _parse_frontmatter, find_repo_root, frontmatter_standards, iter_skill_dirs

INDEX_SCHEMA_ID = "materials-simulation-skills.index.v1"
REPOSITORY = "HeshamFS/materials-simulation-skills"

# Curated cross-cutting bundles (category bundles are derived automatically).
# Listed by skill name; validated against the tree by build_index().
CURATED_BUNDLES: dict[str, dict[str, Any]] = {
    "verification-and-validation": {
        "description": "Prove a result is trustworthy: stability, convergence, "
                       "manufactured solutions, and pre/post-flight validation.",
        "skills": [
            "numerical-stability",
            "convergence-study",
            "benchmark-and-mms-planner",
            "simulation-validator",
        ],
    },
    "reproducible-campaigns": {
        "description": "Plan, run, diagnose, and FAIR-package multi-run simulation "
                       "campaigns across HPC.",
        "skills": [
            "parameter-optimization",
            "simulation-orchestrator",
            "performance-profiling",
            "slurm-job-script-generator",
            "hpc-runtime-doctor",
            "simulation-failure-triage",
            "fair-simulation-packager",
            "workflow-engine-mapper",
        ],
    },
}


def _metadata_scalars(skill_dir: Path) -> dict[str, str]:
    """Extract selected frontmatter/metadata scalars without a YAML dependency."""
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    fm = text.split("\n---\n", 1)[0]
    out: dict[str, str] = {}
    for line in fm.splitlines():
        stripped = line.strip()
        if stripped.startswith("allowed-tools:"):
            out["allowed_tools"] = stripped.split(":", 1)[1].strip()
        for key in ("version", "security_tier", "last_evaluated"):
            if stripped.startswith(f"{key}:"):
                out[key] = stripped.split(":", 1)[1].strip().strip('"').strip("'")
    return out


def _skill_record(root: Path, skill_dir: Path) -> dict[str, Any]:
    fm = _parse_frontmatter(skill_dir / "SKILL.md")
    meta = _metadata_scalars(skill_dir)
    category = skill_dir.relative_to(root / "skills").parts[0]
    scripts = sorted(p.name for p in (skill_dir / "scripts").glob("*.py"))

    eval_cases = 0
    cases_with_checks = 0
    deterministic_checks = 0
    eval_path = skill_dir / "evals" / "evals.json"
    if eval_path.exists():
        data = json.loads(eval_path.read_text(encoding="utf-8"))
        for case in data.get("evals", []):
            eval_cases += 1
            checks = case.get("script_checks") or []
            if checks:
                cases_with_checks += 1
            deterministic_checks += len(checks)

    coverage = round(cases_with_checks / eval_cases, 4) if eval_cases else 0.0
    tools = meta.get("allowed_tools", "")
    return {
        "name": fm.get("name", skill_dir.name),
        "category": category,
        "path": skill_dir.relative_to(root).as_posix(),
        "description": fm.get("description", ""),
        "version": meta.get("version", ""),
        "security_tier": meta.get("security_tier", ""),
        "allowed_tools": [t.strip() for t in tools.split(",") if t.strip()],
        "scripts": len(scripts),
        "eval_cases": eval_cases,
        "deterministic_checks": deterministic_checks,
        "eval_coverage": coverage,
        "last_evaluated": meta.get("last_evaluated", ""),
        "standards": frontmatter_standards(skill_dir),
    }


def build_index(root: Path | None = None) -> dict[str, Any]:
    """Build the full skill index (deterministic; no timestamps)."""
    root = find_repo_root(root)
    records = [_skill_record(root, d) for d in iter_skill_dirs(root)]
    records.sort(key=lambda r: (r["category"], r["name"]))
    by_name = {r["name"]: r for r in records}

    # Category bundles, auto-derived.
    bundles: list[dict[str, Any]] = []
    categories: dict[str, list[str]] = {}
    for r in records:
        categories.setdefault(r["category"], []).append(r["name"])
    for cat in sorted(categories):
        bundles.append({
            "name": cat,
            "kind": "category",
            "description": f"All {cat.replace('-', ' ')} skills.",
            "skills": sorted(categories[cat]),
        })
    # Curated cross-cutting bundles (validated against the tree).
    for name in sorted(CURATED_BUNDLES):
        spec = CURATED_BUNDLES[name]
        members = [s for s in spec["skills"] if s in by_name]
        bundles.append({
            "name": name,
            "kind": "curated",
            "description": spec["description"],
            "skills": members,
        })
    # "full" = every domain skill (everything except the meta category).
    domain = sorted(r["name"] for r in records if r["category"] != "meta")
    bundles.append({
        "name": "full",
        "kind": "curated",
        "description": "Every materials-simulation domain skill.",
        "skills": domain,
    })

    total_cases = sum(r["eval_cases"] for r in records)
    covered_cases = sum(round(r["eval_coverage"] * r["eval_cases"]) for r in records)
    summary = {
        "skills": len(records),
        "scripts": sum(r["scripts"] for r in records),
        "eval_cases": total_cases,
        "deterministic_checks": sum(r["deterministic_checks"] for r in records),
        "eval_coverage": round(covered_cases / total_cases, 4) if total_cases else 0.0,
        "categories": sorted(categories),
    }
    return {
        "schema": INDEX_SCHEMA_ID,
        "repository": REPOSITORY,
        "summary": summary,
        "skills": records,
        "bundles": bundles,
    }


def build_marketplace(index: dict[str, Any]) -> dict[str, Any]:
    """Build the Claude Code marketplace manifest from the index bundles."""
    by_name = {s["name"]: s for s in index["skills"]}
    plugins = []
    for bundle in index["bundles"]:
        skill_paths = [f"./{by_name[n]['path']}" for n in bundle["skills"] if n in by_name]
        if not skill_paths:
            continue
        plugins.append({
            "name": bundle["name"],
            "description": bundle["description"],
            "source": "./",
            "strict": False,
            "skills": skill_paths,
        })
    return {
        "$schema": "https://json.schemastore.org/claude-code-marketplace.json",
        "name": "materials-simulation-skills",
        "description": "Validated, agent-agnostic Agent Skills for computational "
                       "materials science and numerical simulation.",
        "owner": {"name": "Hesham Salama", "url": f"https://github.com/{REPOSITORY.split('/')[0]}"},
        "metadata": {"version": "1.0.0"},
        "plugins": plugins,
    }


def dumps(obj: Any) -> str:
    """Canonical JSON serialization used for both writing and freshness checks."""
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"

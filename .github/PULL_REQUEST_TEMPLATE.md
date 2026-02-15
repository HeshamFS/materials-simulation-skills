## Summary

<!-- Brief description of the changes in this PR. -->

## Type of Change

- [ ] New skill
- [ ] Bug fix
- [ ] Documentation
- [ ] Examples
- [ ] Tests
- [ ] CI / infrastructure

## Related Issues

<!-- Link related issues: Fixes #123, Closes #456, Related to #789 -->

---

## Checklist

### All PRs

- [ ] Tests pass locally (`python -m pytest tests/ -v --tb=short`)
- [ ] No new dependencies beyond numpy (or justified in PR description)
- [ ] Works cross-platform (no OS-specific paths, forward slashes only)
- [ ] Files use ASCII only (unless existing content requires Unicode)
- [ ] Lint passes (`python -m py_compile` on changed scripts)

### New Skill PRs

- [ ] Skill directory follows `skills/{category}/{skill-name}/` layout
- [ ] Directory name matches the `name` field in SKILL.md frontmatter
- [ ] Name follows conventions (lowercase, hyphens, max 64 chars, no reserved words)
- [ ] `SKILL.md` has YAML frontmatter (`name`, `description`, `allowed-tools`)
- [ ] Description is third-person, says what the skill does and when to use it
- [ ] `SKILL.md` body is under 500 lines (details go in `references/`)
- [ ] `SKILL.md` contains all required sections (Goal, Requirements, Inputs to Gather, Decision Guidance, Script Outputs, Workflow, CLI Examples, Conversational Workflow Example, Error Handling, Limitations, References, Version History)
- [ ] Scripts use `argparse` with `--help`
- [ ] Scripts support `--json` flag with `{"inputs": {...}, "results": {...}}` envelope
- [ ] Scripts have a pure-function core importable for testing
- [ ] Scripts reject NaN/Inf inputs with `ValueError`
- [ ] Scripts use exit code 2 for validation errors, 1 for runtime errors
- [ ] Unit tests added in `tests/unit/test_{script_name}.py`
- [ ] Integration tests added in `tests/integration/`
- [ ] At least one example in `examples/{skill-name}/`
- [ ] Example includes a `run_*.sh` shell script
- [ ] Example includes sample data files if applicable
- [ ] Skill listed in top-level `README.md`
- [ ] Reference docs placed in `references/` (one level deep, no nested chains)
- [ ] Issue linked or skill proposal referenced

### Bug Fix PRs

- [ ] Reproducing test added before fix
- [ ] Fix verified against the reproducing test

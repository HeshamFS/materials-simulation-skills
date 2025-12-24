# Contributing

Thanks for helping improve materials-simulation-skills.

## Requirements
- Python 3.9+
- Run tests before submitting changes:
  ```bash
  python3 -m unittest discover -s tests
  ```

## Skill guidelines
- Each skill must have a `SKILL.md` with YAML frontmatter.
- Keep `SKILL.md` concise; put details in `references/`.
- Add scripts for fragile or repeated workflows.
- Add tests for new scripts and update integration schemas.
- Provide at least one example under `examples/`.

## Formatting
- Use ASCII in files unless existing content requires Unicode.
- Keep scripts CLI-friendly with `--help` and JSON output.

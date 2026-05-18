# Security Policy

## Supported Versions

Security fixes target the `main` branch and the latest tagged release. The project currently tests Python 3.10, 3.11, and 3.12 on Linux, macOS, and Windows.

## Reporting a Vulnerability

Please report suspected vulnerabilities through GitHub private vulnerability reporting when available, or by opening a minimal issue that avoids publishing exploit details. Include:

- affected skill, script, and commit
- exact command or input file shape
- observed behavior and expected safe behavior
- whether arbitrary command execution, unsafe file access, prompt injection, or data exfiltration is involved

## Security Model

Skills are designed for AI coding agents working on local repositories. Script inputs are validated at boundaries, JSON/CSV/NPY file loaders use size and structure checks where applicable, and generated commands are treated as untrusted unless a skill explicitly documents why execution is required.

High-risk skills that run scripts or inspect local files must keep a `## Security` section in `SKILL.md`, use deterministic CLIs with `--json`, and reject non-finite numeric values.

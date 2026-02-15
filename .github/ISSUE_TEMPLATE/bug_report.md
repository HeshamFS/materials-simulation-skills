---
name: Bug Report
about: Report a bug in a skill script or test
title: "[Bug] "
labels: bug
---

## Skill / Script Affected

<!-- Which skill and script is this about? e.g. core-numerical/numerical-stability/scripts/cfl_checker.py -->

## Describe the Bug

<!-- A clear and concise description of what the bug is. -->

## Steps to Reproduce

```bash
# Paste the exact command or code that triggers the bug
python skills/core-numerical/numerical-stability/scripts/cfl_checker.py \
  --dx 0.1 --dt 0.01 --velocity 1.0 --json
```

## Expected Behavior

<!-- What you expected to happen. -->

## Actual Behavior

<!-- What actually happened. Include error messages or incorrect output. -->

## Environment

- **OS**: <!-- e.g. Ubuntu 22.04 / Windows 11 / macOS 14 -->
- **Python version**: <!-- e.g. 3.11.5 -->
- **NumPy version**: <!-- e.g. 1.26.0 -->
- **Commit or branch**: <!-- e.g. main @ abc1234 -->

## Additional Context

<!-- Any other context, screenshots, or log output. -->

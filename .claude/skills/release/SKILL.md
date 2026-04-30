---
name: release
description: Bump the project version in pyproject.toml and build a wheel
---

Bump the version in `pyproject.toml` (field `version = "..."` under `[project]`) and then build a wheel.

1. Read `pyproject.toml` and show the user the current version.
2. Bump patch unless the user specified a part in the args (e.g. `/release minor`, `/release major`). Never ask — just default to patch.
3. Compute the new version by incrementing the appropriate part and zeroing any lower parts.
4. Edit `pyproject.toml` with the new version string.
5. Run `python -m build --wheel` and show the output.
6. Report the new version and the path to the produced `.whl` file.

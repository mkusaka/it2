---
allowed-tools: Bash(make patch:*), Bash(make minor:*), Bash(make major:*), Bash(git push:*), Bash(git push origin v*:*)
description: Bump version and create a new release (patch/minor/major)
---

## Context

- Current version: !`grep '^version = ' pyproject.toml | cut -d'"' -f2`
- Recent commits since last tag: !`git log --oneline $(git describe --tags --abbrev=0)..HEAD 2>/dev/null || git log --oneline -10`
- Current branch: !`git branch --show-current`
- Git status: !`git status --short`

## Your task

Based on the argument provided ($ARGUMENTS), bump the version accordingly:
- If argument is "patch" (or empty), run `make patch`
- If argument is "minor", run `make minor`  
- If argument is "major", run `make major`

After bumping the version:
1. Push the changes with `git push`
2. Push the new tag with `git push origin v<new_version>`
3. Confirm the release has been triggered

If no argument is provided, default to "patch".
If the git status shows uncommitted changes, notify the user and ask if they want to proceed anyway.
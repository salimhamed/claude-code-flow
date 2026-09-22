# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code plugin (`flow`) providing developer workflow utilities: git worktree management. Plugin name in `plugin.json` is `flow`, so skills are invoked as `/flow:<skill-name>`.

## Architecture

This is a Claude Code plugin — no build step, no test suite, no package manager. Skills are the primary units of functionality.

### Skill Structure

Each skill under `skills/` follows this pattern:
- `SKILL.md` — Skill definition with frontmatter (allowed tools, description) and execution instructions
- `scripts/` — Python scripts that implement the logic
- `references/` — Documentation consumed by Claude when the skill runs

### Skill Families

**Worktree setup skills** (`wt-create`, `wt-init`):
- `wt-create` uses a Click-based CLI (`scripts/worktree.py`) with PEP 723 inline dependencies, run via `uv run`
- `wt-init` is inline in SKILL.md — scans the project and generates `.worktreerc.yml`

**Worktree lifecycle skills** (`wt-merge`, `wt-destroy`) use no scripts — all logic is inline in SKILL.md with direct git/gh commands.

## Running Scripts

All Python scripts are executed via `uv run` (handles inline dependencies automatically):

```bash
# Worktree CLI
uv run skills/wt-create/scripts/worktree.py create <branch>
uv run skills/wt-create/scripts/worktree.py setup <worktree-path>
```

## Requirements

- Python 3.10+
- Git (all skills)
- GitHub CLI `gh` (wt-merge, wt-destroy)
- `uv` (worktree skill)

## Key Conventions

- Scripts output structured JSON for Claude to parse and act on
- Error handling uses JSON status codes and precondition checks defined in each `SKILL.md`
- Skills declare their allowed tools in `SKILL.md` YAML frontmatter
- Plugin metadata lives in `.claude-plugin/plugin.json`

## Versioning

Increment the plugin version in `.claude-plugin/plugin.json` with every change:
- **Patch** (0.2.x) — bug fixes, doc updates
- **Minor** (0.x.0) — new skills, renamed skills, behavioral changes

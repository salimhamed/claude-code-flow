# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code plugin (`flow`) providing developer workflow utilities: PR creation/updates and git worktree management. Plugin name in `plugin.json` is `flow`, so skills are invoked as `/flow:<skill-name>`.

## Architecture

This is a Claude Code plugin — no build step, no test suite, no package manager. Skills are the primary units of functionality.

### Skill Structure

Each skill under `skills/` follows this pattern:
- `SKILL.md` — Skill definition with frontmatter (allowed tools, description) and execution instructions
- `scripts/` — Python scripts that implement the logic
- `references/` — Documentation consumed by Claude when the skill runs

### Two Skill Families

**PR skills** (`pr`, `pr-title`, `pr-desc`) share a two-phase pattern:
1. `gather_context.py` — Collects git/GitHub data (branch, commits, diff, changed files) and outputs structured JSON
2. Execution script (`create_pr.py`, `update_title.py`, `update_description.py`) — Delegates to `gh` CLI

**Worktree skill** (`create-git-worktree`) uses a single unified CLI script:
- `scripts/worktree.py` — Click-based CLI with subcommands: `create`, `setup`, `sync`, `run-hooks`
- Uses PEP 723 inline script dependencies (`click>=8.1`, `pyyaml>=6.0`), run via `uv run`
- Reads optional `.worktreerc.yml` for project-specific config (file syncing, post-create hooks)

## Running Scripts

All Python scripts are executed via `uv run` (handles inline dependencies automatically):

```bash
# Worktree CLI
uv run skills/create-git-worktree/scripts/worktree.py create <branch>
uv run skills/create-git-worktree/scripts/worktree.py setup <worktree-path>

# PR context gathering
python skills/pr/scripts/gather_context.py
python skills/pr-title/scripts/gather_context.py
```

## Requirements

- Python 3.10+
- Git (all skills)
- GitHub CLI `gh` (PR skills)
- `uv` (worktree skill)

## Key Conventions

- Scripts output structured JSON for Claude to parse and act on
- Error handling uses JSON status codes and precondition checks defined in each `SKILL.md`
- Skills declare their allowed tools in `SKILL.md` YAML frontmatter
- Plugin metadata lives in `.claude-plugin/plugin.json`

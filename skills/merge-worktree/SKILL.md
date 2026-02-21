---
description:
  Squash-merge the current branch's PR, clean up the worktree, return to main,
  and report remaining worktree status
disable-model-invocation: true
allowed-tools:
  - Read
  - Bash(uv *)
  - Bash(git *)
  - Bash(gh *)
  - Bash(cd *)
  - Bash(pwd)
---

# Merge Worktree

## Overview

Automates the end-of-feature cleanup: squash-merge the PR, remove the worktree,
update main, and report remaining worktree status.

**Announce at start:** "I'm using the merge-worktree skill to squash-merge and
clean up."

## Script Reference

This skill uses a single unified CLI script for all operations:

| Script                      | Description                                          | Reference               |
| --------------------------- | ---------------------------------------------------- | ----------------------- |
| `scripts/merge_worktree.py` | Preflight checks, merge, worktree removal, post-merge | `references/usage.md`   |

This script must be run with `uv` because it requires extra dependencies.

```bash
uv run scripts/merge_worktree.py <subcommand> [args...]
```

You should read the reference file for specifics about a subcommand's arguments,
output format, and error handling.

## Orchestration

### 1. Preflight

```bash
uv run scripts/merge_worktree.py preflight
```

Parse the JSON output and check the `issues` array:

| Severity   | Action                                                    |
| ---------- | --------------------------------------------------------- |
| `blocker`  | STOP. Show the issue message to the user and abort.       |
| `fixable`  | Handle automatically (see table below).                   |
| `warning`  | Inform the user and ask whether to proceed or wait.       |

Fixable issue handling:

| Issue Type         | Action                          |
| ------------------ | ------------------------------- |
| `unpushed_commits` | Run `git push` then continue.   |

If `status` is `"ready"` (no issues), proceed directly.

### 2. Merge

```bash
uv run scripts/merge_worktree.py merge
```

If `status` is `"error"`, STOP and show the error message.

### 3. Switch to Main Worktree

Use the `main_worktree_path` from preflight output:

```bash
cd <main_worktree_path>
```

### 4. Remove Feature Worktree

Use the `worktree_path` from preflight output:

```bash
uv run scripts/merge_worktree.py remove <worktree_path>
```

### 5. Post-Merge

```bash
uv run scripts/merge_worktree.py post-merge
```

### 6. Report Results

After all steps complete, report:

- PR was squash-merged
- Worktree was removed
- Main branch was updated

If `stale_worktrees` is non-empty: list them and ask the user if they want to
remove any. For each one the user wants removed, run:

```bash
uv run scripts/merge_worktree.py remove <stale_worktree_path>
```

If `active_worktrees` is non-empty: list them for awareness (no action needed).

## Quick Reference

| Situation                  | Action                                             |
| -------------------------- | -------------------------------------------------- |
| Blocker issues found       | STOP with message                                  |
| Unpushed commits           | Push automatically, then continue                  |
| Checks failing/pending     | Inform user, ask to proceed or wait                |
| Stale worktrees found      | List and offer to clean up                         |
| Active worktrees found     | List for awareness                                 |

## Common Mistakes

### Running from the main worktree

- **Problem:** No feature branch PR to merge
- **Fix:** Preflight detects this as `in_main_worktree` blocker

### Uncommitted changes

- **Problem:** Risk of losing work during worktree removal
- **Fix:** Preflight detects this as `uncommitted_changes` blocker

## Red Flags

**Never:**

- Skip the preflight step
- Force-merge a PR with merge conflicts
- Remove a worktree without merging first
- Run `scripts/merge_worktree.py` with `python` directly — it requires `uv`

**Always:**

- Run preflight first to check readiness
- Handle all blocker issues before proceeding
- Confirm with user on warnings (failing/pending checks)
- Use `cd` to switch to main worktree before running `remove` and `post-merge`

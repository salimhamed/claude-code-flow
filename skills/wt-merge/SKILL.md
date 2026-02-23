---
description:
  Squash-merge the current branch's PR, clean up the worktree, return to main,
  and report remaining worktree status
disable-model-invocation: true
allowed-tools:
  - AskUserQuestion
  - Bash(git *)
  - Bash(gh *)
  - Bash(cd *)
  - Bash(pwd)
---

# Merge Worktree

**Announce at start:** "I'm using the wt-merge skill to squash-merge and
clean up."

## Context

- **Current directory:** !`pwd`
- **Current branch:** !`git branch --show-current`
- **Worktrees:** !`git worktree list --porcelain`
- **Working tree status:** !`git status --porcelain`
- **Unpushed commits:** !`git rev-list @{u}..HEAD 2>/dev/null || echo NO_UPSTREAM`
- **PR info:** !`gh pr view --json number,url,state,title 2>&1 || echo NO_PR`

## Decision Flowchart

```mermaid
flowchart TD
    A[Preconditions] -- fail --> STOP
    A -- pass --> B[Merge PR]
    B --> C[Clean up worktree]
    C --> D[Update main & report]
```

## Preconditions

Only two checks before proceeding — everything else fails naturally with clear
errors from `gh pr merge`.

| Check | How to detect | Action |
|---|---|---|
| Uncommitted changes | Working tree status is non-empty | STOP — tell user to commit or stash |
| Unpushed commits | Output shows commit SHAs or `NO_UPSTREAM` | Run `git push -u origin HEAD`, then continue |

## Steps

### Step 1: Merge

```bash
gh pr merge --squash --delete-branch
```

If this fails, STOP and show the error to the user. The error message from `gh`
is self-explanatory (no PR, PR closed, merge conflicts, checks failing, etc.).

### Step 2: Clean up worktree

`cd` to the main worktree (first entry in the worktree list above), then:

```bash
git worktree remove --force {WORKTREE_PATH}
```

```bash
git worktree prune
```

```bash
git branch -D {BRANCH}
```

Tolerate errors on each command — the branch or directory may already be gone.

### Step 3: Update main

```bash
git fetch --prune && git pull --ff-only
```

If `pull --ff-only` fails, warn the user but continue to the report.

### Step 4: Report

Summarize:

- PR was squash-merged (include title and URL from context)
- Worktree was removed
- Main branch was updated (or note if ff-only failed)

List remaining worktrees from `git worktree list`. If any look stale (e.g.
branch no longer exists on remote), offer to clean them up.

## Red Flags

**Never:**

- Remove a worktree without merging first
- Delete worktrees the user didn't confirm

**Always:**

- Use `cd` to switch to main worktree before removing the feature worktree
- Tolerate errors during cleanup (worktree remove, branch delete)

# merge_worktree.py Reference

## Runtime

```bash
uv run scripts/merge_worktree.py <subcommand> [args...]
```

Inline PEP 723 dependency: `click>=8.1`. No virtual environment or `pip install`
needed — `uv run` handles it.

## `preflight`

### Usage

```bash
uv run scripts/merge_worktree.py preflight
```

No arguments. Must be run from within a feature worktree.

### Checks Performed

1. **Git repo detection** — confirms `cwd` is inside a git repository
2. **Current branch** — reads via `git branch --show-current`
3. **Worktree parsing** — `git worktree list --porcelain` to identify main vs
   current worktree
4. **Main worktree detection** — compares current repo root to first worktree
   entry
5. **Default branch** — via `gh repo view --json defaultBranchRef`
6. **Uncommitted changes** — `git status --porcelain`
7. **Unpushed commits** — checks for upstream with `git rev-parse @{u}`, then
   `git rev-list @{u}..HEAD`
8. **PR status** — `gh pr view --json number,url,state,title,mergeable,statusCheckRollup`

### JSON Output

```json
{
  "status": "ready | not_ready | error",
  "current_branch": "feature/auth",
  "worktree_path": "/path/to/feature-auth",
  "main_worktree_path": "/path/to/main",
  "default_branch": "main",
  "pr": {
    "number": 42,
    "url": "https://github.com/...",
    "title": "Add auth",
    "state": "OPEN",
    "mergeable": "MERGEABLE",
    "statusCheckRollup": []
  },
  "has_uncommitted_changes": false,
  "has_unpushed_commits": false,
  "other_worktrees": [{"path": "...", "branch": "..."}],
  "issues": [{"type": "...", "severity": "blocker|fixable|warning", "message": "..."}]
}
```

| Field                    | Description                                        |
| ------------------------ | -------------------------------------------------- |
| `status`                 | `ready` (no issues), `not_ready`, or `error`       |
| `current_branch`         | Branch name of the current worktree                |
| `worktree_path`          | Absolute path to the current (feature) worktree    |
| `main_worktree_path`     | Absolute path to the main worktree                 |
| `default_branch`         | Repository default branch (e.g. `main`)            |
| `pr`                     | PR metadata object, or `null` if no PR exists      |
| `has_uncommitted_changes`| Whether working tree has uncommitted changes       |
| `has_unpushed_commits`   | Whether there are commits not pushed to remote     |
| `other_worktrees`        | Non-main, non-current worktrees                    |
| `issues`                 | Array of detected issues (see table below)         |

### Issue Types

| Type                   | Severity  | Meaning                              |
| ---------------------- | --------- | ------------------------------------ |
| `on_default_branch`    | blocker   | On main, nothing to merge            |
| `in_main_worktree`     | blocker   | Not in a feature worktree            |
| `uncommitted_changes`  | blocker   | Must commit/stash first              |
| `no_pr`                | blocker   | No PR exists for branch              |
| `pr_not_open`          | blocker   | PR already merged/closed             |
| `not_mergeable`        | blocker   | PR has merge conflicts               |
| `unpushed_commits`     | fixable   | Skill pushes before merge            |
| `checks_failing`       | warning   | Ask user to confirm                  |
| `checks_pending`       | warning   | Ask user to wait or proceed          |

### Exit Codes

| Code | Meaning                                                |
| ---- | ------------------------------------------------------ |
| `0`  | `ready` — all checks passed                            |
| `1`  | `not_ready` or `error` — issues detected               |

## `merge`

### Usage

```bash
uv run scripts/merge_worktree.py merge
```

No arguments. Must be run from within the feature worktree whose PR should be
merged.

### Behavior

Runs `gh pr merge --squash --delete-branch` on the current branch's PR.

### JSON Output

#### `success`

```json
{
  "status": "success",
  "message": "..."
}
```

#### `error`

```json
{
  "status": "error",
  "message": "gh pr merge failed: ..."
}
```

### Exit Codes

| Code | Meaning                          |
| ---- | -------------------------------- |
| `0`  | PR merged successfully           |
| `1`  | Merge failed                     |

## `remove`

### Usage

```bash
uv run scripts/merge_worktree.py remove <WORKTREE_PATH>
```

| Argument         | Required | Description                              |
| ---------------- | -------- | ---------------------------------------- |
| `WORKTREE_PATH`  | Yes      | Absolute path to the worktree to remove  |

Must be run from the main worktree (after `cd`-ing there).

### Behavior

1. Parses `git worktree list --porcelain` to find the branch for the given path
2. Runs `git worktree remove --force <path>` (force handles untracked files)
3. Runs `git worktree prune` to clean stale entries
4. Runs `git branch -D <branch>` to delete the local branch reference

Handles edge cases gracefully:
- Path already gone: skips worktree remove, still prunes
- Branch already deleted: ignores `git branch -D` error

### JSON Output

#### `success`

```json
{
  "status": "success",
  "removed_path": "/path/to/worktree",
  "removed_branch": "feature/auth"
}
```

#### `error`

```json
{
  "status": "error",
  "message": "git worktree remove failed: ..."
}
```

### Exit Codes

| Code | Meaning                            |
| ---- | ---------------------------------- |
| `0`  | Worktree removed successfully      |
| `1`  | Removal failed                     |

## `post-merge`

### Usage

```bash
uv run scripts/merge_worktree.py post-merge
```

No arguments. Must be run from the main worktree.

### Behavior

1. `git fetch --prune` — cleans up deleted remote-tracking refs
2. `git pull --ff-only` — fast-forwards the main branch
3. Parses all worktrees; for each non-main worktree, checks
   `git ls-remote --heads origin <branch>` to determine if the remote branch
   still exists
4. Categorizes worktrees as `active` (remote exists) or `stale` (remote deleted)

### JSON Output

#### `success`

```json
{
  "status": "success",
  "main_updated": true,
  "stale_worktrees": [{"path": "...", "branch": "..."}],
  "active_worktrees": [{"path": "...", "branch": "..."}]
}
```

| Field              | Description                                          |
| ------------------ | ---------------------------------------------------- |
| `main_updated`     | Whether `git pull --ff-only` succeeded               |
| `stale_worktrees`  | Worktrees whose remote branch no longer exists        |
| `active_worktrees` | Worktrees with an active remote branch                |

#### `error`

```json
{
  "status": "error",
  "message": "git fetch --prune failed: ..."
}
```

### Exit Codes

| Code | Meaning                            |
| ---- | ---------------------------------- |
| `0`  | Post-merge completed successfully  |
| `1`  | Fetch or pull failed               |

## Edge Cases

| Case                             | Handling                                           |
| -------------------------------- | -------------------------------------------------- |
| No PR for current branch         | `preflight` reports `no_pr` blocker                |
| PR already merged/closed         | `preflight` reports `pr_not_open` blocker          |
| Branch never pushed              | `preflight` reports `unpushed_commits` (fixable)   |
| Merge conflicts on PR            | `preflight` reports `not_mergeable` blocker        |
| Worktree path already deleted    | `remove` skips worktree remove, still prunes       |
| Local branch already deleted     | `remove` ignores `git branch -D` error             |
| Main can't fast-forward          | `post-merge` reports error                         |
| No other worktrees               | `post-merge` returns empty stale/active arrays     |
| Not in a git repo                | `preflight` reports error immediately              |
| Checks failing on PR             | `preflight` reports `checks_failing` warning       |
| Checks still running             | `preflight` reports `checks_pending` warning       |

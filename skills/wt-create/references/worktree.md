# worktree.py Reference

## Runtime

```bash
uv run {SKILL_DIR}/scripts/worktree.py <subcommand> [args...]
```

Inline PEP 723 dependencies: `click>=8.1`, `pyyaml>=6.0`. No virtual
environment or `pip install` needed — `uv run` handles it.

## `create`

### Usage

```bash
uv run {SKILL_DIR}/scripts/worktree.py create <BRANCH_NAME> [--parent-dir <path>]
```

| Argument        | Required | Description                                                              |
| --------------- | -------- | ------------------------------------------------------------------------ |
| `BRANCH_NAME`   | Yes      | Branch name (new or existing) for the worktree                           |
| `--parent-dir`  | No       | Directory in which to create the worktree (default: parent of repo root) |

### Checks Performed

1. **Git repo detection** — confirms `cwd` is inside a git repository
2. **Default branch detection** — tries `git symbolic-ref refs/remotes/origin/HEAD`;
   falls back to checking `refs/remotes/origin/main` then `refs/remotes/origin/master`
3. **Branch verification** — ensures the current branch is the default branch
4. **Fetch + auto-pull** — fetches `origin/<default>` and compares local
   vs remote SHA; auto-pulls with `--ff-only` if behind (errors if diverged).
   Also fetches `origin/<BRANCH_NAME>` (non-fatal — ignored if the branch isn't
   on origin or the network is down) so the remote ref is current before the
   existence check below
5. **Path computation** — places the worktree in the parent of the repo root
   (or the directory given by `--parent-dir`), sanitizing `/` to `-` in the
   branch name (e.g. `feature/auth` becomes `feature-auth`)
6. **Collision check** — errors if the computed path already exists
7. **Branch existence check** — three cases, in priority order:
   - **Local branch exists** (`refs/heads/<branch>`) → check it out as-is
     (`is_new_branch: false`, `tracked_remote: false`). Local is preferred even
     if it has diverged from the remote — the branch is never auto-reset.
   - **Only the remote branch exists** (`refs/remotes/origin/<branch>`) →
     create a local tracking branch from it via `--track -b`
     (`is_new_branch: false`, `tracked_remote: true`)
   - **Neither exists** → create a new branch off the default branch with `-b`
     (`is_new_branch: true`, `tracked_remote: false`)
8. **`git worktree add`** — creates the worktree

### JSON Output

The `status` field determines which additional fields are present.

#### `success`

```json
{
  "status": "success",
  "worktree_path": "/Users/jesse/Code/myproject/feature-auth",
  "branch": "feature/auth",
  "is_new_branch": true,
  "tracked_remote": false,
  "default_branch": "main",
  "base_sha": "abc1234..."
}
```

| Field            | Description                                 |
| ---------------- | ------------------------------------------- |
| `worktree_path`  | Absolute path to the new worktree directory    |
| `branch`         | Branch name as provided                        |
| `is_new_branch`  | `true` if newly created, `false` if pre-existing |
| `tracked_remote` | `true` if a local tracking branch was created from `origin/<branch>` |
| `default_branch` | Detected default branch (e.g. `main`)          |
| `base_sha`       | Commit SHA the worktree was created from       |

#### `wrong_branch`

```json
{
  "status": "wrong_branch",
  "current_branch": "feature/old",
  "default_branch": "main"
}
```

#### `error`

```json
{
  "status": "error",
  "message": "Path already exists: /Users/jesse/Code/myproject/feature-auth"
}
```

### Exit Codes

| Code | Meaning                                                       |
| ---- | ------------------------------------------------------------- |
| `0`  | `success` — worktree created                                  |
| `1`  | Any other status (`wrong_branch`, `error`)                    |

## `setup`

### Usage

```bash
uv run {SKILL_DIR}/scripts/worktree.py setup <WORKTREE_PATH>
```

| Argument         | Required | Description                        |
| ---------------- | -------- | ---------------------------------- |
| `WORKTREE_PATH`  | Yes      | Target worktree directory to set up |

### Behavior

Runs sync then post-create hooks in one invocation:

1. Finds the main worktree via `git worktree list --porcelain`
2. Syncs config files (same as `sync` — see below)
3. Runs post-create hooks (same as `run-hooks` — see below)

Resolves the main worktree root once and passes it to both operations,
avoiding redundant git calls.

### Exit Codes

| Code | Meaning                                                        |
| ---- | -------------------------------------------------------------- |
| `0`  | Both sync and hooks succeeded (or were graceful no-ops)        |
| `1`  | Sync or hook failure, not in git repo, or malformed YAML       |

## `sync`

### Usage

```bash
uv run {SKILL_DIR}/scripts/worktree.py sync <WORKTREE_PATH>
```

| Argument         | Required | Description                        |
| ---------------- | -------- | ---------------------------------- |
| `WORKTREE_PATH`  | Yes      | Target worktree directory to sync  |

### Behavior

1. Finds the main worktree via `git worktree list --porcelain` (first entry)
2. Reads `copy` list from `.worktreerc.yml` (or `.worktreerc.yaml`) in the main worktree root
3. Globs each pattern against the main worktree
4. Copies matching files/directories into the target worktree
   - Automatically copies `.worktreerc.yml`/`.yaml` into the target worktree if present and not already there
   - Skips files that already exist in the target
   - Directories: `shutil.copytree`; files: `shutil.copy2`

### Output

```text
Syncing from /path/to/main into /path/to/worktree:
  copied .env
  copied .env.local
Done.
```

### Exit Codes

| Code | Meaning                                                        |
| ---- | -------------------------------------------------------------- |
| `0`  | Success, or graceful no-op (no config, main worktree, etc.)    |
| `1`  | Not inside a git repository, or malformed `.worktreerc.yml`    |

## `run-hooks`

### Usage

```bash
uv run {SKILL_DIR}/scripts/worktree.py run-hooks <WORKTREE_PATH>
```

| Argument         | Required | Description                                 |
| ---------------- | -------- | ------------------------------------------- |
| `WORKTREE_PATH`  | Yes      | Worktree directory to run hooks in          |

### Behavior

1. Finds the main worktree via `git worktree list --porcelain`
2. Reads `post_create` list from `.worktreerc.yml` (or `.worktreerc.yaml`) in the main worktree root
3. Executes each command sequentially via `subprocess.run(shell=True, cwd=worktree_path)`
   - stdout and stderr flow through to the terminal (no capture)
   - Stops on first non-zero exit code

### Output

```text
Running: uv sync
Running: pre-commit install
All hooks completed successfully.
```

On failure:

```text
Running: uv sync
Hook failed (exit 1): uv sync
```

### Exit Codes

| Code | Meaning                                                        |
| ---- | -------------------------------------------------------------- |
| `0`  | All hooks ran successfully, or no hooks defined                 |
| `1`  | A hook command failed, not in git repo, or malformed YAML      |

## `.worktreerc.yml` / `.worktreerc.yaml` Format

Either extension is supported. `.yml` is checked first.

```yaml
worktree:
  # Files/dirs to copy from main worktree (glob patterns)
  copy:
    - .env
    - .env.local
    - .direnv

  # Commands to run in the new worktree after creation
  post_create:
    - uv sync
    - pre-commit install

```

- Top-level key must be `worktree`
- `copy`: list of glob patterns matched against the main worktree root
- `post_create`: list of shell commands run via `shell=True` (pipes, redirects,
  etc. all work)
- All sections are optional — missing or empty sections are graceful no-ops

## Edge Cases

| Case                          | Handling                                              |
| ----------------------------- | ----------------------------------------------------- |
| No `.worktreerc.yml`/`.yaml`  | `setup`, `sync`, and `run-hooks` print no-op message, exit 0 |
| Empty `copy`/`post_create`   | Same as missing — graceful no-op                      |
| Malformed YAML                | `click.ClickException` with parse error, exit 1       |
| Hook command not found        | Shell returns exit 127, caught by stop-on-fail logic  |
| Commands with pipes/redirects | Work via `shell=True`                                 |
| `sync` on main worktree      | Detected via path comparison, prints message, exit 0  |
| Existing local branch         | Checked out without `-b`; `is_new_branch` is `false`, `tracked_remote` is `false` |
| Remote-only branch            | Local tracking branch created from `origin/<branch>` via `--track -b`; `tracked_remote` is `true` |
| Local + remote diverged       | Local branch preferred; never auto-reset to the remote |
| Branch checked out elsewhere  | `git worktree add` rejects; error message surfaced     |
| Not in a git repo             | `get_main_worktree()` raises, caught and reported     |

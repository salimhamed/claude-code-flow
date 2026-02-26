# claude-code-flow

A Claude Code plugin providing developer workflow utilities to keep in the flow.

## Skills

| Command | Description |
| ------- | ----------- |
| `/flow:pr-create` | Create a pull request with auto-generated title and body from branch context |
| `/flow:pr-desc` | Update an existing PR's description from current branch context |
| `/flow:pr-title` | Update an existing PR's title from current branch context |
| `/flow:wt-create` | Create an isolated git worktree with config syncing and post-create hooks |
| `/flow:wt-init` | Scan the project and generate a `.worktreerc.yml` with sensible defaults |
| `/flow:wt-destroy` | Destroy a worktree — close any PR, delete branches, and remove the worktree |
| `/flow:wt-merge` | Squash-merge the current branch's PR, clean up the worktree, and update main |

All skills are manual-invocation only (`disable-model-invocation: true`) — Claude will not run them autonomously.

## Installation

### Requirements

- **Git** (`git`)
- **GitHub CLI (`gh`)**
- **uv** (`uv`)

### From GitHub

Add the marketplace from within Claude Code:

Using HTTPS:

```
/plugin marketplace add https://github.com/salimhamed/claude-code-flow.git
```

Or using SSH:

```
/plugin marketplace add git@github.com:salimhamed/claude-code-flow.git
```

Then install the plugin:

```
/plugin install flow@claude-code-flow
```

### Local development

Clone the repository from your terminal:

```bash
git clone https://github.com/salimhamed/claude-code-flow.git
```

Then from within Claude Code, add the local directory and install:

```
/plugin marketplace add ./claude-code-flow
/plugin install flow@claude-code-flow
```

## Usage

### Create a PR

```
/flow:pr-create
```

Gathers branch context (commits, diff, changed files), generates a title and body, then creates the PR via `gh pr create`. Refuses if on the base branch, no commits exist, or a PR already exists.

### Update PR description

```
/flow:pr-desc
```

Updates the body of an existing PR based on the current branch context. Accepts optional instructions:

```
/flow:pr-desc include a ## Usage section showing how to use each skill
```

### Update PR title

```
/flow:pr-title
```

Updates the title of an existing PR based on current branch context.

### Create a git worktree

```
/flow:wt-create feature-branch
```

Creates an isolated git worktree in a sibling directory. Handles branch verification, freshness checks against origin, config file syncing (via `.worktreerc.yml`), and post-create hooks.

#### Configuring worktrees

Add an optional `.worktreerc.yaml` file to your repo root to control file syncing and post-create hooks:

```yaml
worktree:
  # Glob patterns matched against the main worktree root.
  # Matched files are copied into new worktrees (existing files are not overwritten).
  copy:
    - .env
    - .env.local
    - .direnv

  # Shell commands run sequentially in the new worktree directory.
  # Stops on first failure.
  post_create:
    - uv sync
    - pre-commit install
```

The `tmux` section opens a new tmux window or session in the worktree directory after creation:

```yaml
worktree:
  tmux:
    enabled: true    # opt-in (default: off)
    mode: window     # "window" (default) or "session"
    command: claude   # command to run in the new window/session (default: user's shell)
```

All sections are optional. Omit any one and it becomes a no-op.

### Generate a worktreerc

```
/flow:wt-init
```

Scans the project for gitignored config files, lock files, and dev tooling, then generates a `.worktreerc.yml` with sensible defaults. Detects patterns like `.env` files, `uv.lock`, `package-lock.json`, `.mise.toml`, `.pre-commit-config.yaml`, and more.

### Destroy a worktree

```
/flow:wt-destroy [branch-name]
```

Forcefully tears down a worktree — closes any associated PR, deletes local and remote branches, and removes the worktree directory. Discards uncommitted changes. Can target the current worktree (no argument) or a specific branch.

### Merge a worktree

```
/flow:wt-merge
```

Run from a feature worktree with an open PR. Squash-merges the PR, removes the worktree, updates main, and reports remaining worktree status. Automatically pushes unpushed commits before merging. Blocks on uncommitted changes.

## License

MIT

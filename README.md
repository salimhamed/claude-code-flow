# claude-code-flow

A Claude Code plugin providing developer workflow utilities for PRs and git worktrees.

## Skills

| Skill | Command | Description |
| ----- | ------- | ----------- |
| **pr** | `/flow:pr` | Create a pull request with auto-generated title and body from branch context |
| **pr-desc** | `/flow:pr-desc` | Update an existing PR's description from current branch context |
| **pr-title** | `/flow:pr-title` | Update an existing PR's title from current branch context |
| **create-git-worktree** | `/flow:create-git-worktree` | Create an isolated git worktree with config syncing and post-create hooks |

## Installation

### From marketplace

```
claude plugin install claude-code-flow
```

### Local development

```bash
git clone https://github.com/salimhamed/claude-code-flow.git
claude --plugin-dir /path/to/claude-code-flow
```

## Usage

### Create a PR

```
/flow:pr
```

Gathers branch context (commits, diff, changed files), generates a title and body, then creates the PR via `gh pr create`. Refuses if on the base branch, no commits exist, or a PR already exists.

### Update PR description

```
/flow:pr-desc
```

Updates the body of an existing PR based on current branch context. Accepts optional instructions:

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
/flow:create-git-worktree feature-branch
```

Creates an isolated git worktree in a sibling directory. Handles branch verification, freshness checks against origin, config file syncing (via `.worktreerc.yml`), and post-create hooks.

## Requirements

- **Git** — all skills
- **GitHub CLI (`gh`)** — PR skills (`pr`, `pr-desc`, `pr-title`)
- **`uv`** — worktree skill (`create-git-worktree`)
- **Python 3.10+** — all skills

## License

MIT

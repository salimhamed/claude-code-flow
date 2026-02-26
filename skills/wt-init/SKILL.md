---
disable-model-invocation: true
description:
  Generate a .worktreerc.yml config file for the current project by scanning for
  environment files, lock files, and dev tooling - use when setting up worktree
  workflows for a new project
allowed-tools:
  - Glob
  - Read
  - Write
  - Bash(git *)
  - AskUserQuestion
---

# Generate .worktreerc.yml

Scan the current project and generate a `.worktreerc.yml` with sensible defaults
for the `wt-create` skill.

## Steps

### 1. Check for Existing Config

Look for `.worktreerc.yml` or `.worktreerc.yaml` in the repository root.

If one exists, read it, show it to the user, and ask if they want to overwrite or
update it. Stop if they decline.

### 2. Scan Project for Patterns

#### Copy Candidates

Use Glob to detect files that are typically gitignored but needed for development:

- `.env`, `.env.*`
- `.direnv`
- `.vscode/settings.json`
- `.idea/`

For each candidate found, verify it is actually gitignored:

```bash
git check-ignore <file>
```

Only include files that are gitignored (exit code 0). Files tracked by git don't
need to be copied.

#### Post-Create Hook Candidates

Use Glob to detect lock files and dev tooling:

| File Found                  | Suggested Hook        |
| --------------------------- | --------------------- |
| `uv.lock` or `pyproject.toml` (with `[tool.uv]`) | `uv sync`             |
| `package-lock.json`        | `npm ci`              |
| `yarn.lock`                | `yarn install`        |
| `pnpm-lock.yaml`           | `pnpm install`        |
| `Gemfile.lock`             | `bundle install`      |
| `.mise.toml` or `.tool-versions` | `mise install`  |
| `.pre-commit-config.yaml`  | `pre-commit install`  |

### 3. Present Findings to User

Show what was detected and proposed. Use `AskUserQuestion` to let the user
confirm or adjust:

- Which copy patterns to include
- Which post-create hooks to include
- Whether to change the default tmux command or mode (`window` vs `session`)

### 4. Write .worktreerc.yml

Generate the file with the confirmed settings. Always include the `tmux` section
with `command: claude` as the default.

Example output:

```yaml
worktree:
  copy:
    - .env
    - .env.local

  post_create:
    - uv sync
    - pre-commit install

  tmux:
    enabled: true
    mode: window
    command: claude
```

Omit `copy` or `post_create` sections entirely if they would be empty.
The `tmux` section should always be included with `enabled: true` (since the user
explicitly opted to generate the config).

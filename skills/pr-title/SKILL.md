---
description: Update PR title from current branch context
disable-model-invocation: true
allowed-tools:
  - Bash(git *)
  - Bash(gh *)
  - Bash(python *)
---

# Update PR Title

## Script Location

**Scripts live next to this SKILL.md, not in the user's project.** Before
running any script, determine the directory containing this SKILL.md file. Use
that absolute path as `{SKILL_DIR}` when constructing script paths below.

!read references/usage.md

## Gather Context

Run the gather script, passing the user's project directory with `-C`:

```bash
python {SKILL_DIR}/scripts/gather_context.py -C <user-project-directory>
```

## Preconditions

Check these in the JSON output BEFORE proceeding:

1. **PR must exist**: If `pr_number` is null, STOP and say: "Error: No PR exists
   for this branch. Use `/flow:pr-create` to create one first."

## Execution

Update the PR title:

```bash
python {SKILL_DIR}/scripts/update_title.py -C <user-project-directory> --title "<new title>"
```

## Title Format

- Under 70 characters
- Imperative mood (e.g., "Add feature" not "Added feature")
- No period at end
- Summarize the main change from commits and diff

## Output

After updating, output:

```
Updated PR #<number> title to: <new title>
<url>
```

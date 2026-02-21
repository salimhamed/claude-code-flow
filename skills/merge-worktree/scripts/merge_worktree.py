#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "click>=8.1",
# ]
# ///
import json
import subprocess
import sys
from pathlib import Path

import click


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def json_output(status: str, **fields):
    print(json.dumps({"status": status, **fields}))
    sys.exit(0 if status in ("success", "ready") else 1)


def parse_worktrees() -> list[dict]:
    result = run(["git", "worktree", "list", "--porcelain"])
    if result.returncode != 0:
        return []
    worktrees = []
    current = {}
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            current = {"path": line.removeprefix("worktree ")}
        elif line.startswith("branch "):
            current["branch"] = line.removeprefix("branch refs/heads/")
        elif line == "bare":
            current["bare"] = True
        elif line == "" and current:
            worktrees.append(current)
            current = {}
    if current:
        worktrees.append(current)
    return worktrees


def get_main_worktree(worktrees: list[dict]) -> dict | None:
    return worktrees[0] if worktrees else None


@click.group()
def cli():
    pass


@cli.command()
def preflight():
    """Gather context and check readiness for merge-worktree flow."""
    issues = []

    # Git repo detection
    result = run(["git", "rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        json_output("error", message="Not inside a git repository.")
    repo_root = Path(result.stdout.strip()).resolve()

    # Current branch
    result = run(["git", "branch", "--show-current"])
    current_branch = result.stdout.strip()

    # Parse worktrees
    worktrees = parse_worktrees()
    main_wt = get_main_worktree(worktrees)
    if not main_wt:
        json_output("error", message="Could not determine main worktree.")
    main_worktree_path = Path(main_wt["path"]).resolve()

    # Detect if running from main worktree
    in_main_worktree = repo_root == main_worktree_path

    # Default branch
    result = run(
        ["gh", "repo", "view", "--json", "defaultBranchRef", "-q", ".defaultBranchRef.name"]
    )
    default_branch = result.stdout.strip() or "main"

    # Check blockers: on default branch or in main worktree
    if current_branch == default_branch:
        issues.append({
            "type": "on_default_branch",
            "severity": "blocker",
            "message": f"Currently on {default_branch}. Nothing to merge.",
        })
    if in_main_worktree:
        issues.append({
            "type": "in_main_worktree",
            "severity": "blocker",
            "message": "Must run from a feature worktree, not the main worktree.",
        })

    # Uncommitted changes
    result = run(["git", "status", "--porcelain"])
    has_uncommitted = bool(result.stdout.strip())
    if has_uncommitted:
        issues.append({
            "type": "uncommitted_changes",
            "severity": "blocker",
            "message": "Uncommitted changes detected. Commit or stash before merging.",
        })

    # Unpushed commits
    has_unpushed = False
    result = run(["git", "rev-parse", "@{u}"])
    if result.returncode != 0:
        # No upstream — branch was never pushed
        has_unpushed = True
        issues.append({
            "type": "unpushed_commits",
            "severity": "fixable",
            "message": "Branch has no upstream. Needs to be pushed first.",
        })
    else:
        result = run(["git", "rev-list", "@{u}..HEAD"])
        if result.stdout.strip():
            has_unpushed = True
            issues.append({
                "type": "unpushed_commits",
                "severity": "fixable",
                "message": "Unpushed commits detected. Will push before merging.",
            })

    # PR status
    pr_info = None
    result = run([
        "gh", "pr", "view", "--json",
        "number,url,state,title,mergeable,statusCheckRollup",
    ])
    if result.returncode != 0 or not result.stdout.strip():
        issues.append({
            "type": "no_pr",
            "severity": "blocker",
            "message": "No pull request found for this branch.",
        })
    else:
        pr_info = json.loads(result.stdout)

        if pr_info.get("state") != "OPEN":
            issues.append({
                "type": "pr_not_open",
                "severity": "blocker",
                "message": f"PR is {pr_info.get('state', 'unknown')}, not OPEN.",
            })

        mergeable = pr_info.get("mergeable", "")
        if mergeable == "CONFLICTING":
            issues.append({
                "type": "not_mergeable",
                "severity": "blocker",
                "message": "PR has merge conflicts that must be resolved first.",
            })

        checks = pr_info.get("statusCheckRollup") or []
        check_states = [c.get("conclusion") or c.get("state", "") for c in checks]
        if any(s == "FAILURE" for s in check_states):
            issues.append({
                "type": "checks_failing",
                "severity": "warning",
                "message": "Some status checks are failing.",
            })
        elif any(s in ("PENDING", "QUEUED", "IN_PROGRESS", "") for s in check_states):
            issues.append({
                "type": "checks_pending",
                "severity": "warning",
                "message": "Some status checks are still running.",
            })

    # Build other_worktrees list (exclude main and current)
    other_worktrees = []
    for wt in worktrees[1:]:  # skip main (index 0)
        wt_path = Path(wt["path"]).resolve()
        if wt_path != repo_root:
            other_worktrees.append({"path": wt["path"], "branch": wt.get("branch", "")})

    status = "ready" if not issues else "not_ready"

    output = {
        "status": status,
        "current_branch": current_branch,
        "worktree_path": str(repo_root),
        "main_worktree_path": str(main_worktree_path),
        "default_branch": default_branch,
        "pr": pr_info,
        "has_uncommitted_changes": has_uncommitted,
        "has_unpushed_commits": has_unpushed,
        "other_worktrees": other_worktrees,
        "issues": issues,
    }
    print(json.dumps(output))
    sys.exit(0 if status == "ready" else 1)


@cli.command()
def merge():
    """Squash-merge the current branch's PR via gh."""
    result = run(["gh", "pr", "merge", "--squash", "--delete-branch"])
    if result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        message = stderr or stdout or "gh pr merge failed with no output."
        json_output("error", message=message)
    json_output("success", message=result.stdout.strip())


@cli.command()
@click.argument("worktree_path")
def remove(worktree_path: str):
    """Remove a worktree and clean up its local branch."""
    target = Path(worktree_path).resolve()

    # Find the branch associated with this worktree
    worktrees = parse_worktrees()
    branch = None
    for wt in worktrees:
        if Path(wt["path"]).resolve() == target:
            branch = wt.get("branch")
            break

    # Remove the worktree (force handles untracked files like .env)
    if target.exists():
        result = run(["git", "worktree", "remove", "--force", str(target)])
        if result.returncode != 0:
            stderr = result.stderr.strip()
            json_output("error", message=f"git worktree remove failed: {stderr}")

    # Prune stale worktree entries
    run(["git", "worktree", "prune"])

    # Delete the local branch ref (safe — already squash-merged)
    if branch:
        run(["git", "branch", "-D", branch])

    json_output("success", removed_path=str(target), removed_branch=branch)


@cli.command("post-merge")
def post_merge():
    """Update main branch and report remaining worktree status."""
    # Fetch and prune deleted remote-tracking refs
    result = run(["git", "fetch", "--prune"])
    if result.returncode != 0:
        json_output("error", message=f"git fetch --prune failed: {result.stderr.strip()}")

    # Fast-forward main
    result = run(["git", "pull", "--ff-only"])
    main_updated = result.returncode == 0
    if not main_updated:
        json_output(
            "error",
            message=f"git pull --ff-only failed: {result.stderr.strip()}",
        )

    # Categorize remaining worktrees
    worktrees = parse_worktrees()
    stale = []
    active = []
    for wt in worktrees[1:]:  # skip main
        branch = wt.get("branch", "")
        if not branch:
            continue
        result = run(["git", "ls-remote", "--heads", "origin", branch])
        if result.stdout.strip():
            active.append({"path": wt["path"], "branch": branch})
        else:
            stale.append({"path": wt["path"], "branch": branch})

    json_output(
        "success",
        main_updated=main_updated,
        stale_worktrees=stale,
        active_worktrees=active,
    )


if __name__ == "__main__":
    cli()

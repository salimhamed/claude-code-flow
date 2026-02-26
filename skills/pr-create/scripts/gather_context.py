#!/usr/bin/env python3
"""Gather context for creating a pull request."""

import argparse
import json
import os
import subprocess
import sys


def run(cmd: list[str], cwd: str | None = None, check: bool = False) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)
    return result.stdout.strip()


def get_base_branch(cwd: str) -> str:
    return run(["gh", "repo", "view", "--json", "defaultBranchRef", "-q", ".defaultBranchRef.name"], cwd=cwd) or "main"


def get_current_branch(cwd: str) -> str:
    return run(["git", "branch", "--show-current"], cwd=cwd)


def is_pushed(cwd: str) -> bool:
    result = run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], cwd=cwd)
    return bool(result)


def get_existing_pr(cwd: str) -> dict | None:
    output = run(["gh", "pr", "view", "--json", "number,url"], cwd=cwd)
    if not output:
        return None
    return json.loads(output)


def get_commits(base_branch: str, cwd: str) -> list[str]:
    output = run(["git", "log", f"{base_branch}..HEAD", "--oneline"], cwd=cwd)
    return output.splitlines() if output else []


def get_diff_stat(base_branch: str, cwd: str) -> str:
    output = run(["git", "diff", f"{base_branch}...HEAD", "--stat"], cwd=cwd)
    lines = output.splitlines()
    return "\n".join(lines[-20:]) if len(lines) > 20 else output


def get_files_changed(base_branch: str, cwd: str) -> list[str]:
    output = run(["git", "diff", f"{base_branch}...HEAD", "--name-only"], cwd=cwd)
    return output.splitlines() if output else []


def get_diff(base_branch: str, cwd: str, max_lines: int = 500) -> str:
    output = run(["git", "diff", f"{base_branch}...HEAD"], cwd=cwd)
    lines = output.splitlines()
    if len(lines) > max_lines:
        return "\n".join(lines[:max_lines]) + f"\n\n... (truncated, {len(lines) - max_lines} more lines)"
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-C", default=os.getcwd(), help="Project directory")
    args = parser.parse_args()
    repo_dir = args.C

    base_branch = get_base_branch(repo_dir)
    current_branch = get_current_branch(repo_dir)

    context = {
        "current_branch": current_branch,
        "base_branch": base_branch,
        "is_pushed": is_pushed(repo_dir),
        "existing_pr": get_existing_pr(repo_dir),
        "commits": get_commits(base_branch, repo_dir),
        "diff_stat": get_diff_stat(base_branch, repo_dir),
        "files_changed": get_files_changed(base_branch, repo_dir),
        "diff": get_diff(base_branch, repo_dir),
    }

    print(json.dumps(context, indent=2))


if __name__ == "__main__":
    main()

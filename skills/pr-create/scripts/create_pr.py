#!/usr/bin/env python3
"""Create a pull request with the given title and body."""

import argparse
import os
import subprocess
import sys


def is_pushed(cwd: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        capture_output=True,
        cwd=cwd,
    )
    return result.returncode == 0


def push_branch(cwd: str) -> bool:
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
        cwd=cwd,
    ).stdout.strip()
    result = subprocess.run(["git", "push", "-u", "origin", branch], cwd=cwd)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Create a pull request")
    parser.add_argument("--title", required=True, help="PR title")
    parser.add_argument("--body", required=True, help="PR body")
    parser.add_argument("-C", default=os.getcwd(), help="Project directory")
    args = parser.parse_args()

    repo_dir = args.C
    if not is_pushed(repo_dir) and not push_branch(repo_dir):
        sys.exit(1)

    result = subprocess.run(
        ["gh", "pr", "create", "--title", args.title, "--body", args.body],
        cwd=repo_dir,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

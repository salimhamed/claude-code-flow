#!/usr/bin/env python3
"""Update the PR description."""

import argparse
import os
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="Update PR description")
    parser.add_argument("--body", required=True, help="New PR body")
    parser.add_argument("-C", default=os.getcwd(), help="Project directory")
    args = parser.parse_args()

    result = subprocess.run(
        ["gh", "pr", "edit", "--body", args.body],
        cwd=args.C,
        check=False,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

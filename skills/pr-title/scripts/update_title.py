#!/usr/bin/env python3
"""Update the PR title."""

import argparse
import os
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="Update PR title")
    parser.add_argument("--title", required=True, help="New PR title")
    parser.add_argument("-C", default=os.getcwd(), help="Project directory")
    args = parser.parse_args()

    result = subprocess.run(
        ["gh", "pr", "edit", "--title", args.title],
        cwd=args.C,
        check=False,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

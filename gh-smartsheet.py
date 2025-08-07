#!/usr/bin/env python3
import os
import sys
from github import Github

def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: set your GitHub token in the GITHUB_TOKEN env var", file=sys.stderr)
        sys.exit(1)

    g = Github(token)
    repo = g.get_repo("innabox/issues")

    for issue in repo.get_issues(state="all"):
        print(f"#{issue.number} {issue.title} — {issue.state}")

if __name__ == "__main__":
    main()
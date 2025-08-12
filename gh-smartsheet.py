#!/usr/bin/env python3
import os
import sys
from github import Github
import requests
from dotenv import load_dotenv


def check_env():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    SMARTSHEET_TOKEN = os.getenv("SMARTSHEET_TOKEN")
    SMARTSHEET_SHEET_ID = os.getenv("SMARTSHEET_SHEET_ID")

    # Optional: validate presence
    missing = [k for k, v in {
        "GITHUB_TOKEN": GITHUB_TOKEN,
        "SMARTSHEET_TOKEN": SMARTSHEET_TOKEN,
        "SMARTSHEET_SHEET_ID": SMARTSHEET_SHEET_ID
    }.items() if not v]

    if missing:
        print(f"Error: missing in .env -> {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)


def fetch_smartsheet(sheet_id, token):
    """
    Fetch metadata for a specific Smartsheet.
    Returns the parsed JSON.
    """
    url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def gh_access():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: set your GitHub token in the GITHUB_TOKEN env var", file=sys.stderr)
        sys.exit(1)

    g = Github(token)
    repo = g.get_repo("innabox/issues")

    for issue in repo.get_issues(state="all"):
        print(f"#{issue.number} {issue.title} — {issue.state}")

def sm_access():
    sm_token = os.getenv("SMARTSHEET_TOKEN")
    sheet_id = os.getenv("SMARTSHEET_SHEET_ID")

    if not sm_token or not sheet_id:
        print(
            "Warning: SMARTSHEET_TOKEN and/or SMARTSHEET_SHEET_ID not set; skipping Smartsheet fetch.",
            file=sys.stderr
        )
        return

    try:
        sheet = fetch_smartsheet(sheet_id, sm_token)
    except requests.HTTPError as e:
        print(f"Error fetching Smartsheet {sheet_id}: {e}", file=sys.stderr)
        sys.exit(1)

    return sheet

def main():

    gh_access()
    sheet = sm_access()

    # Print out a summary of the sheet
    name = sheet.get("name", "<unnamed>")
    row_count = sheet.get("totalRowCount", "unknown")
    print(f"\nSmartsheet “{name}” (ID: {sheet_id}) has {row_count} rows.")

if __name__ == "__main__":
    main()

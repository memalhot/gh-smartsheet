#!/usr/bin/env python3
import os
import sys
from github import Github
import requests
from dotenv import load_dotenv

# -----------------------------
# ENV
# -----------------------------
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

    return GITHUB_TOKEN, SMARTSHEET_TOKEN, SMARTSHEET_SHEET_ID


# -----------------------------
# GITHUB
# -----------------------------

def collect_github_issues(token):
    """
    Fetch issues from the same repo used in gh_access
    Returns list of dicts: {number, title, state}
    """
    g = Github(token)
    repo = g.get_repo("innabox/issues")
    
    for issue in repo.get_issues(state="all"):
        print(f"#{issue.number} {issue.title} — {issue.state}")
    
    data = []
    for issue in repo.get_issues(state="all"):
        data.append({
            "number": issue.number,
            "title": issue.title,
            "state": issue.state
        })
    return data


# -----------------------------
# SMARTSHEET helpers
# -----------------------------
def sm_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }


def fetch_smartsheet(sheet_id, token):
    """
    Fetch metadata for a specific Smartsheet.
    Returns the parsed JSON.
    """
    url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}"
    resp = requests.get(url, headers=sm_headers(token))
    resp.raise_for_status()
    return resp.json()

def get_or_create_columns(sheet_id, token):
    """
    Ensure the sheet has columns: Issue Number, Title, Status (TEXT_NUMBER).
    Return a dict: { "Issue Number": id, "Title": id, "Status": id }
    """
    sheet = fetch_smartsheet(sheet_id, token)
    existing = {c["title"]: c for c in sheet.get("columns", [])}

    required = [
        ("Issue Number", "TEXT_NUMBER"),
        ("Title", "TEXT_NUMBER"),
        ("Status", "TEXT_NUMBER"),
    ]

    def extract_id(resp_json):
        # Smartsheet returns {"message":"SUCCESS","resultCode":0,"result": {…column…}}
        # or result: [ {…}, {…} ] for bulk calls.
        if isinstance(resp_json, dict) and "result" in resp_json:
            res = resp_json["result"]
            if isinstance(res, list):
                return res[0]["id"]
            return res["id"]
        # Fallback: some SDK/helpers may return the raw Column object
        if isinstance(resp_json, dict) and "id" in resp_json:
            return resp_json["id"]
        raise ValueError(f"Unexpected column-create response shape: {resp_json}")

    col_ids = {}
    next_index = len(sheet.get("columns", []))

    for title, col_type in required:
        if title in existing:
            col_ids[title] = existing[title]["id"]
            continue

        url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}/columns"
        payload = {"title": title, "type": col_type, "index": next_index}
        r = requests.post(url, headers=sm_headers(token), json=payload)
        r.raise_for_status()
        created = r.json()
        col_ids[title] = extract_id(created)
        next_index += 1

    return col_ids


def add_issue_rows(sheet_id, token, issues, col_ids, batch_size=300):
    """
    Append rows to the sheet with Issue Number, Title, Status.
    issues: iterable of dicts with keys: number (int), title (str), state (str)
    """
    def chunk(seq, n):
        for i in range(0, len(seq), n):
            yield seq[i:i+n]

    rows = []
    for it in issues:
        rows.append({
            #"toBottom": True,
            "cells": [
                {"columnId": col_ids["Issue Number"], "value": it["number"]},
                {"columnId": col_ids["Title"],        "value": it["title"]},
                {"columnId": col_ids["Status"],       "value": it["state"]},
            ]
        })

    if not rows:
        print("No issues to add to Smartsheet.")
        return

    url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}/rows"
    # Smartsheet expects an array of row objects in the body.
    for group in chunk(rows, batch_size):
        r = requests.post(url, headers=sm_headers(token), json=group)
        r.raise_for_status()

    print(f"Added {len(rows)} rows to Smartsheet sheet {sheet_id}.")


# -----------------------------
# main
# -----------------------------
def main():
    GITHUB_TOKEN, SMARTSHEET_TOKEN, SMARTSHEET_SHEET_ID = check_env()

    # Make sure the sheet exists and columns are ready
    col_ids = get_or_create_columns(SMARTSHEET_SHEET_ID, SMARTSHEET_TOKEN)

    # Collect issues
    issues = collect_github_issues(GITHUB_TOKEN)

    # Append rows to Smartsheet
    add_issue_rows(SMARTSHEET_SHEET_ID, SMARTSHEET_TOKEN, issues, col_ids)


if __name__ == "__main__":
    main()

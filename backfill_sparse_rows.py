"""
Backfill DynamoDB rows left sparse by the update_item upsert bug.

Finds items in PRSummaries missing author/title/created_at (the fields only
ever set by the full analysis put_item), re-fetches the PR from GitHub,
re-runs the same diff/commit analysis the webhook does, and writes the
complete item back.

Usage:
    python backfill_sparse_rows.py                # dry run, prints what would change
    python backfill_sparse_rows.py --apply         # actually writes to DynamoDB
    python backfill_sparse_rows.py --apply --update-github   # also re-patches PR description/labels
    python backfill_sparse_rows.py --apply --limit 5         # only process first 5 (testing)
"""
import argparse
import json
import os
import time

import boto3

from utils import github, openai_utils

TABLE_NAME = os.getenv("DYNAMODB_TABLE", "PRSummaries")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def find_sparse_items():
    items = []
    scan_kwargs = {
        "FilterExpression": (
            "attribute_not_exists(author) OR attribute_not_exists(title) "
            "OR attribute_not_exists(created_at)"
        )
    }
    while True:
        resp = table.scan(**scan_kwargs)
        items.extend(resp.get("Items", []))
        if "LastEvaluatedKey" not in resp:
            break
        scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
    return items


def pr_number_from_pr_id(pr_id: str) -> str:
    # pr_id was built as f"{github_pr_id}-{pr_number}"
    return pr_id.rsplit("-", 1)[-1]


def backfill_item(item: dict, apply: bool, update_github: bool):
    repo = item["repo"]
    pr_id = item["pr_id"]
    pr_number = item.get("pr_number") or pr_number_from_pr_id(pr_id)

    pr = github.get_pr(repo, pr_number)
    diff_text = github.get_pr_diff(pr["diff_url"])
    commit_messages = github.get_pr_commits(pr["commits_url"])
    analysis = openai_utils.summarize_diff(diff_text, commit_messages)
    reviewers = [r.get("login") for r in pr.get("requested_reviewers", [])]

    status = "merged" if pr.get("merged") else item.get("status", "backfilled")

    new_item = {
        "pr_id": pr_id,
        "repo": repo,
        "pr_number": int(pr_number),
        "title": analysis.title,
        "summary": analysis.summary,
        "changes": json.dumps(analysis.changes),
        "impact": analysis.impact,
        "action_required": analysis.action_required,
        "labels": json.dumps(analysis.labels),
        "commit_messages": json.dumps(commit_messages),
        "created_at": pr.get("created_at"),
        "updated_at": pr.get("updated_at"),
        "status": status,
        "author": pr.get("user", {}).get("login"),
        "reviewers": json.dumps(reviewers),
    }

    if not apply:
        print(f"[dry-run] would backfill {pr_id}:")
        print(json.dumps(new_item, indent=2, default=str))
        return

    table.put_item(Item=new_item)
    print(f"backfilled {pr_id}")

    if update_github:
        changes_formatted = "\n- ".join(analysis.changes)
        full_summary = f"""### {analysis.title}

**Summary:** {analysis.summary}

**Changes:**
- {changes_formatted}

**Impact:** {analysis.impact}
**Action Required:** {analysis.action_required}"""
        github.update_pr_description(repo, pr_number, full_summary)
        github.add_pr_labels(repo, pr_number, analysis.labels)
        print(f"  also updated GitHub PR #{pr_number} description/labels")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="actually write to DynamoDB (default is dry-run)")
    parser.add_argument("--update-github", action="store_true", help="also re-patch the PR description/labels on GitHub")
    parser.add_argument("--limit", type=int, default=None, help="only process the first N sparse rows")
    parser.add_argument("--sleep", type=float, default=1.0, help="seconds to sleep between items (rate limiting)")
    args = parser.parse_args()

    items = find_sparse_items()
    if args.limit:
        items = items[: args.limit]

    print(f"found {len(items)} sparse row(s) in {TABLE_NAME}")

    failures = []
    for i, item in enumerate(items, 1):
        pr_id = item.get("pr_id")
        print(f"[{i}/{len(items)}] {pr_id} ({item.get('repo')})")
        try:
            backfill_item(item, apply=args.apply, update_github=args.update_github)
        except Exception as e:
            print(f"  FAILED: {e}")
            failures.append((pr_id, str(e)))
        if i < len(items):
            time.sleep(args.sleep)

    if failures:
        print(f"\n{len(failures)} item(s) failed:")
        for pr_id, err in failures:
            print(f"  {pr_id}: {err}")


if __name__ == "__main__":
    main()

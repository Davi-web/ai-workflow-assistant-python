import json
import logging
from utils import github, openai_utils
from pydantic import BaseModel
import boto3
from datetime import datetime
import os



class PRAnalysis(BaseModel):
    title: str
    summary: int
    changes: list[str]
    impact: str
    action_required: str
    labels: list[str] 

logger = logging.getLogger()
logger.setLevel(logging.INFO)

table_name = os.getenv("DYNAMODB_TABLE", "PRSummaries")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(table_name)

def handler(event, context):
    body = event.get("body")
    if not body:
        return {"statusCode": 400, "body": "No payload provided"}

    payload =  body if isinstance(body, dict) else json.loads(body)
    action = payload.get("action")
    if action not in ["opened", "synchronize", "reopened"]:
        return {"statusCode": 200, "body": json.dumps({"status": "ignored"})}

    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {}).get("full_name")
    pr_number = pr.get("number")
    diff_url = pr.get("diff_url")
    pr_id = str(pr.get("id")) + "-" + str(pr_number)
    author = pr.get("user", {}).get("login")
    reviewers = [r.get("login") for r in pr.get("requested_reviewers", [])]

    logger.info(f"Processing PR {pr_number} in {repo}, {diff_url}")

    try:
        diff_text = github.get_pr_diff(diff_url)
        commit_messages = github.get_pr_commits(repo, pr_number)
        analysis: PRAnalysis = openai_utils.summarize_diff(diff_text, commit_messages)

        full_summary = f"""### {analysis.title}

**Summary:** {analysis.summary}

**Changes:**
- {"\n- ".join(analysis.changes)}

**Impact:** {analysis.impact}
**Action Required:** {analysis.action_required}"""

        github.update_pr_description(repo, pr_number, full_summary)
        github.add_pr_labels(repo, pr_number, analysis.labels)
        table.put_item(Item={
            "pr_id": pr_id,                  # Unique PR identifier
            "repo": repo,                           # Repository name
            "pr_number": pr_number,                 # PR number
            "title": analysis.title,         # PR title
            "summary": analysis.summary,     # Short summary
            "changes": json.dumps(analysis.changes),  # List of changed files
            "impact": analysis.impact,       # Which parts of the codebase are affected
            "action_required": analysis.action_required, # What reviewers should do
            "label": json.dumps(analysis.labels),         # Bug / Feature / Docs / etc.
            "commit_messages": json.dumps(commit_messages), # List of commit messages
            "created_at": datetime.utcnow().isoformat(),  # PR creation timestamp
            "updated_at": datetime.utcnow().isoformat(),  # Last updated timestamp
            "status": action,                       # open / closed / merged
            "author": author,                        # PR author
            "reviewers": json.dumps(reviewers)       # List of reviewers
        })

    except Exception as e:
        logger.error(f"Error processing PR: {e}")
        return {"statusCode": 500, "body": str(e)}

    return {"statusCode": 200, "body": json.dumps({"status": "ok"})}

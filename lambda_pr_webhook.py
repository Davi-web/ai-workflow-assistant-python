import json
import logging
from utils import github, openai_utils
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
import os


class PRAnalysis(BaseModel):
    title: str
    summary: str
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

    payload = body if isinstance(body, dict) else json.loads(body)
    action = payload.get("action")

    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {}).get("full_name")
    pr_number = pr.get("number")
    diff_url = pr.get("diff_url")
    commit_url = pr.get("commits_url")
    pr_id = f"{pr.get('id')}-{pr_number}"
    author = pr.get("user", {}).get("login")
    reviewers = [r.get("login") for r in pr.get("requested_reviewers", [])]
    pr_created_at = pr.get("created_at")
    pr_updated_at = pr.get("updated_at")

    logger.info(f"Processing PR {pr_number} in {repo}, action={action}")

    try:
        if action == "closed" and pr.get("merged") is True:
            try:
                table.update_item(
                    Key={"pr_id": pr_id, "repo": repo},
                    UpdateExpression="SET updated_at = :updated_at, #s = :status",
                    ConditionExpression="attribute_exists(pr_id)",
                    ExpressionAttributeNames={"#s": "status"},
                    ExpressionAttributeValues={
                        ":updated_at": pr_updated_at,
                        ":status": "merged",
                    },
                )
            except ClientError as e:
                if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
                    raise
                logger.warning(
                    f"No existing record for {pr_id}, skipping merged-status update"
                )
            logger.info(f"PR was merged, skipping analysis: {pr_id}")
            return {"statusCode": 200, "body": json.dumps({"status": "merged"})}

        allowed_actions = {"opened", "synchronize", "reopened"}
        if action not in allowed_actions:
            logger.info(f"Skipping analysis for action: {action}, {pr_id}")
            return {"statusCode": 200, "body": json.dumps({"status": "ignored"})}

        commit_messages = github.get_pr_commits(commit_url)

        logger.info("Continuing with PR analysis")
        diff_text = github.get_pr_diff(diff_url)
        analysis: PRAnalysis = openai_utils.summarize_diff(diff_text, commit_messages)

        changes_formatted = "\n- ".join(analysis.changes)
        full_summary = f"""### {analysis.title}

**Summary:** {analysis.summary}

**Changes:**
- {changes_formatted}

**Impact:** {analysis.impact}
**Action Required:** {analysis.action_required}"""

        github.update_pr_description(repo, pr_number, full_summary)
        github.add_pr_labels(repo, pr_number, analysis.labels)

        table.put_item(
            Item={
                "pr_id": pr_id,
                "repo": repo,
                "pr_number": pr_number,
                "title": analysis.title,
                "summary": analysis.summary,
                "changes": json.dumps(analysis.changes),
                "impact": analysis.impact,
                "action_required": analysis.action_required,
                "labels": json.dumps(analysis.labels),
                "commit_messages": json.dumps(commit_messages),
                "created_at": pr_created_at,
                "updated_at": pr_updated_at,
                "status": action,
                "author": author,
                "reviewers": json.dumps(reviewers),
            }
        )

    except Exception as e:
        logger.error(f"Error processing PR: {e}", exc_info=True)
        return {"statusCode": 500, "body": str(e)}

    return {"statusCode": 200, "body": json.dumps({"status": "ok"})}
import json
import logging
from utils import github, openai_utils
from pydantic import BaseModel

class PRAnalysis(BaseModel):
    title: str
    summary: int
    changes: str
    impact: str
    action_required: str
    labels: list[str] 

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    body = event.get("body")
    if not body:
        return {"statusCode": 400, "body": "No payload provided"}

    payload =  body if isinstance(body, dict) else json.loads(body)
    action = payload.get("action")
    if action not in ["opened", "synchronize"]:
        return {"statusCode": 200, "body": json.dumps({"status": "ignored"})}

    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {}).get("full_name")
    pr_number = pr.get("number")
    diff_url = pr.get("diff_url")

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

    except Exception as e:
        logger.error(f"Error processing PR: {e}")
        return {"statusCode": 500, "body": str(e)}

    return {"statusCode": 200, "body": json.dumps({"status": "ok"})}

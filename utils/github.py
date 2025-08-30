import requests
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def get_pr_diff(diff_url: str) -> str:
    resp = requests.get(diff_url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    resp.raise_for_status()
    return resp.text

def get_pr_commits(commit_url: str) -> list[str]:
    """Fetch commit messages for a PR."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(commit_url, headers=headers)
    resp.raise_for_status()
    commits = resp.json()
    return [c["commit"]["message"] for c in commits]

def update_pr_description(repo: str, pr_number: int, body: str):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    resp = requests.patch(
        url,
        json={"body": body},
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }
    )
    resp.raise_for_status()

def add_pr_labels(repo: str, pr_number: int, labels: list):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels"
    resp = requests.post(
        url,
        json={"labels": labels},
        headers={"Authorization": f"token {GITHUB_TOKEN}"}
    )
    resp.raise_for_status()

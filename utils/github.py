import requests
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def get_pr_diff(pr_url: str) -> str:
    diff_url = pr_url + ".diff"
    resp = requests.get(diff_url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    resp.raise_for_status()
    return resp.text

def get_pr_commits(repo: str, pr_number: int) -> list[str]:
    """Fetch commit messages for a PR."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/commits"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
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

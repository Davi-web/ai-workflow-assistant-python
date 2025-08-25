import os
from pydantic import BaseModel
from openai import OpenAI
import instructor

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = instructor.from_openai(OpenAI(api_key=OPENAI_API_KEY))

class PRAnalysis(BaseModel):
    title: str
    summary: str
    changes: list[str]
    impact: str
    action_required: str
    labels: list[str]  # singular to match your JSON

def summarize_diff(diff: str, commits: list[str]) -> PRAnalysis:
    commit_messages = "\n".join(f"- {c}" for c in commits)
    print(commit_messages)
    response = client.chat.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": """
You are an AI assistant summarizing GitHub pull requests. I will give you the pr commit messages and the pr diff and you are to analyze what changed in the project and summarize these fields for me.
Return the result ONLY in this strict JSON format:

{
  "title": "<one line summary>",
  "summary": "<brief non-technical description>",
  "changes": ["changed <filename with extension>", ...],
  "impact": "<affected parts>",
  "action_required": "<what reviewers should do>",
  "labels": "[<Bug | Feature | Docs | etc.>, <Small Size | Medium Size | Large Size>]"
}

"""},{"role" : "user", "content": f"Here is the PR diff:\n{diff}\nHere are the commit messages:\n{commit_messages}"}],
        response_model=PRAnalysis,
    )
    print(response)

    return response
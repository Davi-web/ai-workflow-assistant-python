# GitHub Pull Request Review Assistant

## Project Overview
The GitHub Pull Request Review Assistant is an automated system that analyzes pull requests in real-time and generates concise, AI-powered summaries with actionable insights. The assistant also labels PRs automatically based on their content, helping teams streamline code review and maintain high-quality standards.

This project showcases full-stack development skills, integrating serverless backend processing with AI models and a planned React dashboard for visualization.

---

## Features
- **Automated PR Analysis:** Parses GitHub PR diffs and commit messages to summarize changes, assess impact, and recommend reviewer actions.
- **AI-Powered Summaries:** Uses OpenAI's GPT models (via Instructor) to generate structured JSON summaries.
- **Labeling System:** Automatically assigns labels like Bug, Feature, or Docs based on PR content.
- **Serverless Architecture:** Backend powered by Python, AWS Lambda, and API Gateway.
- **Extensible Frontend (Planned):** React dashboard to view PR summaries, filter by labels, and explore commit details.

---

## Tech Stack
- **Backend:** Python 3.11, AWS Lambda, API Gateway
- **AI Integration:** OpenAI GPT models with Instructor and Pydantic for structured outputs
- **Webhooks:** GitHub webhooks to trigger analysis on PR events
- **Database (Planned):** PostgreSQL or DynamoDB for storing PR analysis
- **Frontend (Planned):** React, Tailwind CSS / shadcn/ui for dashboard visualization

---

## Getting Started

This project is deployed as an AWS Lambda function, triggered by GitHub webhooks. To set up or update the Lambda function:

1. **Prepare your Python environment**  
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. **Package the Lambda function**
   ```
   # Make a folder for dependencies
   mkdir package
   pip install -r requirements.txt --target ./package --no-cache-dir


   # Copy Lambda function and utils
   cp lambda_pr_webhook.py package/
   cp -r utils package/

   # Zip everything
   cd package
   zip -r ../lambda_pr_webhook.zip .
   cd ..
   # Upload lambda_pr_webhook into lambda
 cp lambda_pr_webhook.zip /mnt/c/Users/David/Coding/ai-workflow-assistant-python
   ```

---

## Backfilling Sparse DynamoDB Rows

`DynamoDB.update_item` upserts by default — if the webhook receives a non-analyzed
action (e.g. `labeled`, `assigned`, or `closed`+merged) before a full analysis has
ever been written for that PR, it creates a sparse item with only `status`/`updated_at`
set, leaving `author`, `title`, `pr_number`, `changes`, and `created_at` null.
`backfill_sparse_rows.py` finds those rows, re-fetches the PR from GitHub, re-runs
the same analysis the webhook does, and writes the complete record back.

1. **Set up your Python environment** (a venv built on Windows won't run under WSL,
   and vice versa — make sure you're consistently using one or the other):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Create a `.env` with the required credentials**
   ```bash
   cp .env.example .env
   # then fill in GITHUB_TOKEN, OPENAI_API_KEY, DYNAMODB_TABLE,
   # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
   ```

3. **Dry run first** — scans the table and prints what each sparse row would be
   backfilled to, without writing anything:
   ```bash
   set -a; source .env; set +a
   python backfill_sparse_rows.py
   ```

4. **Test on a couple of real rows**
   ```bash
   python backfill_sparse_rows.py --apply --limit 2
   ```

5. **Run the full backfill**
   ```bash
   python backfill_sparse_rows.py --apply
   ```
   Add `--update-github` if you also want it to re-patch the PR's description and
   labels on GitHub — off by default since it re-edits already-merged/closed PRs.

   Useful flags: `--limit N` (process only the first N sparse rows), `--sleep S`
   (seconds between items, default `1.0`, for API rate limiting).

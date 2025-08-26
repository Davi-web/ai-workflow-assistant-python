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
# Make a folder for dependencies
mkdir package
pip install -r requirements.txt --target ./package

# Copy Lambda function and utils
cp lambda_function.py package/
cp -r utils package/

# Zip everything
cd package
zip -r ../lambda_package.zip .
cd ..

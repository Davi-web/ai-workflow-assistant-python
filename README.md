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

1. **Clone the Repository**
```bash
git clone https://github.com/your-username/ai-pr-review-assistant.git
cd ai-pr-review-assistant

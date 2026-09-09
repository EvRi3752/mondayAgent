"""
Monday - AI agent built for reminding me to do Leetcode questions on a daily basis..
----------------------------

Pulls rows from my Notion databse and sends me a reminder to do 2 - 3 Leetcode questions 
on a daily basis.

"""

import os
import random
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

import requests
from dotenv import load_dotenv

load_dotenv()

# Configuration

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID") or os.environ.get("DATABASE_ID")

# Property names

PROP_TITLE = os.environ.get("PROP_NAME") or os.environ.get("PROP_TITLE", "name")
PROP_JAVA = os.environ.get("PROP_JAVA", "java")
PROP_CONCEPTS = os.environ.get("PROP_CONCEPTS", "concepts")
PROP_SOLVED_DATE = os.environ.get("PROP_DATE_SOLVED") or os.environ.get("PROP_SOLVED_DATE", "date solved")
PROP_NEEDS_REVIEW = os.environ.get("PROP_NEEDS_REVIEW", "needs review !!")
PROP_TIMES_SOLVED = os.environ.get("PROP_NOT_SOLVED") or os.environ.get("PROP_TIMES_SOLVED", "num times solved")
REVIEW_AFTER_DAYS = int(os.environ.get("REVIEW_AFTER_DAYS", "2"))

PROP_DIFFICULTY = os.environ.get("PROP_LEVEL") or os.environ.get("PROP_DIFFICULTY", "level")
PROP_URL = os.environ.get("PROP_QLINK") or os.environ.get("PROP_URL", "q link")
PROP_SUMMARY = os.environ.get("PROP_SUMMARY", "summary")
PROP_TIME_TAKEN = os.environ.get("PROP_TT") or os.environ.get("PROP_TIME_TAKEN", "time taken")
 
QUESTIONS_PER_DAY = int(os.environ.get("QUESTIONS_PER_DAY", "2"))  # 1-3 recommended
 
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]  # app password, not your normal password
TO_EMAIL = os.environ.get("TO_EMAIL", EMAIL_ADDRESS)
 
NOTION_API_URL = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# Notion query

def fetch_all_rows():
    """Fetch every row from the database, handling pagination."""
    rows = []
    payload = {}
    while True:
        resp = requests.post(NOTION_API_URL, headers=NOTION_HEADERS, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        rows.extend(data["results"])
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]
    return rows
 
 
def extract_text(prop):
    """Pull plain text out of a Notion title/rich_text property."""
    if not prop:
        return ""
    kind = prop.get("type")
    parts = prop.get(kind, [])
    return "".join(p.get("plain_text", "") for p in parts)
 
 
def extract_select(prop):
    if not prop or not prop.get("select"):
        return ""
    return prop["select"].get("name", "")
 
 
def extract_url(prop):
    if not prop:
        return ""
    return prop.get("url") or ""


def extract_date(prop):
    if not prop or not prop.get("date"):
        return ""
    return prop["date"].get("start") or ""


def extract_checkbox(prop):
    return bool(prop and prop.get("checkbox"))


def extract_number(prop):
    if not prop:
        return None
    return prop.get("number")
 
 
def row_to_problem(row):
    props = row["properties"]
    return {
        "title": extract_text(props.get(PROP_TITLE)) or "(untitled)",
        "java": props.get(PROP_JAVA),
        "concepts": extract_text(props.get(PROP_CONCEPTS)),
        "solved_date": extract_date(props.get(PROP_SOLVED_DATE)),
        "needs_review": extract_checkbox(props.get(PROP_NEEDS_REVIEW)),
        "times_solved": extract_number(props.get(PROP_TIMES_SOLVED)),
        "difficulty": extract_select(props.get(PROP_DIFFICULTY)),
        "url": extract_url(props.get(PROP_URL)),
        "summary": extract_text(props.get(PROP_SUMMARY)),
        "time_taken": extract_number(props.get(PROP_TIME_TAKEN)),
    }


def is_ready_for_review(problem, now=None):
    """Return whether a completed problem has reached its review date."""
    if not problem["solved_date"]:
        return False
    try:
        solved_at = datetime.fromisoformat(problem["solved_date"].replace("Z", "+00:00"))
    except ValueError:
        return False
    if solved_at.tzinfo is None:
        solved_at = solved_at.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
    return solved_at <= now - timedelta(days=REVIEW_AFTER_DAYS)
 
 
def pick_daily_problems():
    rows = fetch_all_rows()
    problems = [row_to_problem(r) for r in rows]
 
    unsolved = [
        problem
        for problem in problems
        if not problem["solved_date"] or is_ready_for_review(problem)
    ]
 
    if not unsolved:
        return []
 
    count = min(QUESTIONS_PER_DAY, len(unsolved))
    return random.sample(unsolved, count)

# Email

def build_email_body(problems):
    if not problems:
        return "No unsolved problems left in your LeetCode Study Hub. Time to add more!"
 
    lines = ["Here are your LeetCode problems for today:\n"]
    for i, p in enumerate(problems, start=1):
        line = f"{i}. {p['title']}"
        if p["difficulty"]:
            line += f" ({p['difficulty']})"
        lines.append(line)
        if p["url"]:
            lines.append(f"   {p['url']}")
        lines.append("")
    return "\n".join(lines)
 
 
def send_email(body):
    msg = MIMEText(body)
    msg["Subject"] = "Your daily LeetCode problems"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = TO_EMAIL
 
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, [TO_EMAIL], msg.as_string())


def send_test_email():
    """Verify SMTP connection and credentials without querying Notion."""
    send_email("This is a test email from mondayAgent. SMTP is working.")
    print(f"Test email sent successfully to {TO_EMAIL}.")

# Main

def main():
    if "--test-email" in sys.argv:
        try:
            send_test_email()
        except (OSError, smtplib.SMTPException) as e:
            print(f"Email test failed: {e}", file=sys.stderr)
            sys.exit(1)
        return

    try:
        problems = pick_daily_problems()
    except requests.HTTPError as e:
        print(f"Notion API error: {e.response.status_code} {e.response.text}", file=sys.stderr)
        sys.exit(1)
 
    body = build_email_body(problems)
    send_email(body)
    print("Email sent:")
    print(body)
 
 
if __name__ == "__main__":
    main()
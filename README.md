# mondayAgent
Simple agent that reminds me to do LeetCode questions.

Completed questions are scheduled for spaced repetition. A completed question is
eligible again after `REVIEW_AFTER_DAYS` days from `date solved`.

Required Notion setup:

- Use the configured property names: `name`, `java`, `concepts`, `date solved`,
  `level`, `needs review !!`, `num times solved`, `q link`, `summary`, and
  `time taken`.
- Set that date when a question is completed.

Optional environment variables:

- `PROP_SOLVED_DATE`: solved-date property name, default `date solved`
- `REVIEW_AFTER_DAYS`: delay before review, default `2`

## GitHub Actions

The daily reminder runs from `.github/workflows/daily-reminder.yml` at 13:00 UTC.
It can also be started manually from the Actions tab with **Run workflow**.

Add these repository secrets under **Settings > Secrets and variables > Actions**:

- `NOTION_TOKEN`
- `NOTION_DATABASE_ID`
- `EMAIL_ADDRESS`
- `EMAIL_PASSWORD` (an SMTP app password)
- `TO_EMAIL`

The workflow uses Gmail SMTP by default. Set optional configuration as repository
variables or add matching secrets and expose them in the workflow if your Notion
property names or schedule differ.

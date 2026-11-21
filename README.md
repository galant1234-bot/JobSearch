# Job search agent (Tel Aviv district)

Scheduled Claude session that searches for senior technical support / customer success jobs,
scores them against agent/profile.md, and emails an alert for new, fresh, high-scoring jobs.

- agent/profile.md: candidate profile and constraints (edit to change targeting)
- agent/search_prompt.md: run instructions, scoring and alert rules
- state/seen.json: jobs already evaluated (prevents duplicate alerts)
- digests/: daily markdown digests

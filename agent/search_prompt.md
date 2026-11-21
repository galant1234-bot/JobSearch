# Job search run instructions

Goal: find NEW, still-open jobs matching agent/profile.md and alert the candidate fast.
Freshness is the top priority.

## Steps
1. Read agent/profile.md and state/seen.json (list of already-reported job URLs/ids).
2. Search (WebSearch, standard mode) for each target title, English and Hebrew, with
   "Tel Aviv" / district cities. Cover: comeet.com, lever.co, workable.com, greenhouse.io,
   ashbyhq.com, alljobs.co.il, drushim.co.il, jobmaster.co.il, linkedin.com/jobs (snippets only),
   indeed/glassdoor (snippets only), and company career pages. Use several query phrasings,
   e.g. "posted today", "hiring now", "דרושים".
3. For every candidate not in seen.json, fetch the posting page (WebFetch/curl):
   - Confirm it is OPEN (redirect to company page, 404, "no longer accepting" = closed, skip).
   - Extract the publish date: JSON-LD `datePosted`, "Posted N days ago", page text, or search
     snippet date. If no date can be found, mark date="unknown" and treat as lower freshness.
4. Score 0-100:
   - Role fit (title/scope matches target roles): 0-35
   - Skills/domain fit (API, SQL, escalation, integrations, logs): 0-30
   - Seniority fit (senior/lead; penalise junior): 0-15
   - Location/work-mode fit: 0-10
   - Freshness: <=1 day +10, <=3 days +7, <=7 days +4, <=14 days +2, older/unknown 0
   Hard rejects: closed, outside Tel Aviv district (non-remote), junior/Tier 1 only,
   unrelated to the candidate's experience.
5. Classes: score >= 75 "strong", 60-74 "stretch". Anything below 60 is dropped.
6. ALERT rule: a job is alerted immediately if it is new (not in seen.json), published within
   the last 3 days (or date unknown but first seen today and score >= 80), AND score >= 70.
   Send one email per run containing all new alerts (not one email per job), subject
   "Job alert: N new matches (top: <title> @ <company>)". Use the Gmail send_message tool.
   If Gmail is unavailable, write the alert to digests/ALERT-<timestamp>.md and say so.
7. Write digests/YYYY-MM-DD.md (append a section per run): table of all new matches with score,
   class, company, title, location, published date (age), link, one-line why it fits.
8. Update state/seen.json with every job evaluated (including rejected), keyed by URL, with
   first_seen date, score and decision. Commit and push to the working branch.
9. If nothing new qualifies, send no email; just log "no new matches" in the digest.

## Rules
- Never fabricate jobs, dates or links. Only report what a fetched page or search result shows.
- State uncertainty (e.g. "date unknown", "snippet only, could not verify open").
- LinkedIn/Indeed/Glassdoor block scraping: use search snippets only, do not circumvent blocks.

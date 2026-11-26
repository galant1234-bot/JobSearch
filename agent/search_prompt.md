# Job search run instructions

Goal: find NEW, still-open jobs matching agent/profile.md and alert the candidate fast.
Freshness is the top priority.

## Steps
1. FIRST run `python3 scripts/merge_state.py` (merges the seen-jobs lists that earlier runs pushed to
   their own claude/* branches), then read agent/profile.md and state/seen.json (already-evaluated jobs).
2. COMEET FIRST (most reliable source, includes dates): run `python3 scripts/comeet_scan.py`.
   It reads every company page in scripts/comeet_companies.txt, which embeds all positions with
   time_updated, location and workplace type, and prints relevant roles in the Tel Aviv district
   sorted by data. Ignore obvious false positives (legal, warehouse, sales). time_updated is the
   last update, not necessarily the first publication: say "updated N days ago" when unsure.
   MANDATORY, never skip: grow scripts/comeet_companies.txt. Each run do at least 3 WebSearch calls
   (allowed_domains comeet.com), then append new Israeli companies' URLs and commit them. Use WebSearch restricted to comeet.com
   (e.g. "Tel Aviv support engineer", "customer success Israel") to find new Israeli companies and
   append their https://www.comeet.com/jobs/<slug>/<uid> URL. (Comeet is also branded
   "Spark Hire Recruit".)
2a. FEENY (Israeli startup job aggregator, https://feeny.ai): run `python3 scripts/feeny_scan.py`.
   Its "Nd ago" label is the crawler's last-seen time, NOT the posting date. The script reports the
   real postedAt. Use postedAt for freshness. Only /job/ pages and sitemaps are used (robots.txt
   disallows query-string filters: never use them). 404 pages are removed jobs.
2b. Then ALWAYS also run WebSearch for the other sources below (do not skip; the digest must list what was searched):
 (WebSearch, standard mode) for each target title with "Tel Aviv" / district cities.
   ENGLISH ONLY: do not search in Hebrew. Tech-focused sources only:
   - Comeet-hosted career pages (comeet.com/jobs/...), Glassdoor (snippets only; it blocks scraping)
   - Company career pages and ATS boards used by Israeli tech companies
     (Greenhouse, Lever, Workable, Ashby) and Israeli VC/startup job boards
   - LinkedIn / Indeed (snippets only)
   Do NOT use general Israeli job boards (AllJobs, Drushim, JobMaster, Dialog, Jobnet): they are
   not tech-focused. SparkHire is not used (no Israeli tech relevance found).
   Use several phrasings, e.g. "hiring now", "posted today".
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
6. NEVER RE-ALERT: a job URL already in state/seen.json (whatever its decision) is never alerted or emailed again,
   even if Comeet shows a fresh time_updated or its score changed. (The Fullpath technical support role was
   alerted twice, on 2026-11-22 and 2026-11-24, because an edit made it look new.) Only mention such a
   job in the digest, with a note like "updated again". Match URLs by comeet company/position id, ignoring slug text.
   ALERT rule: a job is alerted immediately if it is new (not in seen.json), published within
   the last 3 days (or date unknown but first seen today and score >= 80), AND score >= 70.
   Send ONE email per run containing all new alerts (never one email per job).
   Subject: "Job alert: N new matches (top: <title> @ <company>)". Use Gmail send_message with
   `htmlBody` (not `body`, no Markdown). Format the email as follows, nothing else:
   - One short intro line (date/time of run, number of matches).
   - A single HTML table, styled simply (border-collapse, 1px borders, padding 8px, header row
     shaded), sorted by score descending, with exactly these columns:
       1. Job Title (job title in bold, company and location on a second line)
       2. Summary (2-3 sentences: what the role does, key requirements, why it fits the CV;
          include the posted age, e.g. "Posted 1 day ago")
       3. Score (number out of 100, add "strong" or "stretch")
       4. Link (a clickable "Open job" link to the job page itself, never a search or board page)
   - No other sections, lists or paragraphs. Items that could not be verified are not alerted.
   If Gmail is unavailable, write the same table to digests/ALERT-<timestamp>.md and say so.
7. Write digests/YYYY-MM-DD.md (append a section per run): table of all new matches with score,
   class, company, title, location, published date (age), link, one-line why it fits.
8. Update state/seen.json with every job evaluated (including rejected), keyed by URL, with
   first_seen date, score and decision. Commit and push to the working branch.
9. DAILY STATUS EMAIL (heartbeat, proves the agent is alive). It is sent ONLY at the end of the day and
   ONLY if no other email went out during the day:
   a. Get the Israel time with `TZ=Asia/Jerusalem date`. This step applies only to the LAST run of the day,
      i.e. a run that started at or after 21:00 Israel time. Earlier runs skip this step entirely and send
      only the normal alert email (step 6) when matches qualify.
   b. In that last run, first handle step 6 normally (alert email if matches qualify; then you are done,
      no status email is needed because an email was sent).
   c. Otherwise check whether ANY email from this agent was already sent today (Asia/Jerusalem date): use
      mcp__Gmail__search_threads with query
      `from:me (subject:"Job alert" OR subject:"Job agent" OR subject:"Relevant roles" OR subject:"Job matches") newer_than:1d`
      and compare dates in Israel time. If search_threads is unavailable, treat it as "no email sent today"
      only when this run found no alert-eligible matches.
   d. If no email was sent today, send ONE email: subject "Job agent daily status: OK, no new positions today"
      (or "Job agent daily status: PROBLEM" if anything is broken). Use htmlBody. Keep it short: a small
      table with: Run time (Israel), runs today (from the digest), Comeet companies scanned, Feeny scan
      (ok/failed), web searches run, jobs evaluated today, new jobs found today, problems (scanner errors,
      blocked sites, missing tools, or "none").
   e. If an email was already sent today, send nothing.
10. Runs are scheduled Sunday to Friday, so no status email is expected on Saturday. If a weekday has NO
    email at all, the agent did not run to completion or could not send email.

#!/usr/bin/env python3
"""Union state/seen.json from every remote claude/* branch into the working copy.

Scheduled runs push to their own random claude/* branch, so each run starts without the previous
run's seen-jobs list. Run this FIRST in every run to avoid duplicate alerts.
"""
import json, subprocess

def sh(*a):
    return subprocess.run(a, capture_output=True, text=True).stdout

subprocess.run(["git", "fetch", "-q", "origin", "+refs/heads/claude/*:refs/remotes/origin/claude/*"])
merged = {}
try:
    merged.update(json.load(open("state/seen.json")).get("seen", {}))
except Exception:
    pass
for ref in sh("git", "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin/claude/").split():
    try:
        seen = json.loads(sh("git", "show", f"{ref}:state/seen.json")).get("seen", {})
    except Exception:
        continue
    for url, rec in seen.items():
        if url not in merged or str(rec.get("first_seen", "")) < str(merged[url].get("first_seen", "9999")):
            merged[url] = rec if url not in merged else merged[url]
# also union the Comeet company list that runs append to on their own branches
lines = set()
try:
    lines |= {l.strip() for l in open("scripts/comeet_companies.txt") if l.strip()}
except Exception:
    pass
for ref in sh("git", "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin/claude/").split():
    lines |= {l.strip() for l in sh("git", "show", f"{ref}:scripts/comeet_companies.txt").splitlines() if l.strip()}
def key(u):
    return u.split("/jobs/")[-1].lower().split("/")[0]
byslug = {}
for u in sorted(lines):
    byslug.setdefault(key(u) if "/jobs/" in u else u, u)
open("scripts/comeet_companies.txt", "w").write("\n".join(byslug.values()) + "\n")
print(f"merged comeet_companies.txt: {len(byslug)} companies")
json.dump({"seen": merged}, open("state/seen.json", "w"), indent=1)
print(f"merged seen.json: {len(merged)} jobs")

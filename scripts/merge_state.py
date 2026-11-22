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
json.dump({"seen": merged}, open("state/seen.json", "w"), indent=1)
print(f"merged seen.json: {len(merged)} jobs")

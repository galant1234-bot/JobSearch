#!/usr/bin/env python3
"""Scan Comeet company career pages for relevant, recent positions in the Tel Aviv district.

Usage: python3 scripts/comeet_scan.py [companies.txt]   (one comeet.com/jobs/<slug>/<uid> URL per line)
Prints JSON lines: company, title, location, workplace, updated, age_days, url.
Comeet embeds all positions (with time_updated) in COMPANY_POSITIONS_DATA on the company page.
"""
import json, re, ssl, sys, urllib.request
from datetime import datetime, timezone

ROLE = re.compile(r"support|success|escalation|solutions? engineer|implementation|integration|technical account|customer engineer|deployment|onboarding", re.I)
JUNIOR = re.compile(r"\b(junior|intern|student|entry|tier ?1)\b", re.I)
CITIES = re.compile(r"tel[ -]?aviv|ramat[ -]?gan|givatayim|bnei[ -]?brak|holon|bat[ -]?yam|herzliya|petah|petach|or yehuda|kiryat ono|rishon|yafo|jaffa", re.I)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30, context=ssl.create_default_context()).read().decode("utf-8", "ignore")

def positions(url):
    t = fetch(url)
    key = "COMPANY_POSITIONS_DATA = "
    i = t.find(key)
    if i < 0:
        return []
    return json.JSONDecoder().raw_decode(t[i + len(key):])[0] or []

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "scripts/comeet_companies.txt"
    now = datetime.now(timezone.utc)
    for line in open(path):
        url = line.split("#")[0].strip()
        if not url:
            continue
        try:
            pos = positions(url)
        except Exception as e:
            print(json.dumps({"company_url": url, "error": str(e)[:100]})); continue
        for p in pos:
            loc = p.get("location") or {}
            locs = json.dumps(loc, ensure_ascii=False)
            title = p.get("name", "")
            if not (ROLE.search(title) and CITIES.search(locs)):
                continue
            upd = p.get("time_updated") or ""
            try:
                age = (now - datetime.fromisoformat(upd.replace("Z", "+00:00"))).days
            except Exception:
                age = None
            print(json.dumps({"company": p.get("company_name"), "title": title, "junior_flag": bool(JUNIOR.search(title)),
                              "location": loc.get("name") if isinstance(loc, dict) else loc,
                              "workplace": p.get("workplace_type"), "updated": upd, "age_days": age,
                              "url": p.get("url_comeet_hosted_page")}, ensure_ascii=False))

if __name__ == "__main__":
    main()

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
# Data-leadership track (data quality / data operations / annotation / analytics team leads); NOT data engineering or infra/biz ops
DATA_ROLE = re.compile(r"data[ -]?(operations?|ops|quality|annotation|labell?ing|services|support|delivery|governance|management)|analytics? (team|manager|lead|operations?)|(team lead|manager|head).{0,20}\bdata\b|\bdata\b.{0,20}(team lead|manager|head of)|kpi|annotation|labell?ing|insights? (team|manager)", re.I)
DATA_LEAD = re.compile(r"lead|manager|head|senior|director|supervisor", re.I)
DATA_EXCL = re.compile(r"data cent(er|re)|project manager|hardware|data engineer|etl|mlops|devops|platform|software|backend|full[ -]?stack|security|scientist|researcher|bizops|biz ops|sales ops|revops|marketing ops|it ops|network|student|intern|analyst$|dba|database admin", re.I)
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
            track = "support"
            if not CITIES.search(locs):
                continue
            if not ROLE.search(title):
                if DATA_ROLE.search(title) and DATA_LEAD.search(title) and not DATA_EXCL.search(title):
                    track = "data"
                else:
                    continue
            upd = p.get("time_updated") or ""
            try:
                age = (now - datetime.fromisoformat(upd.replace("Z", "+00:00"))).days
            except Exception:
                age = None
            print(json.dumps({"company": p.get("company_name"), "title": title, "track": track, "junior_flag": bool(JUNIOR.search(title)),
                              "location": loc.get("name") if isinstance(loc, dict) else loc,
                              "workplace": p.get("workplace_type"), "updated": upd, "age_days": age,
                              "url": p.get("url_comeet_hosted_page")}, ensure_ascii=False))

if __name__ == "__main__":
    main()

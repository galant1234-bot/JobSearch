#!/usr/bin/env python3
"""Scan feeny.ai for relevant Tel Aviv-district jobs, using only robots-allowed pages (sitemaps, /job/ pages).

Feeny's visible "Nd ago" is when its crawler last saw the job (lastSeenAt). The real posting date is
postedAt in the page payload, so this script reports postedAt as the age. Pages that 404 are removed jobs.
Prints JSON lines: title, company_location, age_days (from postedAt), last_seen, valid_through, url.
"""
import json, re, sys, time, urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0"}
AREA = re.compile(r"tel-aviv|israel|ramat-gan|herzliya|petah-tikva|givatayim|bnei-brak|holon|rishon")
ROLE = re.compile(r"data-operations?|data-ops|data-quality|data-annotation|annotation|labell?ing|data-services|data-delivery|analytics-(team|manager|operations)|team-lead.*data|data.*(team-lead|manager|lead)|support|success-engineer|escalation|solutions?-engineer|implementation|technical-account|customer-engineer|deployment")
SKIP = re.compile(r"data-engineer|etl|mlops|devops|data-scientist|software|backend|platform-engineer|bizops|revops|it-support|product-manager|full-stack|data-engineer|fp-a|field-technical|sales|account-executive|marketing|legal|recruit")

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode("utf-8", "ignore")

def main(max_age=None):
    urls = []
    for i in range(6):
        try:
            urls += re.findall(r"<loc>([^<]+)</loc>", get(f"https://feeny.ai/sitemap/{i}.xml"))
        except Exception as e:
            print(json.dumps({"error": f"sitemap {i} failed: {e}"[:150]}), file=sys.stderr)
    if not urls:
        sys.exit("feeny sitemaps unreachable: no results (not an empty result)")
    jobs = [u for u in urls if "/job/" in u]
    rel = [u for u in jobs if AREA.search(u.split("/job/")[1]) and ROLE.search(u.split("/job/")[1]) and not SKIP.search(u.split("/job/")[1])]
    now = datetime.now(timezone.utc)
    for u in rel:
        try:
            t = get(u)
        except Exception:
            continue  # 404 = job removed
        title = re.findall(r"<title>(.*?)</title>", t, re.S)[0].replace(" | Feeny", "")
        pa = re.search(r'\\"postedAt\\":\\"([^"\\]+)', t); ls = re.search(r'\\"lastSeenAt\\":\\"([^"\\]+)', t)
        vt = re.search(r'"validThrough":"([^"]+)"', t)
        age = (now - datetime.fromisoformat(pa.group(1).replace("Z", "+00:00"))).days if pa else None
        if max_age is not None and age is not None and age > max_age:
            continue
        print(json.dumps({"title": title, "age_days": age, "posted": pa.group(1)[:10] if pa else None,
                          "last_seen": ls.group(1)[:10] if ls else None,
                          "valid_through": vt.group(1)[:10] if vt else None, "url": u}, ensure_ascii=False))
        time.sleep(1.5)

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)

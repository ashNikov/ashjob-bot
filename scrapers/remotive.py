"""Remotive scraper — devops category, filtered through both gates."""
import requests
from matcher import passes, is_relevant, is_geo_ok

FEED_URL = "https://remotive.com/api/remote-jobs?category=devops"
HEADERS = {"User-Agent": "ashjob-bot/0.1 (personal job search; s.uwemudo@gmail.com)"}


def fetch():
    resp = requests.get(FEED_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    jobs = []
    for j in resp.json().get("jobs", []):
        jobs.append({
            "title": j.get("title", ""),
            "company": j.get("company_name", ""),
            "location": j.get("candidate_required_location") or "",
            "tags": j.get("tags", []),
            "url": j.get("url", ""),
            "source": "Remotive",
        })
    return jobs


def fetch_relevant():
    return [j for j in fetch() if passes(j["title"], j["tags"], j["location"])]


if __name__ == "__main__":
    all_jobs = fetch()
    kept = fetch_relevant()

    print(f"Remotive — fetched: {len(all_jobs)} | passed both gates: {len(kept)}")
    print("=" * 60)
    print("KEPT (relevant + open to you):\n")
    for j in kept:
        print(f"  ✅ {j['title']} @ {j['company']}")
        print(f"     location: {j['location']}")
        print(f"     {j['url']}\n")

    print("=" * 60)
    print("DROPPED (and why):\n")
    for j in all_jobs:
        if j in kept:
            continue
        rel = is_relevant(j["title"], j["tags"])
        geo = is_geo_ok(j["location"])
        reason = []
        if not rel:
            reason.append("not-devops")
        if not geo:
            reason.append(f"geo-blocked ({j['location'] or 'unknown'})")
        print(f"  ❌ {j['title'][:45]:45} | {', '.join(reason)}")

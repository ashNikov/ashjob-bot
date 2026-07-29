"""RemoteOK scraper — fetches jobs, uses shared matcher for relevance."""
import requests
from matcher import is_relevant_strict, is_geo_ok, is_fresh

FEED_URL = "https://remoteok.com/api"
HEADERS = {"User-Agent": "ashjob-bot/0.1 (personal job search; s.uwemudo@gmail.com)"}


def fetch():
    resp = requests.get(FEED_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    jobs = []
    for j in resp.json()[1:]:  # skip metadata element
        jobs.append({
            "title": j.get("position", ""),
            "company": j.get("company", ""),
            "location": j.get("location") or "Anywhere",
            "tags": j.get("tags", []),
            "url": j.get("url", ""),
            "source": "RemoteOK",
        })
    return jobs


def fetch_relevant():
    out = []
    for j in fetch():
        if (is_relevant_strict(j["title"])
                and is_geo_ok(j["location"])
                and is_fresh(j.get("posted", ""))):
            out.append(j)
    return out


if __name__ == "__main__":
    jobs = fetch_relevant()
    print(f"RemoteOK — relevant: {len(jobs)}\n" + "-" * 60)
    for j in jobs:
        print(f"{j['title']} @ {j['company']} | {j['location']}")
        print(f"  tags: {', '.join(j['tags'][:6])}")
        print(f"  {j['url']}\n")

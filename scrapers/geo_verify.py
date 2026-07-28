"""
Real-page geo verification (polite, with graceful fallback).
Feeds say 'Anywhere' but JDs often hide 'US work auth required'.
We try to fetch and check. If a site blocks bots (403) we DON'T spoof —
we flag the job 'verify-manually' so Uwem eyeballs it. Respects the block.
"""
import time
import requests

HEADERS = {"User-Agent": "ashjob-bot/0.1 (personal job search; s.uwemudo@gmail.com)"}
DELAY_SECONDS = 2.0

US_LOCK_PHRASES = [
    "authorized to work in the u", "us work authorization",
    "u.s. work authorization", "must reside in the united states",
    "must be located in the united states", "must be based in the us",
    "eligible to work in the united states", "us citizens only",
    "u.s. citizens only", "requires us citizenship", "green card",
    "must live in the us",
]


def verify_one(url: str) -> str:
    """Return 'ok', 'us-locked', 'verify-manually', or 'unverified'."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 403:
            return "verify-manually"   # site blocks bots — we respect it
        resp.raise_for_status()
        text = resp.text.lower()
        if any(p in text for p in US_LOCK_PHRASES):
            return "us-locked"
        return "ok"
    except requests.exceptions.HTTPError:
        return "verify-manually"
    except Exception:
        return "unverified"


def verify_jobs(jobs: list) -> list:
    for i, j in enumerate(jobs):
        j["geo_verified"] = verify_one(j["url"])
        if i < len(jobs) - 1:
            time.sleep(DELAY_SECONDS)
    return jobs


if __name__ == "__main__":
    import remotive, weworkremotely
    from matcher import seniority_bucket

    jobs = remotive.fetch_relevant() + weworkremotely.fetch_relevant()
    good = [j for j in jobs if seniority_bucket(j["title"]) == "good"]
    print(f"Verifying {len(good)} good-fit jobs...\n")

    verify_jobs(good)
    icons = {"ok": "✅", "us-locked": "❌",
             "verify-manually": "🔍", "unverified": "⚠️"}
    for j in good:
        print(f"  {icons[j['geo_verified']]} {j['geo_verified']:16} | "
              f"{j['title'][:38]} @ {j['company']}  [{j['source']}]")

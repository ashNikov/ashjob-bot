"""Orchestrator — scrape, filter, dedup, bucket by seniority."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scrapers"))

from tracker import filter_new
from matcher import seniority_bucket
import remotive, remoteok, weworkremotely

SOURCES = [
    ("Remotive", remotive.fetch_relevant),
    ("RemoteOK", remoteok.fetch_relevant),
    ("WeWorkRemotely", weworkremotely.fetch_relevant),
]


def main():
    all_relevant = []
    for name, fetch_fn in SOURCES:
        try:
            jobs = fetch_fn()
            print(f"  {name}: {len(jobs)} relevant")
            all_relevant.extend(jobs)
        except Exception as e:
            print(f"  {name}: ERROR — {e}")

    new_jobs = filter_new(all_relevant)
    for j in new_jobs:
        j["level"] = seniority_bucket(j["title"])

    good = [j for j in new_jobs if j["level"] == "good"]
    stretch = [j for j in new_jobs if j["level"] == "stretch"]
    dropped = [j for j in new_jobs if j["level"] == "drop"]

    print(f"\nNEW: {len(new_jobs)} | good: {len(good)} "
          f"stretch: {len(stretch)} drop: {len(dropped)}")
    print("=" * 60)
    print("🎯 GOOD FIT (your level):\n")
    for j in good:
        print(f"  {j['title']} @ {j['company']}")
        print(f"    {j['location']} [{j['source']}]\n    {j['url']}\n")
    print("🔶 STRETCH (senior — apply with eyes open):\n")
    for j in stretch:
        print(f"  {j['title']} @ {j['company']}  [{j['source']}]")
    print(f"\n(dropped {len(dropped)} over-level: Director/Manager/Staff/etc)")


if __name__ == "__main__":
    main()

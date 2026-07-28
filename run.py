"""
Orchestrator — runs all scrapers, filters, dedups.
This is the main entry point. Shows only NEW + relevant + geo-OK jobs.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scrapers"))

from tracker import filter_new
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

    print(f"\nTotal relevant across sources: {len(all_relevant)}")
    new_jobs = filter_new(all_relevant)
    print(f"NEW (not seen before): {len(new_jobs)}")
    print("=" * 60)
    for j in new_jobs:
        print(f"✅ {j['title']} @ {j['company']}")
        print(f"   {j['location']}  [{j['source']}]")
        print(f"   {j['url']}\n")


if __name__ == "__main__":
    main()

"""
Job tracker — the bot's memory.
Remembers every job seen (by unique id) so nothing surfaces twice.
Later grows into the full application log.
CSV lives at ../data/jobs.csv
"""
import csv
import os
import hashlib
from datetime import datetime

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "jobs.csv")

FIELDS = ["id", "first_seen", "source", "title", "company",
          "location", "url", "status"]


def job_id(job: dict) -> str:
    """Stable unique id from url (fallback: title+company)."""
    basis = job.get("url") or f"{job.get('title','')}|{job.get('company','')}"
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]


def _load_seen_ids() -> set:
    if not os.path.exists(CSV_PATH):
        return set()
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return {row["id"] for row in csv.DictReader(f)}


def _ensure_file():
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()


def filter_new(jobs: list) -> list:
    """Return only jobs we haven't recorded before, and record them."""
    _ensure_file()
    seen = _load_seen_ids()
    new_jobs = []
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        for j in jobs:
            jid = job_id(j)
            if jid in seen:
                continue
            seen.add(jid)
            new_jobs.append(j)
            writer.writerow({
                "id": jid,
                "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "source": j.get("source", ""),
                "title": j.get("title", ""),
                "company": j.get("company", ""),
                "location": j.get("location", ""),
                "url": j.get("url", ""),
                "status": "new",
            })
    return new_jobs


if __name__ == "__main__":
    # quick self-test
    sample = [{"url": "http://x.com/1", "title": "DevOps Eng",
               "company": "Acme", "location": "Africa", "source": "test"}]
    first = filter_new(sample)
    second = filter_new(sample)
    print(f"First run  (should be 1 new): {len(first)}")
    print(f"Second run (should be 0 new): {len(second)}")
    print(f"CSV written to: {os.path.abspath(CSV_PATH)}")

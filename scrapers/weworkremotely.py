"""WeWorkRemotely scraper — DevOps/sysadmin RSS feed."""
import requests
import xml.etree.ElementTree as ET
from matcher import passes

FEED_URL = "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss"
HEADERS = {"User-Agent": "ashjob-bot/0.1 (personal job search; s.uwemudo@gmail.com)"}


def fetch():
    resp = requests.get(FEED_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    jobs = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        # WWR titles look like "Company: Job Title"
        company = ""
        if ":" in title:
            company, title = title.split(":", 1)
            company, title = company.strip(), title.strip()
        region = (item.findtext("region") or "").strip()
        jobs.append({
            "title": title,
            "company": company,
            "location": region or "",
            "tags": [],
            "url": (item.findtext("link") or "").strip(),
            "source": "WeWorkRemotely",
        })
    return jobs


def fetch_relevant():
    return [j for j in fetch() if passes(j["title"], j["tags"], j["location"], j.get("posted",""))]


if __name__ == "__main__":
    jobs = fetch_relevant()
    print(f"WeWorkRemotely — relevant: {len(jobs)}")
    for j in jobs:
        print(f"  {j['title']} @ {j['company']} | {j['location'] or 'n/a'}")

"""MyJobMag scraper — Nigerian job board (HTML). Local DevOps/cloud roles."""
import requests
from bs4 import BeautifulSoup
from matcher import is_relevant, is_geo_ok, is_fresh

BASE = "https://www.myjobmag.com"
SEARCH = BASE + "/search/jobs?q=devops"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}


def fetch():
    resp = requests.get(SEARCH, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    jobs, seen = [], set()
    for a in soup.select('a[href*="/job/"]'):
        href = a.get("href", "")
        title = a.get_text(strip=True)
        if not title or href in seen:
            continue
        seen.add(href)
        # titles look like "DevOps Engineer at Company Name"
        company = ""
        if " at " in title:
            title, company = title.split(" at ", 1)
        jobs.append({
            "title": title.strip(),
            "company": company.strip(),
            "location": "Nigeria",   # MyJobMag is NG-based
            "tags": [],
            "url": BASE + href if href.startswith("/") else href,
            "posted": "",            # detail page has date; list doesn't — fail-open
            "source": "MyJobMag",
        })
    return jobs


def fetch_relevant():
    out = []
    for j in fetch():
        # NG board: local roles, so geo always ok; use normal relevance + freshness
        if is_relevant(j["title"], j["tags"]) and is_fresh(j.get("posted", "")):
            out.append(j)
    return out


if __name__ == "__main__":
    jobs = fetch_relevant()
    print(f"MyJobMag — relevant: {len(jobs)}")
    for j in jobs:
        print(f"  {j['title']} @ {j['company']}")
        print(f"    {j['url']}")

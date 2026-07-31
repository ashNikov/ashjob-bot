"""Jobberman scraper — Nigerian job board (HTML). Local DevOps/cloud roles."""
import requests
from bs4 import BeautifulSoup
from matcher import is_relevant, is_fresh

SEARCH = "https://www.jobberman.com/jobs?q=devops"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}


def fetch():
    resp = requests.get(SEARCH, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    jobs, seen = [], set()
    for a in soup.select('a[href*="/listings/"]'):
        href = a.get("href", "")
        title = a.get_text(strip=True)
        if not title or href in seen:
            continue
        seen.add(href)
        jobs.append({
            "title": title.strip(),
            "company": "",          # company is elsewhere in card; list gives title only
            "location": "Nigeria",
            "tags": [],
            "url": href if href.startswith("http") else "https://www.jobberman.com" + href,
            "posted": "",
            "source": "Jobberman",
        })
    return jobs


def fetch_relevant():
    return [j for j in fetch()
            if is_relevant(j["title"], j["tags"]) and is_fresh(j.get("posted", ""))]


if __name__ == "__main__":
    jobs = fetch_relevant()
    print(f"Jobberman — relevant: {len(jobs)}")
    for j in jobs:
        print(f"  {j['title']}")
        print(f"    {j['url']}")

"""
Job Discovery — scrapes/queries multiple job boards and saves new listings to the DB.
Run: python run.py discover
"""

import re
import time
import requests
import feedparser
from bs4 import BeautifulSoup
from scripts.database import upsert_job, init_db
from config import JOB_BOARDS, SEARCH_QUERIES

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


# ─── Utility ─────────────────────────────────────────────────────────────────

def clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def parse_salary(text: str) -> tuple[str | None, float | None, bool]:
    """Returns (raw_string, monthly_usd_estimate, is_listed)."""
    if not text:
        return None, None, False
    patterns = [
        r"\$[\d,]+\s*[-–]\s*\$[\d,]+\s*(?:per\s+)?(?:yr|year|annually)",
        r"\$[\d,]+\s*[-–]\s*\$[\d,]+\s*(?:per\s+)?(?:mo|month)",
        r"\$[\d,]+\s*[-–]\s*\$[\d,]+\s*(?:per\s+)?(?:hr|hour)",
        r"\$[\d,]+\s*[kK]\s*[-–]\s*\$?[\d,]+\s*[kK]",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group()
            nums = [float(n.replace(",", "").replace("k", "000").replace("K", "000"))
                    for n in re.findall(r"[\d,]+[kK]?", raw) if re.search(r"\d", n)]
            if not nums:
                return raw, None, True
            avg = sum(nums) / len(nums)
            # Convert to monthly
            if re.search(r"hr|hour", raw, re.I):
                monthly = avg * 40 * 4.33
            elif re.search(r"yr|year|annual", raw, re.I):
                monthly = avg / 12
            else:
                monthly = avg
            return raw, round(monthly, 2), True
    # Check if there's any dollar sign at all
    if "$" in text or "salary" in text.lower() or "compensation" in text.lower():
        return text[:120], None, True
    return None, None, False


# ─── Remotive API ─────────────────────────────────────────────────────────────

def fetch_remotive() -> list[dict]:
    results = []
    cfg = JOB_BOARDS.get("remotive", {})
    if not cfg.get("enabled"):
        return results

    print("[Remotive] Fetching via API...")
    try:
        resp = requests.get(cfg["url"], headers=HEADERS, timeout=15)
        resp.raise_for_status()
        jobs = resp.json().get("jobs", [])
        for j in jobs:
            # Basic remote + keyword relevance filter
            title = j.get("job_type", "") + " " + j.get("title", "")
            if not any(kw in title.lower() for kw in ["health", "medical", "clinical", "ai", "remote"]):
                if "remote" not in j.get("tags", []):
                    continue
            desc = clean_text(j.get("description", ""))
            sal_raw, sal_monthly, sal_listed = parse_salary(desc)
            results.append({
                "title": j.get("title", ""),
                "company": j.get("company_name", ""),
                "url": j.get("url", ""),
                "board": "remotive",
                "description": desc[:8000],
                "salary_raw": sal_raw,
                "salary_monthly": sal_monthly,
                "salary_listed": int(sal_listed),
                "remote": 1,
            })
    except Exception as e:
        print(f"[Remotive] Error: {e}")
    return results


# ─── We Work Remotely (RSS) ───────────────────────────────────────────────────

def fetch_weworkremotely() -> list[dict]:
    results = []
    cfg = JOB_BOARDS.get("weworkremotely", {})
    if not cfg.get("enabled"):
        return results

    print("[WeWorkRemotely] Fetching RSS...")
    for feed_url in cfg.get("feeds", []):
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                desc = clean_text(entry.get("summary", ""))
                sal_raw, sal_monthly, sal_listed = parse_salary(desc)
                results.append({
                    "title": entry.get("title", ""),
                    "company": entry.get("author", ""),
                    "url": entry.get("link", ""),
                    "board": "weworkremotely",
                    "description": desc[:8000],
                    "salary_raw": sal_raw,
                    "salary_monthly": sal_monthly,
                    "salary_listed": int(sal_listed),
                    "remote": 1,
                })
        except Exception as e:
            print(f"[WeWorkRemotely] Feed error ({feed_url}): {e}")
    return results


# ─── LinkedIn Scraper ─────────────────────────────────────────────────────────

def fetch_linkedin() -> list[dict]:
    results = []
    cfg = JOB_BOARDS.get("linkedin", {})
    if not cfg.get("enabled"):
        return results

    print("[LinkedIn] Scraping job listings...")
    for query in SEARCH_QUERIES[:5]:  # limit to avoid rate limiting
        try:
            params = {**cfg["params"], "keywords": query, "location": "Worldwide"}
            resp = requests.get(cfg["base_url"], params=params, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("div.job-search-card, li.jobs-search__results-list")
            for card in cards[:10]:
                title_el  = card.select_one("h3, .base-search-card__title")
                company_el = card.select_one("h4, .base-search-card__subtitle")
                link_el   = card.select_one("a.base-card__full-link, a[href*='/jobs/']")
                if not (title_el and link_el):
                    continue
                url = link_el.get("href", "").split("?")[0]
                results.append({
                    "title": title_el.get_text(strip=True),
                    "company": company_el.get_text(strip=True) if company_el else "",
                    "url": url,
                    "board": "linkedin",
                    "description": "",  # fetched separately if score >= threshold
                    "salary_raw": None,
                    "salary_monthly": None,
                    "salary_listed": 0,
                    "remote": 1,
                })
            time.sleep(2)  # polite delay
        except Exception as e:
            print(f"[LinkedIn] Error for query '{query}': {e}")
    return results


# ─── HIMSS Job Board ──────────────────────────────────────────────────────────

def fetch_himss() -> list[dict]:
    results = []
    cfg = JOB_BOARDS.get("himss", {})
    if not cfg.get("enabled"):
        return results

    print("[HIMSS] Scraping job listings...")
    try:
        resp = requests.get(cfg["base_url"], params=cfg["params"], headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select(".job-listing, .joblisting, article")[:20]:
            title_el = card.select_one("h2, h3, .job-title, .listing-title")
            link_el  = card.select_one("a")
            if not (title_el and link_el):
                continue
            url = link_el.get("href", "")
            if url and not url.startswith("http"):
                url = "https://jobs.himss.org" + url
            results.append({
                "title": title_el.get_text(strip=True),
                "company": "",
                "url": url,
                "board": "himss",
                "description": "",
                "salary_raw": None,
                "salary_monthly": None,
                "salary_listed": 0,
                "remote": 1,
            })
    except Exception as e:
        print(f"[HIMSS] Error: {e}")
    return results


# ─── Main Discovery Runner ────────────────────────────────────────────────────

def run_discovery() -> dict:
    init_db()
    all_jobs = (
        fetch_remotive()
        + fetch_weworkremotely()
        + fetch_linkedin()
        + fetch_himss()
    )

    added, skipped = 0, 0
    for job in all_jobs:
        job_id = upsert_job(job)
        if job_id:
            added += 1
        else:
            skipped += 1

    summary = {
        "total_found": len(all_jobs),
        "added_new": added,
        "skipped_dupes": skipped,
    }
    print(f"\n[Discovery] Done — {added} new jobs added, {skipped} duplicates skipped.")
    return summary


if __name__ == "__main__":
    run_discovery()

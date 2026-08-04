from datetime import datetime, timezone

import requests

API_URL = "https://www.arbeitnow.com/api/job-board-api"


def fetch_arbeitnow_jobs() -> list[dict]:
    res = requests.get(API_URL, timeout=15)
    res.raise_for_status()
    data = res.json()
    jobs = data.get("data") or []

    result = []
    for job in jobs:
        if not job or not job.get("slug") or not job.get("remote"):
            continue  # remote-only
        posted_at = None
        if job.get("created_at"):
            posted_at = datetime.fromtimestamp(
                job["created_at"], tz=timezone.utc
            ).isoformat()
        result.append(
            {
                "id": f"arbeitnow-{job['slug']}",
                "title": job.get("title"),
                "company": job.get("company_name") or "Unknown company",
                "location": job.get("location") or "Remote",
                "tags": job.get("tags") or [],
                "url": job.get("url"),
                "source": "Arbeitnow",
                "posted_at": posted_at,
            }
        )
    return result

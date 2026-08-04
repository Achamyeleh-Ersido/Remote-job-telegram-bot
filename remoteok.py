import requests

API_URL = "https://remoteok.com/api"

# RemoteOK asks for a descriptive User-Agent, otherwise it may block requests.
HEADERS = {
    "User-Agent": "remote-jobs-telegram-bot/1.0 (https://github.com/)",
}


def fetch_remoteok_jobs() -> list[dict]:
    res = requests.get(API_URL, headers=HEADERS, timeout=15)
    res.raise_for_status()
    data = res.json()

    # The first element is a legal/metadata notice, not a job. Skip it.
    jobs = data[1:] if isinstance(data, list) else []

    result = []
    for job in jobs:
        if not job or not job.get("id") or not job.get("position"):
            continue
        result.append(
            {
                "id": f"remoteok-{job['id']}",
                "title": job["position"],
                "company": job.get("company") or "Unknown company",
                "location": job.get("location") or "Remote",
                "tags": job.get("tags") or [],
                "url": job.get("url") or f"https://remoteok.com/remote-jobs/{job['id']}",
                "source": "RemoteOK",
                "posted_at": job.get("date"),
            }
        )
    return result

# Remote Jobs Telegram Bot (Python)

Polls public remote-job APIs (RemoteOK, Arbeitnow) on a schedule and auto-posts
new listings to a Telegram channel. Built with `python-telegram-bot`.

## 1. Create the bot & channel

1. Message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot` → copy the token.
2. Create a Telegram **channel** (public or private).
3. Add your bot to the channel **as an admin** (needs "Post Messages" permission).
4. Channel ID:
   - Public channel → use `@your_channel_username`.
   - Private channel → forward any message from it to [@userinfobot](https://t.me/userinfobot) to get the numeric ID (looks like `-1001234567890`).

## 2. Configure

```bash
cp .env.example .env
```

Fill in `.env`:
- `BOT_TOKEN` — from BotFather
- `CHANNEL_ID` — from step above
- `CHECK_INTERVAL_MINUTES` — optional, defaults to 15
- `KEYWORDS` / `EXCLUDE_KEYWORDS` — optional filters, e.g. `KEYWORDS=react,node,frontend`

## 3. Run locally

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 main.py
```

The bot checks for jobs immediately on startup, then again every
`CHECK_INTERVAL_MINUTES`. Send `/check` to the bot in a DM to trigger a manual
check anytime.

## 4. Deploy (free tier)

**Render / Railway / Fly.io** all work similarly:

1. Push this folder to a GitHub repo.
2. Create a new **Worker/Background Service** (not a Web Service — this bot doesn't
   listen on a port) pointing at the repo.
3. Build command: `pip install -r requirements.txt`. Start command: `python3 main.py`.
4. Add the same environment variables from `.env` in the platform's dashboard.
5. Deploy.

> **Persistence note:** `data/posted.json` tracks which jobs were already posted
> so the bot doesn't repost them. On most free tiers the filesystem resets on
> every redeploy/restart, so you may see a handful of re-posts after a deploy.
> If that's a problem, swap `src/store.py` for a free Redis instance (e.g.
> [Upstash](https://upstash.com)) or a small Postgres table — happy to wire
> that up if you want it.

## Adding more job sources

Each source lives in `src/sources/*.py` and exports a function that returns
a list of job dicts shaped like:

```python
{
    "id": str, "title": str, "company": str, "location": str,
    "tags": list[str], "url": str, "source": str, "posted_at": str | None,
}
```

Add a new file, then import and include it in the `fetch_all_jobs()` loop in
`main.py`.

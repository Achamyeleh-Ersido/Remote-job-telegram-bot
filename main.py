import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

from formatter import format_job_message
from arbeitnow import fetch_arbeitnow_jobs
from remoteok import fetch_remoteok_jobs
from store import load_posted_ids, save_posted_ids

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO
)
log = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHECK_INTERVAL_MINUTES = float(os.getenv("CHECK_INTERVAL_MINUTES", "15"))
INCLUDE_KEYWORDS = [
    k.strip().lower() for k in os.getenv("KEYWORDS", "").split(",") if k.strip()
]
EXCLUDE_KEYWORDS = [
    k.strip().lower()
    for k in os.getenv("EXCLUDE_KEYWORDS", "").split(",")
    if k.strip()
]

if not BOT_TOKEN:
    sys.exit("Missing BOT_TOKEN in environment. Copy .env.example to .env and fill it in.")
if not CHANNEL_ID:
    sys.exit("Missing CHANNEL_ID in environment. Copy .env.example to .env and fill it in.")


def matches_filters(job: dict) -> bool:
    haystack = " ".join(
        [job.get("title", ""), job.get("company", ""), *(job.get("tags") or [])]
    ).lower()

    if INCLUDE_KEYWORDS and not any(k in haystack for k in INCLUDE_KEYWORDS):
        return False
    if EXCLUDE_KEYWORDS and any(k in haystack for k in EXCLUDE_KEYWORDS):
        return False
    return True


def fetch_all_jobs() -> list[dict]:
    jobs = []
    for fetch_fn, name in (
        (fetch_remoteok_jobs, "RemoteOK"),
        (fetch_arbeitnow_jobs, "Arbeitnow"),
    ):
        try:
            jobs.extend(fetch_fn())
        except Exception as exc:  # noqa: BLE001 - log and keep going
            log.error("Source fetch failed (%s): %s", name, exc)
    return jobs


async def check_and_post_jobs(context: ContextTypes.DEFAULT_TYPE) -> int:
    log.info("Checking for new jobs...")
    posted_ids = load_posted_ids()
    jobs = fetch_all_jobs()

    new_jobs = [
        job for job in jobs if job["id"] not in posted_ids and matches_filters(job)
    ]

    if not new_jobs:
        log.info("No new jobs found.")
        return 0

    log.info("Found %d new job(s). Posting...", len(new_jobs))

    posted_count = 0
    for job in new_jobs:
        try:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=format_job_message(job),
                parse_mode=ParseMode.MARKDOWN_V2,
                disable_web_page_preview=True,
            )
            posted_ids.add(job["id"])
            posted_count += 1
            # Small delay to stay well under Telegram's rate limits.
            await asyncio.sleep(1.5)
        except Exception as exc:  # noqa: BLE001
            log.error("Failed to post job %s: %s", job["id"], exc)

    save_posted_ids(posted_ids)
    log.info("Done posting new jobs.")
    return posted_count


async def scheduled_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    await check_and_post_jobs(context)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 hello This bot auto-posts new remote job listings to a channel.\n"
        "It runs on a schedule in the background — no commands needed here.\n"
        "Use /check to trigger a manual check right now."
    )


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Checking for new jobs now...")
    try:
        count = await check_and_post_jobs(context)
        await update.message.reply_text(f"Check complete. Posted {count} new job(s).")
    except Exception as exc:  # noqa: BLE001
        log.exception("Manual check failed")
        await update.message.reply_text("Something went wrong during the check. See server logs.")


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("check", check_command))

    # Run immediately on startup, then on the interval.
    app.job_queue.run_once(scheduled_check, when=0)
    app.job_queue.run_repeating(
        scheduled_check, interval=CHECK_INTERVAL_MINUTES * 60, first=CHECK_INTERVAL_MINUTES * 60
    )

    log.info(
        "Bot starting. Posting to %s every %s minute(s).",
        CHANNEL_ID,
        CHECK_INTERVAL_MINUTES,
    )
    app.run_polling()


if __name__ == "__main__":
    main()

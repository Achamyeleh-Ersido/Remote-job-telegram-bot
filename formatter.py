import re

# Characters that are special in Telegram's MarkdownV2 and must be escaped.
_SPECIAL_CHARS = re.compile(r"([_*\[\]()~`>#+\-=|{}.!\\])")


def escape_md(text) -> str:
    return _SPECIAL_CHARS.sub(r"\\\1", str(text or ""))


def format_job_message(job: dict) -> str:
    tags = job.get("tags") or []
    tags_line = ""
    if tags:
        tags_line = " ".join(f"`{escape_md(t)}`" for t in tags[:6])

    lines = [
        f"🟢 *{escape_md(job['title'])}*",
        f"🏢 {escape_md(job['company'])}",
        f"📍 {escape_md(job['location'])}",
    ]
    if tags_line:
        lines.append(f"🏷 {tags_line}")
    lines.append(f"🔗 [Apply here]({job['url']})")
    lines.append(f"_via {escape_md(job['source'])}_")

    return "\n".join(lines)

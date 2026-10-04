#!/usr/bin/env python3
"""Minimal Telegram job-runner bot (long polling, single-owner)."""
from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import jobs
import papers

load_dotenv()
log = logging.getLogger("telegram-jobs")


def allowed_ids() -> set[str]:
    raw = os.environ.get("TELEGRAM_CHAT_ID", "")
    return {c.strip() for c in raw.split(",") if c.strip()}


async def guard(update: Update) -> bool:
    chat_id = str(update.effective_chat.id) if update.effective_chat else ""
    if chat_id not in allowed_ids():
        if update.message:
            await update.message.reply_text("Unauthorized.")
        return False
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update):
        return
    names = ", ".join(sorted(jobs.REGISTRY))
    await update.message.reply_text(
        "telegram-jobs ready.\n"
        "/help — commands\n"
        f"/list — jobs: {names}\n"
        "/run <name> — run a job\n"
        "/find <keywords> — top 10 related papers"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update):
        return
    await start(update, context)


async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update):
        return
    lines = [f"{name} — {desc}" for name, (desc, _) in sorted(jobs.REGISTRY.items())]
    await update.message.reply_text("\n".join(lines) or "No jobs registered.")


async def run_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /run <job-name>")
        return
    name = context.args[0]
    entry = jobs.REGISTRY.get(name)
    if not entry:
        await update.message.reply_text(f"Unknown job: {name}")
        return
    desc, func = entry
    try:
        result = func()
        await update.message.reply_text(f"[{name}] {desc}\n{result}")
    except Exception as exc:  # noqa: BLE001 - report job errors to owner
        log.exception("job failed: %s", name)
        await update.message.reply_text(f"[{name}] failed: {exc}")


async def find_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update):
        return
    query = " ".join(context.args).strip()
    if not query:
        await update.message.reply_text("Usage: /find <keywords>")
        return
    await update.message.reply_text(f'Searching papers for "{query}" ...')
    try:
        import asyncio

        results = await asyncio.to_thread(papers.search, query, 10)
        for chunk in papers.format_results(query, results):
            await update.message.reply_text(chunk, disable_web_page_preview=True)
    except Exception as exc:  # noqa: BLE001 - report search errors to owner
        log.exception("find failed: %s", query)
        await update.message.reply_text(f"find failed: {exc}")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")
    if not allowed_ids():
        raise SystemExit("TELEGRAM_CHAT_ID is not set")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("run", run_cmd))
    app.add_handler(CommandHandler("find", find_cmd))
    app.run_polling()


if __name__ == "__main__":
    main()

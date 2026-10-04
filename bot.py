#!/usr/bin/env python3
"""Minimal Telegram job-runner bot (long polling, single-owner)."""
from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import jobs
import papers
import websearch

COMMANDS = [
    ("/start", "봇 상태 + 명령어 안내", "live"),
    ("/help", "도움말", "live"),
    ("/list", "명령어 리스트", "live"),
    ("/run <job>", "등록된 job 실행", "live"),
    ("/find <검색어>", "Google 웹 검색 top 10", "live"),
    ("/findresearch <검색어>", "관련 논문 top 10", "live"),
]

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
    await update.message.reply_text(
        "telegram-jobs ready.\n"
        "/list — 명령어 리스트\n"
        "/find <검색어> — Google 웹 검색 top 10\n"
        "/findresearch <검색어> — 관련 논문 top 10\n"
        "/run <job> — 등록된 job 실행"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update):
        return
    await start(update, context)


async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update):
        return
    lines = []
    for cmd, desc, status in COMMANDS:
        mark = "●" if status == "live" else "○ 개발중"
        lines.append(f"{mark} {cmd} — {desc}")
    job_names = ", ".join(sorted(jobs.REGISTRY))
    lines.append(f"\njobs: {job_names}")
    await update.message.reply_text("\n".join(lines))


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


async def do_findresearch(update: Update, query: str) -> None:
    query = query.strip()
    if not query:
        await update.message.reply_text('Usage: /findresearch <keywords> 또는 "findresearch <keywords>"')
        return
    # 1) 접수 피드백 (즉시)
    await update.message.reply_text(f'📥 접수됨: "{query}"\n논문 검색 중... (top 10)')
    # 2) 검색 후 결과 전달
    try:
        import asyncio

        results = await asyncio.to_thread(papers.search, query, 10)
        for chunk in papers.format_results(query, results):
            await update.message.reply_text(chunk, disable_web_page_preview=True)
    except Exception as exc:  # noqa: BLE001 - report search errors to owner
        log.exception("findresearch failed: %s", query)
        await update.message.reply_text(f"findresearch failed: {exc}")


async def do_find(update: Update, query: str) -> None:
    query = query.strip()
    if not query:
        await update.message.reply_text('Usage: /find <검색어> 또는 "find <검색어>"')
        return
    await update.message.reply_text(f'📥 접수됨: "{query}"\n웹 검색 중... (top 10)')
    try:
        import asyncio

        hits, source = await asyncio.to_thread(websearch.search, query, 10)
        for chunk in websearch.format_results(query, hits, source):
            await update.message.reply_text(chunk, disable_web_page_preview=True)
    except Exception as exc:  # noqa: BLE001 - report search errors to owner
        log.exception("find failed: %s", query)
        await update.message.reply_text(f"find failed: {exc}")


async def findresearch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update):
        return
    await do_findresearch(update, " ".join(context.args))


async def find_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update):
        return
    await do_find(update, " ".join(context.args))


async def find_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update):
        return
    text = (update.message.text or "").strip()
    low = text.lower()
    if low.startswith("findresearch "):
        await do_findresearch(update, text[13:])
    elif low.startswith("find "):
        await do_find(update, text[5:])
    else:
        await update.message.reply_text('📥 접수됨. "/list"로 명령어를 확인해요.')


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
    app.add_handler(CommandHandler("findresearch", findresearch_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, find_text))
    app.run_polling()


if __name__ == "__main__":
    main()

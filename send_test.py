#!/usr/bin/env python3
"""One-off Telegram send test. Reads TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID from env."""
from __future__ import annotations

import os
import sys
import urllib.parse
import urllib.request


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip().split(",")[0].strip()
    text = sys.argv[1] if len(sys.argv) > 1 else "telegram-jobs test: 발송 OK"
    if not token:
        print("TELEGRAM_BOT_TOKEN is not set", file=sys.stderr)
        return 2
    if not chat_id:
        print("TELEGRAM_CHAT_ID is not set", file=sys.stderr)
        return 2
    url = (
        f"https://api.telegram.org/bot{token}/sendMessage?"
        + urllib.parse.urlencode({"chat_id": chat_id, "text": text})
    )
    try:
        with urllib.request.urlopen(url, timeout=15) as res:
            body = res.read().decode("utf-8", "replace")
        ok = '"ok":true' in body.replace(" ", "")
        print("SEND OK" if ok else f"UNEXPECTED: {body[:300]}")
        return 0 if ok else 1
    except Exception as exc:  # noqa: BLE001 - surface API errors
        print(f"SEND FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

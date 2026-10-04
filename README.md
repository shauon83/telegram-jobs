# telegram-jobs

Telegram으로 소유자와 소통하며 job을 실행하는 개인용 bot. Long polling 방식.

GitHub repo Settings > Secrets에 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 저장됨. 코드는 토큰 없이 env로만 읽음.

## 구조
- `bot.py` — `/start /help /list /run` + chat_id allowlist
- `jobs.py` — `REGISTRY`에 job 등록

## 실행
```powershell
pip install -r requirements.txt
copy .env.example .env
# .env에 TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID 입력
python bot.py
```

Telegram에서:
```
/start
/list
/run ping
```

## job 추가
`jobs.py`에 함수 + `REGISTRY["name"] = ("설명", func)` 추가.

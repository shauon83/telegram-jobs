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
/find 아이피타임 이지메시
/findresearch graph neural networks
```

## 검색
- `/find <검색어>` — Google 웹 검색 top 10 (API 키 있으면 Google 공식, 없으면 DDG fallback + Google 링크)
- `/findresearch <검색어>` — OpenAlex 관련도순 top 10 (2021년 이후) + Scholar 딥링크
- 일반 텍스트 `find ...`, `findresearch ...`도 동일 동작
- `/list` — 명령어 리스트 (신규 명령 추가 시 COMMANDS에 등록)

## job 추가
`jobs.py`에 함수 + `REGISTRY["name"] = ("설명", func)` 추가.

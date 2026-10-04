"""Web search top 10.

Primary: Google Custom Search API when GOOGLE_API_KEY + GOOGLE_CX are set.
Fallback: DuckDuckGo html endpoint (no key). Always includes a Google link.
"""
from __future__ import annotations

import html as htmlmod
import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass
class Hit:
    title: str
    url: str
    snippet: str


def google_url(query: str) -> str:
    return "https://www.google.com/search?" + urllib.parse.urlencode({"q": query})


def _via_google_api(query: str, limit: int) -> list[Hit] | None:
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    cx = os.environ.get("GOOGLE_CX", "").strip()
    if not key or not cx:
        return None
    params = {"key": key, "cx": cx, "q": query, "num": str(min(limit, 10))}
    url = "https://www.googleapis.com/customsearch/v1?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=20) as res:
        payload = json.loads(res.read().decode("utf-8"))
    hits = []
    for item in payload.get("items", [])[:limit]:
        hits.append(Hit(item.get("title", ""), item.get("link", ""), item.get("snippet", "")))
    return hits


def _via_ddg(query: str, limit: int) -> list[Hit]:
    data = urllib.parse.urlencode({"q": query}).encode()
    req = urllib.request.Request(
        "https://html.duckduckgo.com/html/",
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        page = res.read().decode("utf-8", "replace")
    hits: list[Hit] = []
    for m in re.finditer(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', page, re.S):
        if len(hits) >= limit:
            break
        raw_link, raw_title = m.group(1), m.group(2)
        title = htmlmod.unescape(re.sub(r"<.*?>", "", raw_title)).strip()
        link = raw_link
        if link.startswith("//"):
            link = "https:" + link
        if "duckduckgo.com/l/" in link:
            qs = urllib.parse.parse_qs(urllib.parse.urlsplit(link).query)
            link = qs.get("uddg", [link])[0]
        hits.append(Hit(title or link, link, ""))
    return hits


def search(query: str, limit: int = 10) -> tuple[list[Hit], str]:
    """Returns (hits, source) where source is 'google' or 'ddg'."""
    hits = _via_google_api(query, limit)
    if hits is not None:
        return hits, "google"
    return _via_ddg(query, limit), "ddg"


def format_results(query: str, hits: list[Hit], source: str) -> list[str]:
    header = f'find "{query}" top {len(hits)} [{source}]\nGoogle: {google_url(query)}'
    chunks = [header]
    for i, h in enumerate(hits, 1):
        line = f"\n\n{i}. {h.title}\n   {h.url}"
        if h.snippet:
            line += f"\n   {h.snippet[:160]}"
        if len(chunks[-1]) + len(line) > 3800:
            chunks.append(line.strip())
        else:
            chunks[-1] += line
    return chunks

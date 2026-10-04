"""Paper search via OpenAlex (free, no key) with Google Scholar deep links.

Google Scholar has no official API and blocks scraping, so relevance search
goes through OpenAlex (which indexes the same scholarly corpus). Each result
includes a Scholar link for follow-up lookup.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass
class Paper:
    title: str
    authors: str
    year: int | None
    venue: str
    citations: int
    url: str


def scholar_url(query: str) -> str:
    return "https://scholar.google.com/scholar?" + urllib.parse.urlencode({"q": query})


def search(query: str, limit: int = 10, since_year: int = 2021) -> list[Paper]:
    """Search OpenAlex by relevance, biased to recent works."""
    params = {
        "search": query,
        "per-page": str(limit),
        "filter": f"from_publication_date:{since_year}-01-01",
        "select": "title,authorships,publication_year,primary_location,cited_by_count,doi,id",
    }
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "telegram-jobs/1.0"})
    with urllib.request.urlopen(req, timeout=20) as res:
        payload = json.loads(res.read().decode("utf-8"))
    papers: list[Paper] = []
    for work in payload.get("results", [])[:limit]:
        title = (work.get("title") or "Untitled").strip()
        authorships = work.get("authorships", []) or []
        names = [a.get("author", {}).get("display_name", "?") for a in authorships]
        if len(names) > 3:
            authors = f"{', '.join(names[:3])} et al."
        else:
            authors = ", ".join(names) or "-"
        loc = work.get("primary_location") or {}
        source = (loc.get("source") or {}).get("display_name", "") or ""
        doi = work.get("doi") or (loc.get("landing_page_url")) or work.get("id", "")
        papers.append(
            Paper(
                title=title,
                authors=authors,
                year=work.get("publication_year"),
                venue=source,
                citations=int(work.get("cited_by_count") or 0),
                url=doi,
            )
        )
    return papers


def format_results(query: str, papers: list[Paper]) -> list[str]:
    """Format as one or more Telegram-safe (<4000 char) messages."""
    header = f'find "{query}" top {len(papers)}\nScholar: {scholar_url(query)}'
    chunks = [header]
    current = header
    for i, p in enumerate(papers, 1):
        line = (
            f"\n\n{i}. {p.title}\n"
            f"   {p.authors} | {p.year or '-'} | {p.venue or '-'}\n"
            f"   cited {p.citations} | {p.url}"
        )
        if len(current) + len(line) > 3800:
            chunks.append(line.strip())
            current = line
        else:
            chunks[-1] += line
            current += line
    return chunks

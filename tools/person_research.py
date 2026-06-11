#!/usr/bin/env python3
"""
Free public-info researcher for boss-skills.

Searches free, no-API-key sources for public information about a person
(boss, mentor, advisor, PI), to support persona profiling:

- OpenAlex        author profiles + papers + concepts (academia)
- Semantic Scholar author search + papers (academia)
- arXiv           recent preprints (academia)
- Crossref        publications metadata (academia)
- GitHub          public profile + repos (engineering)
- Wikipedia       biography summary (public figures)

All endpoints are free and need no API key. Network failures are reported
per-source and never abort the whole run.

Usage:
  python tools/person_research.py --name "Jane Doe" --sources all
  python tools/person_research.py --name "Jane Doe" --affiliation "MIT" \
      --sources openalex,arxiv --limit 10 --save-dir bosses/jane/knowledge/research
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

USER_AGENT = "boss-skills-person-research/1.0 (https://github.com/vogtsw/boss-skills)"
TIMEOUT = 20


def http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8")


def search_openalex(name: str, affiliation: str, limit: int) -> dict:
    url = "https://api.openalex.org/authors?search=" + urllib.parse.quote(name) + "&per-page=5"
    data = http_get_json(url)
    candidates = []
    for author in data.get("results", [])[:5]:
        inst = (author.get("last_known_institutions") or [{}])
        inst_name = inst[0].get("display_name", "") if inst else ""
        candidates.append(
            {
                "id": author.get("id", ""),
                "name": author.get("display_name", ""),
                "institution": inst_name,
                "works_count": author.get("works_count", 0),
                "cited_by_count": author.get("cited_by_count", 0),
                "topics": [c.get("display_name", "") for c in (author.get("x_concepts") or [])[:8]],
            }
        )

    picked = None
    if candidates:
        if affiliation:
            for cand in candidates:
                if affiliation.lower() in cand["institution"].lower():
                    picked = cand
                    break
        picked = picked or candidates[0]

    works = []
    if picked and picked["id"]:
        author_key = picked["id"].rsplit("/", 1)[-1]
        works_url = (
            "https://api.openalex.org/works?filter=author.id:" + author_key
            + "&sort=cited_by_count:desc&per-page=" + str(limit)
        )
        wdata = http_get_json(works_url)
        for work in wdata.get("results", []):
            works.append(
                {
                    "title": work.get("title", ""),
                    "year": work.get("publication_year"),
                    "cited_by": work.get("cited_by_count", 0),
                    "venue": ((work.get("primary_location") or {}).get("source") or {}).get("display_name", ""),
                    "url": work.get("doi") or work.get("id", ""),
                }
            )
    return {"candidates": candidates, "picked": picked, "top_works": works}


def search_semantic_scholar(name: str, limit: int) -> dict:
    url = (
        "https://api.semanticscholar.org/graph/v1/author/search?query=" + urllib.parse.quote(name)
        + "&fields=name,affiliations,paperCount,citationCount,hIndex,url&limit=5"
    )
    data = http_get_json(url)
    candidates = []
    for author in data.get("data", [])[:5]:
        candidates.append(
            {
                "authorId": author.get("authorId", ""),
                "name": author.get("name", ""),
                "affiliations": author.get("affiliations", []),
                "paperCount": author.get("paperCount", 0),
                "citationCount": author.get("citationCount", 0),
                "hIndex": author.get("hIndex", 0),
                "url": author.get("url", ""),
            }
        )

    papers = []
    if candidates:
        author_id = candidates[0]["authorId"]
        papers_url = (
            "https://api.semanticscholar.org/graph/v1/author/" + author_id
            + "/papers?fields=title,year,venue,citationCount,abstract&limit=" + str(limit)
        )
        pdata = http_get_json(papers_url)
        for paper in pdata.get("data", []):
            abstract = paper.get("abstract") or ""
            papers.append(
                {
                    "title": paper.get("title", ""),
                    "year": paper.get("year"),
                    "venue": paper.get("venue", ""),
                    "citationCount": paper.get("citationCount", 0),
                    "abstract": abstract[:400],
                }
            )
    return {"candidates": candidates, "papers": papers}


def search_arxiv(name: str, limit: int) -> dict:
    query = 'au:"' + name + '"'
    url = (
        "http://export.arxiv.org/api/query?search_query=" + urllib.parse.quote(query)
        + "&sortBy=submittedDate&sortOrder=descending&max_results=" + str(limit)
    )
    text = http_get_text(url)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(text)
    papers = []
    for entry in root.findall("atom:entry", ns):
        title = (entry.findtext("atom:title", "", ns) or "").strip()
        summary = (entry.findtext("atom:summary", "", ns) or "").strip()
        published = (entry.findtext("atom:published", "", ns) or "")[:10]
        link = entry.findtext("atom:id", "", ns) or ""
        authors = [a.findtext("atom:name", "", ns) for a in entry.findall("atom:author", ns)]
        papers.append(
            {
                "title": re.sub(r"\s+", " ", title),
                "published": published,
                "authors": authors,
                "summary": re.sub(r"\s+", " ", summary)[:400],
                "url": link,
            }
        )
    return {"papers": papers}


def search_crossref(name: str, limit: int) -> dict:
    url = (
        "https://api.crossref.org/works?query.author=" + urllib.parse.quote(name)
        + "&rows=" + str(limit) + "&sort=is-referenced-by-count&order=desc"
    )
    data = http_get_json(url)
    works = []
    for item in data.get("message", {}).get("items", []):
        date_parts = (item.get("issued", {}).get("date-parts") or [[None]])[0]
        works.append(
            {
                "title": (item.get("title") or [""])[0],
                "year": date_parts[0] if date_parts else None,
                "venue": (item.get("container-title") or [""])[0],
                "cited_by": item.get("is-referenced-by-count", 0),
                "doi": item.get("DOI", ""),
                "type": item.get("type", ""),
            }
        )
    return {"works": works}


def search_github(name: str, limit: int) -> dict:
    url = "https://api.github.com/search/users?q=" + urllib.parse.quote(name) + "&per_page=5"
    data = http_get_json(url)
    candidates = []
    for user in data.get("items", [])[:3]:
        login = user.get("login", "")
        profile: dict = {"login": login, "html_url": user.get("html_url", "")}
        try:
            detail = http_get_json("https://api.github.com/users/" + login)
            profile.update(
                {
                    "name": detail.get("name", ""),
                    "company": detail.get("company", ""),
                    "bio": detail.get("bio", ""),
                    "blog": detail.get("blog", ""),
                    "public_repos": detail.get("public_repos", 0),
                    "followers": detail.get("followers", 0),
                }
            )
            repos = http_get_json(
                "https://api.github.com/users/" + login + "/repos?sort=stars&per_page=" + str(min(limit, 10))
            )
            profile["top_repos"] = [
                {
                    "name": r.get("name", ""),
                    "description": r.get("description", ""),
                    "language": r.get("language", ""),
                    "stars": r.get("stargazers_count", 0),
                }
                for r in repos
            ]
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            pass
        candidates.append(profile)
    return {"candidates": candidates}


def search_wikipedia(name: str, lang: str = "zh") -> dict:
    results = {}
    for code in (lang, "en"):
        if code in results:
            continue
        try:
            url = (
                "https://" + code + ".wikipedia.org/api/rest_v1/page/summary/"
                + urllib.parse.quote(name.replace(" ", "_"))
            )
            data = http_get_json(url)
            if data.get("type") != "disambiguation" and data.get("extract"):
                results[code] = {
                    "title": data.get("title", ""),
                    "description": data.get("description", ""),
                    "extract": data.get("extract", ""),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                }
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
            continue
    return results


SOURCES = {
    "openalex": lambda args: search_openalex(args.name, args.affiliation, args.limit),
    "semanticscholar": lambda args: search_semantic_scholar(args.name, args.limit),
    "arxiv": lambda args: search_arxiv(args.name, args.limit),
    "crossref": lambda args: search_crossref(args.name, args.limit),
    "github": lambda args: search_github(args.name, args.limit),
    "wikipedia": lambda args: search_wikipedia(args.name),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Free public-info researcher for persona profiling")
    parser.add_argument("--name", required=True, help="Person name (real name preferred for academic sources)")
    parser.add_argument("--affiliation", default="", help="Affiliation hint for disambiguation, e.g. university or company")
    parser.add_argument(
        "--sources",
        default="all",
        help="Comma-separated: openalex,semanticscholar,arxiv,crossref,github,wikipedia or 'all'",
    )
    parser.add_argument("--limit", type=int, default=10, help="Max items per source")
    parser.add_argument("--save-dir", default="", help="Optional dir to save raw JSON results")
    args = parser.parse_args()

    if args.sources == "all":
        selected = list(SOURCES)
    else:
        selected = [s.strip() for s in args.sources.split(",") if s.strip() in SOURCES]
        if not selected:
            print("Error: no valid sources. Valid: " + ", ".join(SOURCES), file=sys.stderr)
            sys.exit(1)

    report = {"name": args.name, "affiliation_hint": args.affiliation, "sources": {}}
    for source in selected:
        try:
            report["sources"][source] = SOURCES[source](args)
        except Exception as exc:  # network/parse errors must not abort other sources
            report["sources"][source] = {"error": str(exc)}

    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.save_dir:
        save_dir = Path(args.save_dir).expanduser()
        save_dir.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", args.name.lower()).strip("-") or "person"
        out_path = save_dir / (slug + "-research.json")
        out_path.write_text(output, encoding="utf-8")
        print("Saved: " + str(out_path))
    else:
        try:
            print(output)
        except UnicodeEncodeError:
            sys.stdout.buffer.write(output.encode("utf-8"))


if __name__ == "__main__":
    main()

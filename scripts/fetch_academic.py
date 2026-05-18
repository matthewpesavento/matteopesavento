#!/usr/bin/env python3
"""
Fetches recent papers from Semantic Scholar for each journal/venue,
writes results to data/academic_papers.json.
Runs as a GitHub Action once daily.
"""

import json
import time
import requests
from pathlib import Path

VENUES = [
    {
        "id": "nber",
        "label": "NBER",
        "query": 'venue:"National Bureau of Economic Research"',
    },
    {
        "id": "jama",
        "label": "JAMA",
        "query": "venue:JAMA",
    },
    {
        "id": "aer",
        "label": "AER",
        "query": 'venue:"American Economic Review"',
    },
    {
        "id": "health-econ",
        "label": "Health Economics",
        "query": 'venue:"Journal of Health Economics"',
    },
    {
        "id": "qje",
        "label": "QJE",
        "query": 'venue:"The Quarterly Journal of Economics"',
    },
    {
        "id": "restat",
        "label": "REStat",
        "query": 'venue:"The Review of Economics and Statistics"',
    },
]

FIELDS = "title,authors,year,externalIds,openAccessPdf"
BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


def fetch_venue(venue):
    params = {
        "query": venue["query"],
        "fields": FIELDS,
        "limit": 5,
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        papers = []
        for p in data.get("data", []):
            doi   = (p.get("externalIds") or {}).get("DOI")
            arxiv = (p.get("externalIds") or {}).get("ArXiv")
            pdf   = (p.get("openAccessPdf") or {}).get("url")
            if doi:
                link = f"https://doi.org/{doi}"
            elif arxiv:
                link = f"https://arxiv.org/abs/{arxiv}"
            elif pdf:
                link = pdf
            else:
                link = None

            authors_list = p.get("authors") or []
            last_names   = [a["name"].split()[-1] for a in authors_list[:3]]
            authors_str  = ", ".join(last_names)
            if len(authors_list) > 3:
                authors_str += " et al."

            papers.append({
                "title":   p.get("title", "").strip(),
                "authors": authors_str,
                "year":    str(p.get("year", "")),
                "doi":     doi,
                "link":    link,
            })

        print(f"  {venue['id']}: fetched {len(papers)} papers")
        return papers

    except requests.exceptions.HTTPError as e:
        print(f"  {venue['id']}: HTTP error {e.response.status_code} — {e}")
        return []
    except Exception as e:
        print(f"  {venue['id']}: error — {e}")
        return []


def main():
    results = {}

    for i, venue in enumerate(VENUES):
        print(f"Fetching {venue['label']}...")
        papers = fetch_venue(venue)
        results[venue["id"]] = {
            "label":  venue["label"],
            "papers": papers,
        }
        # Semantic Scholar allows ~1 req/sec on the free tier
        # Wait 2 seconds between requests to stay well clear
        if i < len(VENUES) - 1:
            time.sleep(2)

    # Write output
    out_path = Path("data/academic_papers.json")
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    total = sum(len(v["papers"]) for v in results.values())
    print(f"\nDone — {total} papers written to {out_path}")


if __name__ == "__main__":
    main()

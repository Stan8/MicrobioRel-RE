#!/usr/bin/env python3
"""
Fill in pmid / doi / title / journal / year in 08_articles.csv.

Needs network access to Europe PMC (no API key required).
Run from the folder containing 08_articles.csv:

    pip install requests pandas
    python resolve_article_ids.py

Writes 08_articles.csv in place.
"""
import time
import pandas as pd
import requests

REST = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def fetch(pmcid):
    r = requests.get(
        REST,
        params={"query": f"PMCID:{pmcid}", "format": "json", "resultType": "core"},
        timeout=30,
    )
    r.raise_for_status()
    hits = r.json().get("resultList", {}).get("result", [])
    if not hits:
        return {}
    h = hits[0]
    return {
        "pmid": h.get("pmid", ""),
        "doi": h.get("doi", ""),
        "title": h.get("title", ""),
        "journal": h.get("journalTitle", ""),
        "year": h.get("pubYear", ""),
    }


def main():
    df = pd.read_csv("08_articles.csv", dtype=str).fillna("")
    for i, row in df.iterrows():
        if row["pmid"]:
            continue
        try:
            meta = fetch(row["PMC"])
        except Exception as exc:
            print(f"  {row['PMC']}: FAILED ({exc})")
            continue
        for k, v in meta.items():
            df.at[i, k] = v
        print(f"  {row['PMC']} -> pmid={meta.get('pmid','?')} doi={meta.get('doi','?')}")
        time.sleep(0.5)  # be polite to the API
    df.to_csv("08_articles.csv", index=False)
    n_ok = (df["pmid"] != "").sum()
    print(f"\nDone. {n_ok} / {len(df)} resolved.")


if __name__ == "__main__":
    main()

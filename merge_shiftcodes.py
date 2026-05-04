#!/usr/bin/env python3
"""
Merge shift codes from GitHub repositories and web scrapers.
"""

import json
import requests
from datetime import datetime, timezone
from collections import OrderedDict

from scrapers import mentalmars, gamedevtools, xsmashx88x

REPOS = [
    "https://raw.githubusercontent.com/Majawat/autoshift-codes/main/shiftcodes.json",
    "https://raw.githubusercontent.com/ugoogalizer/autoshift-codes/main/shiftcodes.json",
    "https://raw.githubusercontent.com/DankestMemeLord/autoshift-codes/main/shiftcodes.json",
    "https://raw.githubusercontent.com/zarmstrong/autoshift-codes/main/shiftcodes.json",
]

SCRAPERS = [
    mentalmars,
    gamedevtools,
    xsmashx88x,
]


def fetch_json(url):
    print(f"Fetching {url}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None


def merge_codes(all_data):
    """Merge codes from multiple sources, keeping the entry with the most recent archived date."""
    merged = OrderedDict()

    for data in all_data:
        if not data or not isinstance(data, list) or len(data) == 0:
            continue

        # Handles [{meta, codes}] (repo JSON) or a flat list of code dicts (scrapers)
        if isinstance(data[0], dict) and "codes" in data[0]:
            codes = data[0].get("codes", [])
        else:
            codes = data

        for entry in codes:
            if not isinstance(entry, dict):
                continue
            code = entry.get("code")
            if not code:
                continue

            if code in merged:
                if entry.get("archived", "") > merged[code].get("archived", ""):
                    merged[code] = entry
            else:
                merged[code] = entry

    return list(merged.values())


def main():
    print("Starting shift codes merge...\n")

    all_data = []

    # --- GitHub repos ---
    repo_count = 0
    for url in REPOS:
        data = fetch_json(url)
        if data:
            all_data.append(data)
            repo_count += 1
    print(f"\nFetched {repo_count}/{len(REPOS)} repositories")

    # --- Web scrapers ---
    print()
    scraper_total = 0
    for scraper in SCRAPERS:
        try:
            codes = scraper.scrape()
            if codes:
                all_data.append(codes)
                scraper_total += len(codes)
        except Exception as e:
            print(f"  [ERROR] {scraper.__name__} failed: {e}")

    print(f"\nScraped {scraper_total} codes from web sources")

    if not all_data:
        print("\nError: No data from any source!")
        return

    # --- Merge & sort ---
    merged = merge_codes(all_data)
    print(f"Total unique codes after merge: {len(merged)}")

    # Sort A→Z by game, then newest-first within each game
    merged.sort(key=lambda x: (x.get("game", ""), x.get("archived", "")), reverse=False)
    merged.sort(key=lambda x: x.get("game", ""))

    output = [
        {
            "meta": {
                "version": "0.1",
                "description": "GitHub Alternate Source for Shift Codes",
                "attribution": "Data sourced from mentalmars.com, gamedevtools.net, xsmashx88x.github.io, and GitHub forks",
                "permalink": "https://raw.githubusercontent.com/Majawat/autoshift-codes/main/shiftcodes.json",
                "generated": {
                    "human": datetime.now(timezone.utc).isoformat()
                },
                "newcodecount": len(merged)
            },
            "codes": merged
        }
    ]

    output_file = "shiftcodes.json"
    print(f"\nWriting to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] {len(merged)} unique codes written to {output_file}")


if __name__ == "__main__":
    main()

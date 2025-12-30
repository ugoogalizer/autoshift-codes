#!/usr/bin/env python3
"""
Merge shift codes from multiple GitHub repositories.
"""

import json
import requests
from datetime import datetime, timezone
from collections import OrderedDict

# URLs to fetch
REPOS = [
    "https://raw.githubusercontent.com/Majawat/autoshift-codes/main/shiftcodes.json",
    "https://raw.githubusercontent.com/ugoogalizer/autoshift-codes/main/shiftcodes.json",
    "https://raw.githubusercontent.com/DankestMemeLord/autoshift-codes/main/shiftcodes.json",
    "https://raw.githubusercontent.com/zarmstrong/autoshift-codes/main/shiftcodes.json",
]

def fetch_json(url):
    """Fetch JSON from a URL."""
    print(f"Fetching {url}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None

def merge_codes(all_data):
    """Merge codes from multiple JSON files, removing duplicates."""
    # Use a dict with code as key to automatically deduplicate
    merged_codes = OrderedDict()

    for data in all_data:
        if not data or not isinstance(data, list) or len(data) == 0:
            continue

        # Handle both formats: [{meta, codes}] or direct array
        if isinstance(data[0], dict) and "codes" in data[0]:
            codes = data[0].get("codes", [])
        else:
            codes = data

        for code_entry in codes:
            if not isinstance(code_entry, dict):
                continue

            code = code_entry.get("code")
            if not code:
                continue

            # Keep the entry with the most recent archived date
            if code in merged_codes:
                existing_archived = merged_codes[code].get("archived", "")
                new_archived = code_entry.get("archived", "")
                if new_archived > existing_archived:
                    merged_codes[code] = code_entry
            else:
                merged_codes[code] = code_entry

    return list(merged_codes.values())

def main():
    """Main merge function."""
    print("Starting shift codes merge...\n")

    # Fetch all JSON files
    all_data = []
    for url in REPOS:
        data = fetch_json(url)
        if data:
            all_data.append(data)

    if not all_data:
        print("\nError: No data fetched from any repository!")
        return

    print(f"\nSuccessfully fetched {len(all_data)} repositories")

    # Merge codes
    merged_codes = merge_codes(all_data)
    print(f"Total unique codes after merge: {len(merged_codes)}")

    # Sort codes by game, then by archived date (newest first)
    merged_codes.sort(key=lambda x: (
        x.get("game", ""),
        x.get("archived", "")
    ), reverse=True)

    # Create output structure
    output = [
        {
            "meta": {
                "version": "0.1",
                "description": "GitHub Alternate Source for Shift Codes",
                "attribution": "Data provided by https://mentalmars.com",
                "permalink": "https://raw.githubusercontent.com/Majawat/autoshift-codes/main/shiftcodes.json",
                "generated": {
                    "human": datetime.now(timezone.utc).isoformat()
                },
                "newcodecount": len(merged_codes)
            },
            "codes": merged_codes
        }
    ]

    # Write to file
    output_file = "shiftcodes.json"
    print(f"\nWriting merged data to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Merged {len(merged_codes)} unique shift codes!")
    print(f"[SUCCESS] Output written to {output_file}")

if __name__ == "__main__":
    main()

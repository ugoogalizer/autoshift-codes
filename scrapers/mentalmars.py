import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

from .utils import CODE_PATTERN, parse_date, format_expires

PAGES = [
    ("Borderlands 4",           "https://mentalmars.com/game-news/borderlands-4-shift-codes/"),
    ("Borderlands 3",           "https://mentalmars.com/game-news/borderlands-3-golden-keys/"),
    ("Tiny Tina's Wonderlands", "https://mentalmars.com/game-news/tiny-tinas-wonderlands-shift-codes/"),
    ("Borderlands 2",           "https://mentalmars.com/game-news/borderlands-2-golden-keys/"),
]

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; autoshift-scraper/1.0)"}


def _scrape_page(game, url):
    try:
        resp = requests.get(url, timeout=30, headers=_HEADERS)
        resp.raise_for_status()
    except Exception as e:
        print(f"  [mentalmars] Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    codes = []

    for table in soup.find_all("table"):
        thead = table.find("thead")
        if not thead:
            continue
        headers = [th.get_text(strip=True).lower() for th in thead.find_all("th")]

        # Require a column whose header contains "code"
        code_col = next((i for i, h in enumerate(headers) if "code" in h), None)
        if code_col is None:
            continue

        reward_col  = next((i for i, h in enumerate(headers) if "reward" in h), 0)
        added_col   = next((i for i, h in enumerate(headers) if "added" in h), 1)
        expires_col = next((i for i, h in enumerate(headers) if "expir" in h), 3)

        tbody = table.find("tbody")
        if not tbody:
            continue

        for row in tbody.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) <= code_col:
                continue

            code_cell = cells[code_col]
            code_tag  = code_cell.find("code")
            if not code_tag:
                continue

            code = code_tag.get_text(strip=True)
            if not CODE_PATTERN.match(code):
                continue

            expired = bool(code_cell.find("s"))

            reward      = cells[reward_col].get_text(" ", strip=True)  if len(cells) > reward_col  else ""
            added_str   = cells[added_col].get_text(strip=True)        if len(cells) > added_col   else ""
            expires_str = cells[expires_col].get_text(strip=True)      if len(cells) > expires_col else ""

            added_dt = parse_date(added_str)
            archived = (added_dt or datetime.now(timezone.utc)).isoformat()

            codes.append({
                "code":     code,
                "type":     "shift",
                "game":     game,
                "platform": "universal",
                "reward":   reward,
                "archived": archived,
                "expires":  format_expires(expires_str),
                "expired":  expired,
                "link":     url,
            })

    return codes


def scrape():
    print("Scraping mentalmars.com...")
    codes = []
    for game, url in PAGES:
        page_codes = _scrape_page(game, url)
        print(f"  {game}: {len(page_codes)} codes")
        codes.extend(page_codes)
    print(f"  Total from mentalmars: {len(codes)}")
    return codes


if __name__ == "__main__":
    for entry in scrape():
        print(entry)

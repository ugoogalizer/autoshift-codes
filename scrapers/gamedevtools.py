import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

from .utils import CODE_PATTERN, format_expires

PAGES = [
    ("Borderlands 4", "https://gamedevtools.net/shift-codes-borderlands-4"),
]

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; autoshift-scraper/1.0)"}

# en-dash or hyphen between code and description
_SEP = re.compile(r"\s*[–\-]+\s*")


def _scrape_page(game, url):
    try:
        resp = requests.get(url, timeout=30, headers=_HEADERS)
        resp.raise_for_status()
    except Exception as e:
        print(f"  [gamedevtools] Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    codes = []

    for li in soup.find_all("li"):
        strong = li.find("strong")
        if not strong:
            continue

        code = strong.get_text(strip=True)
        if not CODE_PATTERN.match(code):
            continue

        full_text = li.get_text(" ", strip=True)
        rest = _SEP.split(full_text[len(code):].strip(), maxsplit=1)
        description = rest[-1].strip() if rest else ""

        # Split "REWARD, expires DATE"
        expires_str = ""
        if re.search(r",\s*expires\s+", description, re.IGNORECASE):
            parts = re.split(r",\s*expires\s+", description, maxsplit=1, flags=re.IGNORECASE)
            reward      = parts[0].strip()
            expires_str = parts[1].strip()
        else:
            reward = description

        codes.append({
            "code":     code,
            "type":     "shift",
            "game":     game,
            "platform": "universal",
            "reward":   reward,
            "archived": datetime.now(timezone.utc).isoformat(),
            "expires":  format_expires(expires_str),
            "expired":  False,
            "link":     url,
        })

    return codes


def scrape():
    print("Scraping gamedevtools.net...")
    codes = []
    for game, url in PAGES:
        page_codes = _scrape_page(game, url)
        print(f"  {game}: {len(page_codes)} codes")
        codes.extend(page_codes)
    print(f"  Total from gamedevtools: {len(codes)}")
    return codes


if __name__ == "__main__":
    for entry in scrape():
        print(entry)

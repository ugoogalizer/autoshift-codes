import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

from .utils import CODE_PATTERN, parse_date

URL          = "https://xsmashx88x.github.io/bl4shiftcodes/"
EXPIRED_URL  = "https://raw.githubusercontent.com/xsmashx88x/-xsmashx88x/main/expired_codes.js"
GAME         = "Borderlands 4"

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; autoshift-scraper/1.0)"}

# Matches: createDate(2026, 5, 5, ...)
_CREATE_DATE = re.compile(r'createDate\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)')


def _parse_create_date(s):
    m = _CREATE_DATE.search(s)
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
    except ValueError:
        return None


_HTML_TAGS = re.compile(r'<[^>]+>')

def _get_str_field(entry, field):
    """Return the string value of a JS object field, respecting quote type."""
    # Try double-quoted value
    m = re.search(rf'{field}\s*:\s*"([^"]*)"', entry)
    if m:
        return _HTML_TAGS.sub('', m.group(1)).strip()
    # Try single-quoted value (may contain double quotes inside, e.g. HTML)
    m = re.search(rf"{field}\s*:\s*'([^']*)'", entry)
    if m:
        return _HTML_TAGS.sub('', m.group(1)).strip()
    return None


def _parse_expires(entry):
    m = re.search(r'expires\s*:\s*("UED"|createDate\([^)]+\)|[^,\n/]+)', entry)
    if not m:
        return "Unknown"
    val = m.group(1).strip()
    if val == '"UED"' or val == "UED":
        return "Never"
    dt = _parse_create_date(val)
    return dt.strftime("%Y-%m-%d") if dt else "Unknown"


def _parse_date_added(s):
    if not s:
        return None
    # xsmashx88x uses "2026-4-30" and "4/6/2026" — parse_date handles both
    return parse_date(s)


def _extract_array_content(script_text, var_name):
    """Return the text between the outer [ ] of a JS array declaration."""
    m = re.search(rf'const\s+{var_name}\s*=\s*\[', script_text)
    if not m:
        return ""
    depth = 0
    start = None
    for i in range(m.start(), len(script_text)):
        if script_text[i] == '[':
            if depth == 0:
                start = i + 1
            depth += 1
        elif script_text[i] == ']':
            depth -= 1
            if depth == 0:
                return script_text[start:i]
    return ""


def _extract_objects(array_text):
    """Return a list of raw { ... } object strings from a JS array."""
    objects, depth, start = [], 0, None
    for i, c in enumerate(array_text):
        if c == '{':
            if depth == 0:
                start = i
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0 and start is not None:
                objects.append(array_text[start:i + 1])
                start = None
    return objects


def _parse_entry(entry, expired=False):
    code = _get_str_field(entry, "code")
    if not code or not CODE_PATTERN.match(code):
        return None

    title        = _get_str_field(entry, "title") or ""
    date_added_s = _get_str_field(entry, "dateAdded") or ""

    archived_dt = _parse_date_added(date_added_s)
    archived    = (archived_dt or datetime.now(timezone.utc)).isoformat()

    return {
        "code":     code,
        "type":     "shift",
        "game":     GAME,
        "platform": "universal",
        "reward":   title,
        "archived": archived,
        "expires":  _parse_expires(entry),
        "expired":  expired,
        "link":     URL,
    }


def scrape():
    print("Scraping xsmashx88x.github.io...")
    try:
        resp = requests.get(URL, timeout=30, headers=_HEADERS)
        resp.raise_for_status()
    except Exception as e:
        print(f"  [xsmashx88x] Error fetching page: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    script_text = None
    for script in soup.find_all("script"):
        if script.string and "GOLD_KEYS_DATA" in script.string:
            script_text = script.string
            break

    if not script_text:
        print("  [xsmashx88x] Could not find data script block")
        return []

    inline_arrays = [
        ("GOLD_KEYS_DATA", False),
        ("SKINS_DATA",     False),
    ]

    codes = []
    for var_name, expired in inline_arrays:
        array_content = _extract_array_content(script_text, var_name)
        if not array_content:
            print(f"  [xsmashx88x] {var_name} not found")
            continue
        for obj in _extract_objects(array_content):
            entry = _parse_entry(obj, expired=expired)
            if entry:
                codes.append(entry)

    # Expired codes live in a separate raw JS file fetched at runtime
    try:
        exp_resp = requests.get(EXPIRED_URL, timeout=30, headers=_HEADERS)
        exp_resp.raise_for_status()
        exp_content = _extract_array_content(exp_resp.text, "EXPIRED_CODES_DATA")
        if exp_content:
            for obj in _extract_objects(exp_content):
                entry = _parse_entry(obj, expired=True)
                if entry:
                    codes.append(entry)
        else:
            print("  [xsmashx88x] EXPIRED_CODES_DATA not found in external file")
    except Exception as e:
        print(f"  [xsmashx88x] Error fetching expired codes: {e}")

    print(f"  Total from xsmashx88x: {len(codes)}")
    return codes


if __name__ == "__main__":
    for entry in scrape():
        print(entry)

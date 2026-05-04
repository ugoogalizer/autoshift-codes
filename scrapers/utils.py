import re
from datetime import datetime, timezone

CODE_PATTERN = re.compile(r'^[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}$')

_DATE_FORMATS = [
    "%b %d, %Y",   # May 1, 2026
    "%B %d, %Y",   # May 01, 2026
    "%d %B %Y",    # 1 May 2026
    "%d %b %Y",    # 1 May 2026 (abbrev)
    "%Y-%m-%d",    # 2026-05-01
    "%m/%d/%Y",    # 4/6/2026
]

def parse_date(s):
    if not s:
        return None
    s = s.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None

def format_expires(s):
    """Normalise an expiry string to YYYY-MM-DD, 'Never', or 'Unknown'."""
    dt = parse_date(s)
    if dt:
        return dt.strftime("%Y-%m-%d")
    if s and s.strip().lower() in ("never", "ued", "unlimited", "n/a"):
        return "Never"
    return "Unknown"

"""
AI News scraper — fetches RSS/Atom feeds from several AI news sources,
dedupes by link, sorts by date, and writes the result to news.json.

Zero dependencies: uses only the Python standard library.
"""

import json
import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# ---------------------------------------------------------------------------
# Sources (RSS/Atom feeds)
# ---------------------------------------------------------------------------
SOURCES = [
    {"name": "TechCrunch AI",       "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "The Verge AI",        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
    {"name": "VentureBeat AI",      "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "Wired AI",            "url": "https://www.wired.com/feed/tag/ai/latest/rss"},
    {"name": "Hacker News (AI)",    "url": "https://hnrss.org/newest?q=AI"},
]

MAX_ITEMS = 200          # cap on total items kept in news.json
FETCH_TIMEOUT = 15       # seconds per feed
USER_AGENT = "Mozilla/5.0 (AI-News-Scraper/1.0)"

# System cert store is broken on this machine, so skip verification.
# Fine for reading public news feeds; the data is not sensitive.
_SSL_CTX = ssl._create_unverified_context()

RSS_NS = "{http://purl.org/rss/1.0/modules/content/}"
DC_NS = "{http://purl.org/dc/elements/1.1/}"
ATOM_NS = "{http://www.w3.org/2005/Atom}"
MEDIA_NS = "{http://search.yahoo.com/mrss/}"


def fetch_feed(url: str) -> str | None:
    """Download a feed's raw XML. Returns None on failure."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT, context=_SSL_CTX) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [!] {url} -> {type(e).__name__}: {e}")
        return None


def _to_timestamp(value: str) -> float | None:
    """Best-effort parse of a date string (RFC822 or ISO 8601)."""
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).timestamp()
    except Exception:
        pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def _first_image(html: str) -> str | None:
    """Extract the first <img src=...> from HTML content."""
    if not html:
        return None
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I)
    if m and m.group(1).startswith(("http://", "https://")):
        return m.group(1)
    return None


def _strip_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _clean_summary(text: str) -> str:
    """Strip boilerplate (e.g. HN 'Article URL: ... Comments URL: ...')."""
    text = _strip_html(text)
    for marker in ("Article URL", "Comments URL", "Points:"):
        idx = text.find(marker)
        if idx != -1:
            text = text[:idx]
            break
    return text.strip()[:600]


def parse_rss(xml_text: str, source: str) -> list[dict]:
    """Parse an RSS 2.0 document into news items."""
    items = []
    root = ET.fromstring(xml_text)
    for it in root.iter("item"):
        def text(tag: str) -> str:
            el = it.find(tag)
            return (el.text or "").strip() if el is not None and el.text else ""

        link = text("link") or ""
        if not link:
            continue

        content_html = text(RSS_NS + "encoded") or text("description")
        summary = _clean_summary(content_html)
        published = text("pubDate") or text(DC_NS + "date")

        items.append({
            "title": text("title") or "(no title)",
            "link": link,
            "summary": summary[:600],
            "image": _first_image(content_html),
            "source": source,
            "published": published,
            "timestamp": _to_timestamp(published),
        })
    return items


def parse_atom(xml_text: str, source: str) -> list[dict]:
    """Parse an Atom document into news items."""
    items = []
    root = ET.fromstring(xml_text)
    for entry in root.iter(ATOM_NS + "entry"):
        def text(tag: str) -> str:
            el = entry.find(ATOM_NS + tag)
            return (el.text or "").strip() if el is not None and el.text else ""

        link_el = entry.find(ATOM_NS + "link")
        link = link_el.get("href", "") if link_el is not None else ""
        if not link:
            continue

        summary_html = text("summary") or text("content")
        published = text("published") or text("updated")

        items.append({
            "title": text("title") or "(no title)",
            "link": link,
            "summary": _clean_summary(summary_html),
            "image": _first_image(summary_html),
            "source": source,
            "published": published,
            "timestamp": _to_timestamp(published),
        })
    return items


def parse_feed(xml_text: str, source: str) -> list[dict]:
    try:
        root = ET.fromstring(xml_text)
        if root.tag == "feed" or root.tag == ATOM_NS + "feed":
            return parse_atom(xml_text, source)
        return parse_rss(xml_text, source)
    except ET.ParseError as e:
        print(f"  [!] {source}: XML parse error: {e}")
        return []


def scrape() -> list[dict]:
    print(f"Fetching {len(SOURCES)} feeds...")
    with ThreadPoolExecutor(max_workers=len(SOURCES)) as pool:
        results = list(pool.map(lambda s: (s, fetch_feed(s["url"])), SOURCES))

    all_items: list[dict] = []
    for source, xml_text in results:
        if not xml_text:
            continue
        parsed = parse_feed(xml_text, source["name"])
        print(f"  [OK] {source['name']}: {len(parsed)} items")
        all_items.extend(parsed)

    # Dedupe by link
    seen: set[str] = set()
    unique = []
    for item in all_items:
        key = item["link"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    # Sort newest first; items without a date go last
    unique.sort(key=lambda i: i["timestamp"] if i["timestamp"] is not None else 0, reverse=True)
    unique = unique[:MAX_ITEMS]

    return unique


def main() -> None:
    items = scrape()
    payload = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "count": len(items),
        "items": items,
    }
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(items)} items to news.json")


if __name__ == "__main__":
    main()

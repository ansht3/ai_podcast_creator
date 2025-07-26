"""Feed and article fetching utilities.

This module encapsulates all network operations for retrieving RSS feeds and
article contents.  It attempts to use third‑party libraries (`feedparser` and
`newspaper3k`) when available, but gracefully falls back to standard
libraries if they are not installed.  This design allows the program to run
in restricted environments while still providing higher‑quality extraction
when the optional packages are present.
"""

from __future__ import annotations

import datetime
import json
import logging
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

try:
    import feedparser  # type: ignore
except ImportError:
    feedparser = None  # type: ignore

try:
    from newspaper import Article  # type: ignore
except ImportError:
    Article = None  # type: ignore

try:
    from bs4 import BeautifulSoup  # type: ignore
except ImportError:
    BeautifulSoup = None  # type: ignore

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)


@dataclass
class FeedEntry:
    title: str
    link: str
    published: datetime.datetime


def parse_rss_feed(url: str) -> List[FeedEntry]:
    """Parse an RSS/Atom feed and return a list of entries.

    If the `feedparser` library is available it will be used.  Otherwise a
    lightweight regular expression–based parser will be employed.  The
    resulting entries contain the article title, link and published
    timestamp.

    :param url: URL to the feed.
    :returns: List of FeedEntry objects sorted by publication date (newest first).
    """
    entries: List[FeedEntry] = []

    # Common headers to avoid bot detection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }

    # Use feedparser if installed for robust parsing.
    if feedparser:
        logger.debug("Fetching feed %s using feedparser", url)
        feed = feedparser.parse(url)
        for entry in feed.entries:
            # Attempt to parse publication date; fall back to current time if missing.
            try:
                published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
                if published_parsed:
                    published = datetime.datetime.fromtimestamp(
                        datetime.datetime(*published_parsed[:6]).timestamp(), tz=datetime.timezone.utc
                    )
                else:
                    published = datetime.datetime.now(tz=datetime.timezone.utc)
            except Exception:
                published = datetime.datetime.now(tz=datetime.timezone.utc)

            entries.append(
                FeedEntry(
                    title=str(entry.get("title", "")),
                    link=str(entry.get("link", "")),
                    published=published,
                )
            )
    else:
        # Fallback: simple regex to extract <item> or <entry> elements.
        logger.debug("Fetching feed %s using regex fallback", url)
        if not requests:
            logger.error("requests library not available; cannot fetch feeds")
            return []
        try:
            resp = requests.get(url, timeout=10, headers=headers)
            resp.raise_for_status()
        except Exception as exc:
            logger.error("Failed to fetch feed %s: %s", url, exc)
            return []
        content = resp.text
        # Extract items
        item_pattern = re.compile(
            r"<item>(.*?)</item>", re.DOTALL | re.IGNORECASE
        )
        entries_raw = item_pattern.findall(content)
        for item in entries_raw:
            title_match = re.search(r"<title>(.*?)</title>", item, re.DOTALL | re.IGNORECASE)
            link_match = re.search(r"<link>(.*?)</link>", item, re.DOTALL | re.IGNORECASE)
            pub_match = re.search(
                r"<(?:pubDate|updated)>(.*?)</(?:pubDate|updated)>", item, re.DOTALL | re.IGNORECASE
            )
            title = title_match.group(1).strip() if title_match else ""
            link = link_match.group(1).strip() if link_match else ""
            pub_str = pub_match.group(1).strip() if pub_match else None
            try:
                published = (
                    datetime.datetime.strptime(pub_str, "%a, %d %b %Y %H:%M:%S %Z")
                    if pub_str
                    else datetime.datetime.now(tz=datetime.timezone.utc)
                )
            except Exception:
                published = datetime.datetime.now(tz=datetime.timezone.utc)
            if link:
                entries.append(FeedEntry(title=title, link=link, published=published))

    # Sort newest first
    return sorted(entries, key=lambda e: e.published, reverse=True)


def fetch_article_text(url: str) -> Optional[str]:
    """Download and extract the main text of an article from a URL.

    The function first attempts to use `newspaper3k` to perform robust
    extraction.  If the library is unavailable or fails for a particular
    article, a fallback that uses `BeautifulSoup` to extract the `<p>` tags
    will be used.  If both methods fail, `None` is returned.

    :param url: Article URL.
    :returns: Plain text of the article or None if extraction fails.
    """
    logger.debug("Fetching article %s", url)
    
    # Common headers to avoid bot detection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Try to use newspaper if installed
    if Article is not None:
        try:
            art = Article(url)
            art.download()
            art.parse()
            text = art.text
            if text:
                return text.strip()
        except Exception as exc:
            logger.warning("newspaper failed for %s: %s", url, exc)

    # Fallback: requests + BeautifulSoup
    if not requests or not BeautifulSoup:
        logger.error(
            "Cannot fetch article %s: missing dependencies (requests=%s, BeautifulSoup=%s)",
            url,
            bool(requests),
            bool(BeautifulSoup),
        )
        return None
    try:
        resp = requests.get(url, timeout=10, headers=headers)
        resp.raise_for_status()
    except Exception as exc:
        logger.error("Failed to download article %s: %s", url, exc)
        return None
    html = resp.text
    soup = BeautifulSoup(html, "html.parser")
    # Extract text from paragraph tags
    paragraphs = [p.get_text().strip() for p in soup.find_all("p") if p.get_text().strip()]
    if not paragraphs:
        return None
    return "\n".join(paragraphs)
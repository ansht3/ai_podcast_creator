"""Top‑level orchestration for the AI Podcast Producer.

This module coordinates the fetching of feeds and articles, summarisation and
text‑to‑speech generation.  It provides two entry points:

* `run_once()`: processes all configured feeds one time.
* `schedule_run()`: schedules `run_once` to run at a regular interval.

The state of the last processed article per feed is persisted between runs
using a JSON file.  If the state file does not exist, all articles in the
feeds will be considered new on the first run.
"""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import re
import time

import schedule

from config import (
    FEED_URLS,
    MAX_ARTICLES_PER_FEED,
    MAX_SUMMARY_SENTENCES,
    OUTPUT_DIR,
    RUN_EVERY_MINUTES,
    STATE_FILE,
    TTS_ENGINE,
    TTS_LANGUAGE,
)
from .fetcher import FeedEntry, fetch_article_text, parse_rss_feed
from .summariser import summarise
from .tts import get_tts_engine

logger = logging.getLogger(__name__)


def _load_state(path: Path) -> Dict[str, float]:
    """Load the persisted state from disk.

    The state maps feed URLs to the UNIX timestamp of the most recent
    processed article.  If the state file is missing or malformed, an empty
    dictionary is returned.

    :param path: Path to the JSON file.
    :returns: Mapping of feed URL to timestamp.
    """
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        # Ensure keys are strings and values are floats
        return {str(k): float(v) for k, v in data.items()}
    except Exception as exc:
        logger.warning("Failed to load state from %s: %s", path, exc)
        return {}


def _save_state(state: Dict[str, float], path: Path) -> None:
    """Persist the state dictionary to disk.

    :param state: Mapping of feed URL to timestamp.
    :param path: Path to write the JSON file to.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state), encoding="utf-8")
    except Exception as exc:
        logger.error("Failed to save state to %s: %s", path, exc)


def _process_entry(
    entry: FeedEntry,
    summary_dir: Path,
    tts_fn,
    feed_url: str,
    state: Dict[str, float],
) -> Optional[float]:
    """Process a single feed entry: fetch, summarise, synthesise.

    :param entry: The feed entry to process.
    :param summary_dir: Directory where output files will be saved.
    :param tts_fn: TTS function obtained via `get_tts_engine`.
    :param feed_url: URL of the feed (used for state updates).
    :param state: Mutable state mapping to update with latest timestamps.
    :returns: The published timestamp of the processed entry or None if skipped.
    """
    logger.info("Processing article: %s", entry.title)
    text = fetch_article_text(entry.link)
    if not text:
        logger.warning("Skipping article (no text extracted): %s", entry.link)
        return None
    summary = summarise(text, max_sentences=MAX_SUMMARY_SENTENCES)
    # Compose file names: slugify title for file naming
    safe_title = re.sub(r"[^a-zA-Z0-9_-]", "_", entry.title)[:50]
    timestamp_str = entry.published.strftime("%Y%m%dT%H%M%SZ")
    base_name = f"{timestamp_str}_{safe_title}" if safe_title else timestamp_str
    txt_path = summary_dir / f"{base_name}.txt"
    mp3_path = summary_dir / f"{base_name}.mp3"
    try:
        summary_dir.mkdir(parents=True, exist_ok=True)
        txt_path.write_text(summary, encoding="utf-8")
        # Generate audio
        tts_fn(summary, str(mp3_path), lang=TTS_LANGUAGE)
    except Exception as exc:
        logger.error("Failed to process article %s: %s", entry.link, exc)
        return None
    # Update state for this feed
    state[feed_url] = max(state.get(feed_url, 0.0), entry.published.timestamp())
    return entry.published.timestamp()


def run_once() -> None:
    """Run the entire pipeline once.

    This function fetches articles from each configured feed, summarises
    them and produces audio files.  It keeps track of the most recent
    publication dates to avoid processing the same articles again.  Errors
    are logged but do not stop the processing of other feeds.
    """
    logger.info("AI Podcast Producer run started")
    state = _load_state(STATE_FILE)
    tts_fn = get_tts_engine(TTS_ENGINE)
    today_dir = OUTPUT_DIR / datetime.datetime.now().strftime("%Y-%m-%d")
    for feed_url in FEED_URLS:
        logger.info("Fetching feed %s", feed_url)
        entries = parse_rss_feed(feed_url)
        if not entries:
            logger.warning("No entries parsed from feed %s", feed_url)
            continue
        # Determine cutoff timestamp
        last_ts = state.get(feed_url, 0.0)
        new_entries: List[FeedEntry] = []
        for entry in entries:
            if entry.published.timestamp() > last_ts:
                new_entries.append(entry)
        logger.info("Found %d new articles in feed %s", len(new_entries), feed_url)
        # Limit number of articles per feed
        if MAX_ARTICLES_PER_FEED is not None:
            new_entries = new_entries[:MAX_ARTICLES_PER_FEED]
        for entry in new_entries:
            _process_entry(entry, today_dir, tts_fn, feed_url, state)
    _save_state(state, STATE_FILE)
    logger.info("AI Podcast Producer run completed")


def schedule_run() -> None:
    """Schedule the pipeline to run periodically.

    Uses the `schedule` library to run `run_once` every
    `RUN_EVERY_MINUTES`.  This function blocks indefinitely.
    """
    logger.info("Scheduling AI Podcast Producer every %d minutes", RUN_EVERY_MINUTES)
    schedule.every(RUN_EVERY_MINUTES).minutes.do(run_once)
    # Run immediately once at start
    run_once()
    while True:
        schedule.run_pending()
        time.sleep(1)
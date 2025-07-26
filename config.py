"""Configuration for the AI Podcast Producer.

This module centralises all configuration values.  You can adjust feed URLs,
summary length, scheduling intervals and other parameters here without
touching the core logic.
"""

from pathlib import Path

# List of RSS or Atom feed URLs to monitor.  You can add any publicly
# available feeds here.  Avoid feeds that produce hundreds of articles per
# hour—processing will take longer and may overwhelm the summariser.
FEED_URLS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.npr.org/1004/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://feeds.reuters.com/Reuters/worldNews",
    "https://feeds.feedburner.com/TechCrunch/",
]

# Maximum number of articles to process from each feed on a single run.  This
# prevents the agent from spending too long catching up if it hasn't run in a
# while.  If set to None, all new articles will be processed.
MAX_ARTICLES_PER_FEED = 3

# Number of sentences to include in each summary.  Longer values produce
# lengthier audio segments; shorter values yield more concise digests.
MAX_SUMMARY_SENTENCES = 5

# Default language code for text‑to‑speech.  The value should be a BCP‑47
# language tag understood by your chosen TTS engine (for gTTS, examples
# include 'en' for English, 'es' for Spanish, etc.).
TTS_LANGUAGE = "en"

# Directory where generated summaries and audio files will be stored.  A new
# subdirectory named after the current date (YYYY‑MM‑DD) will be created
# automatically on each run.
OUTPUT_DIR = Path("output")

# Path to the file where state is persisted.  State tracks the last published
# timestamp processed for each feed so the agent can avoid reprocessing
# articles on subsequent runs.
STATE_FILE = Path("state.json")

# How often to run the job when scheduling is enabled (in minutes).  For
# example, setting this to 60 will run the agent once every hour when
# executing `python main.py --schedule`.
RUN_EVERY_MINUTES = 60

# Name of the TTS function to use.  The function should be defined in
# `ai_podcast_producer/src/tts.py` and must accept two positional
# arguments: the text to speak and the output file path.  When adding your
# own TTS engine, implement it there and set this constant to the name of
# your function.
TTS_ENGINE = "gtts_synthesise"

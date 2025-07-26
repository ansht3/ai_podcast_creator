# AI Podcast Producer

## Overview

**AI Podcast Producer** is a Python‑based tool for automatically generating short audio news digests.  The agent monitors a list of RSS feeds, downloads the latest articles, summarises their contents and then converts those summaries into spoken audio.  It can be run on demand or scheduled to run periodically using the built‑in scheduler.

The project is designed with scalability in mind.  Each stage of the pipeline—fetching feeds, downloading articles, summarising text and generating audio—is encapsulated in its own module.  This modular architecture allows you to swap out components (for example, replacing the summarisation algorithm or the text‑to‑speech engine) without affecting the rest of the system.  The orchestration layer can run tasks concurrently, so the program remains responsive even when processing many articles.

## Features

* **RSS monitoring** – Reads from a configurable list of RSS/Atom feeds to discover new content.  Only articles published after the last run are processed.
* **Article extraction** – Downloads the full text of each article.  By default, it uses the [newspaper3k](https://github.com/codelucas/newspaper) library when available, but falls back to a simple HTML parser if the library is not installed.
* **Summarisation** – Condenses long articles into a handful of sentences using a frequency–based summariser.  No external AI services are required, so the code runs anywhere Python does.
* **Text‑to‑speech (TTS)** – Converts each summary into an `.mp3` file using [gTTS](https://pypi.org/project/gTTS/).  If gTTS is not installed, the module exposes a hook where another TTS engine can be plugged in.
* **Scheduling** – The agent can run on a timer (e.g. every hour) using the built‑in `schedule` library.  Alternatively, you can invoke it manually by running `python main.py`.
* **Extensible** – Feeds, maximum number of articles, summary length, languages and other parameters are all configurable via `config.py`.

## Installation

1. **Clone the repository**

   ```bash
   git clone <your‑fork‑or‑repo‑url>
   cd ai_podcast_producer
   ```

2. **Create a virtual environment (recommended)**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**

   The project depends on a few third‑party libraries for fetching, parsing and speech synthesis.  Install them with pip:

   ```bash
   pip install -r requirements.txt
   ```

   If you cannot install optional packages like `newspaper3k` or `gTTS` due to network restrictions, the program will still run but may use simpler extraction and will skip audio generation.  See `src/tts.py` for details on plugging in an alternative TTS engine.

## Usage

### Run once

To fetch the latest articles, generate summaries and produce audio files, simply run:

```bash
python main.py
```

Summaries and audio files will be saved in the `output/` directory, organised by date.  A log of processed articles is stored in `ai_podcast_producer/state.json` to avoid processing the same article twice.

### Scheduled execution

To schedule the agent to run periodically (e.g. every hour), edit the `RUN_EVERY_MINUTES` value in `ai_podcast_producer/config.py`.  Then run:

```bash
python main.py --schedule
```

The scheduler uses the [schedule](https://pypi.org/project/schedule/) library internally and will block the process, executing the job at the configured interval.

### Customising feeds

The list of RSS/Atom feeds lives in `ai_podcast_producer/config.py` under the variable `FEED_URLS`.  Add or remove entries as needed.  The agent only processes articles published after the timestamp stored in `state.json`, so you can safely extend the list without re‑processing old stories.

### Changing summarisation behaviour

By default the summariser extracts the five most informative sentences from each article.  You can change this number by modifying `MAX_SUMMARY_SENTENCES` in `config.py`.  You can also replace the implementation in `src/summariser.py` with your favourite summarisation algorithm; just expose a `summarise(text: str, max_sentences: int) -> str` function.

### Using a different TTS engine

The default TTS implementation relies on the `gTTS` library, which sends a request to Google Translate to generate speech.  If you prefer to avoid external services or need offline synthesis, implement your own `synthesise_speech(text: str, filename: str)` function in `src/tts.py` and update the `TTS_ENGINE` constant in `config.py` to point to it.

## Repository structure

```
ai_podcast_producer/
│   README.md          Project documentation
│   requirements.txt   List of Python dependencies
│   main.py            Entry point for running the agent
│   config.py          Configuration variables
│   state.json         Stores timestamps of last processed articles
│
└───src/
    ├── __init__.py    Makes the src directory a package
    ├── fetcher.py     RSS feed and article fetching utilities
    ├── summariser.py  Text summarisation logic
    ├── tts.py         Text‑to‑speech helper functions
    └── producer.py    Orchestrates the end‑to‑end pipeline
```

## Contributing

Contributions are welcome!  Feel free to open issues or submit pull requests with improvements, bug fixes or new features.  Please ensure that your changes are covered by appropriate tests (if applicable) and that the documentation is updated accordingly.

## License

This project is provided under the MIT License.  See the `LICENSE` file for more information.
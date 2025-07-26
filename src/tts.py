"""Text‑to‑speech utilities.

This module contains functions for converting text into audio files.  The
default implementation relies on the `gTTS` library, which sends a request
to Google Translate to synthesise speech.  If `gTTS` is unavailable or if
you prefer to run offline, you can implement your own function with the
same signature and configure it via `config.TTS_ENGINE`.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def gtts_synthesise(text: str, filename: str, lang: str = "en") -> None:
    """Generate speech using the gTTS library and save it to an MP3 file.

    :param text: Text to speak.
    :param filename: Path to the output MP3 file.
    :param lang: Language code (default: 'en').
    :raises RuntimeError: If gTTS is not installed.
    """
    try:
        from gtts import gTTS  # type: ignore
    except ImportError:
        raise RuntimeError(
            "gTTS is not installed.  Install it via 'pip install gTTS' or select a different TTS engine."
        )
    # Ensure output directory exists
    out_path = Path(filename)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    logger.debug("Synthesising speech to %s", out_path)
    tts = gTTS(text=text, lang=lang)
    tts.save(str(out_path))


def noop_synthesise(text: str, filename: str, lang: str = "en") -> None:
    """Fallback TTS implementation that writes the text to a .txt file.

    In environments where no speech synthesis library is installed or network
    access is restricted, it may still be useful to persist summaries.  This
    function writes the plain text to a file with the same base name but
    `.txt` extension and logs a warning.  No audio is generated.

    :param text: Text to write to file.
    :param filename: Path where audio would have been saved (the .txt will
        replace the extension).
    :param lang: Unused parameter retained for signature compatibility.
    """
    out_path = Path(filename).with_suffix(".txt")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    logger.warning(
        "No TTS engine installed.  Writing summary text to %s instead of generating audio.",
        out_path,
    )
    out_path.write_text(text, encoding="utf-8")


def get_tts_engine(name: str) -> Callable[[str, str, str], None]:
    """Return a TTS function by name.

    The function should accept three positional arguments (text, filename,
    language).  If the requested engine is unknown, the `noop_synthesise`
    function is returned.

    :param name: Name of the TTS engine as configured in `config.TTS_ENGINE`.
    :returns: A callable for synthesising speech.
    """
    engines = {
        "gtts_synthesise": gtts_synthesise,
        "noop_synthesise": noop_synthesise,
    }
    engine = engines.get(name)
    if engine is None:
        logger.warning("Unknown TTS engine '%s'; falling back to noop_synthesise", name)
        return noop_synthesise
    return engine

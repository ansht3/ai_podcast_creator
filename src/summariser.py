"""Simple frequency‑based text summarisation.

This module implements a light‑weight extractive summariser that selects
the most informative sentences from an article.  It does not require
third‑party machine learning libraries and runs on the standard Python
library.  The algorithm follows these steps:

1. Tokenise the article into sentences.
2. Tokenise sentences into words, remove stop words and punctuation and
   compute word frequencies.
3. Score each sentence by summing the frequencies of its words.
4. Select the top N sentences by score and preserve their original order.

If the article has fewer sentences than the requested number, the full text
is returned.
"""

from __future__ import annotations

import logging
import re
from typing import List, Sequence, Tuple

logger = logging.getLogger(__name__)


# A basic set of common English stop words.  Extend this list if you wish
# to filter out additional low‑information words.  Avoid duplicates to
# improve performance.
STOP_WORDS = set(
    [
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "if",
        "while",
        "with",
        "for",
        "to",
        "of",
        "in",
        "on",
        "at",
        "by",
        "from",
        "this",
        "that",
        "these",
        "those",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "shall",
        "should",
        "can",
        "could",
        "may",
        "might",
        "must",
        "about",
        "into",
        "than",
        "as",
        "it",
        "its",
        "he",
        "she",
        "they",
        "them",
        "his",
        "her",
        "their",
        "we",
        "you",
        "your",
        "i",
        "me",
        "my",
        "mine",
        "ours",
        "ourselves",
    ]
)


def _split_sentences(text: str) -> List[str]:
    """Split a block of text into sentences using a regular expression.

    The regex looks for punctuation that typically signals the end of a
    sentence (periods, question marks, exclamation marks) followed by
    whitespace and an uppercase letter.  This heuristic works well for
    English prose but may not handle abbreviations perfectly.

    :param text: Raw article text.
    :returns: List of sentence strings.
    """
    # Normalise whitespace
    text = re.sub(r"\s+", " ", text.strip())
    # Use lookbehind to split at punctuation followed by space and capital letter
    sentence_endings = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
    sentences = sentence_endings.split(text)
    # Remove any empty sentences
    return [s.strip() for s in sentences if s.strip()]


def _tokenise(sentence: str) -> List[str]:
    """Split a sentence into lower‑case words and strip punctuation.

    :param sentence: A single sentence.
    :returns: List of cleaned word tokens.
    """
    # Remove non‑alphabetic characters and split on whitespace
    words = re.findall(r"\b[a-zA-Z']+\b", sentence.lower())
    return words


def summarise(text: str, max_sentences: int = 5) -> str:
    """Return a summary of the input text using at most `max_sentences`.

    When the article contains fewer sentences than `max_sentences`, the
    original text is returned unchanged.  Otherwise the top‐scoring sentences
    are selected based on word frequency.

    :param text: Full article text.
    :param max_sentences: Maximum number of sentences to include in the summary.
    :returns: A concise summary.
    """
    sentences = _split_sentences(text)
    logger.debug("Article split into %d sentences", len(sentences))
    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    # Compute word frequencies excluding stop words
    freq: dict[str, int] = {}
    for sentence in sentences:
        for word in _tokenise(sentence):
            if word in STOP_WORDS:
                continue
            freq[word] = freq.get(word, 0) + 1

    # Score sentences: sum of word frequencies normalised by sentence length
    scores: List[Tuple[int, float]] = []
    for idx, sentence in enumerate(sentences):
        words = _tokenise(sentence)
        if not words:
            scores.append((idx, 0.0))
            continue
        score = sum(freq.get(w, 0) for w in words) / len(words)
        scores.append((idx, score))

    # Select the top N sentences by score
    # Sorting by score descending, then by index ascending to favour earlier sentences
    top_indices = sorted(scores, key=lambda x: (-x[1], x[0]))[:max_sentences]
    # Restore original order
    top_indices_sorted = sorted(idx for idx, _ in top_indices)
    summary = " ".join(sentences[i] for i in top_indices_sorted)
    return summary
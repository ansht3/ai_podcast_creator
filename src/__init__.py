"""Top‑level package for AI Podcast Producer.

Exposes convenience functions to run the pipeline programmatically.
"""

from .producer import run_once, schedule_run

__all__ = ["run_once", "schedule_run"]
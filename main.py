"""Entry point for the AI Podcast Producer.

Run this module to fetch new articles, generate summaries and produce audio
files.  Use the `--schedule` flag to run the agent on a recurring basis.
"""

from __future__ import annotations

import argparse
import logging

from src.producer import run_once, schedule_run


def configure_logging(verbose: bool = False) -> None:
    """Configure the root logger.

    :param verbose: If true, set log level to DEBUG; otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="AI Podcast Producer")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="run continuously on a schedule defined in config.py",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="enable debug logging",
    )
    args = parser.parse_args(argv)
    configure_logging(args.verbose)
    if args.schedule:
        schedule_run()
    else:
        run_once()


if __name__ == "__main__":
    main()
"""Shared helpers for analyzing Claude Code session transcripts.

Both claude_models.py and claude_time.py reconstruct "active" time from the
JSONL transcripts Claude Code writes under ~/.claude/projects/, using the
same idle-gap cutoff, formatting, and file-walking logic. This module holds
that shared logic so future claude-analysis scripts have one place to
import it from instead of re-deriving it.
"""
import glob
import json
import os
from datetime import timedelta

IDLE = timedelta(minutes=5)  # gaps longer than this are breaks, not work


def iter_events():
    """Yield every parsed JSON event from every Claude Code session transcript.

    Walks ~/.claude/projects/*/*.jsonl, parsing each line as JSON. Lines that
    fail to parse are silently skipped.

    Yields:
        Tuples of (session_id, event), where session_id is the transcript's
        filename without extension, and event is the parsed JSON object for
        one line.
    """
    for path in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
        session_id = os.path.splitext(os.path.basename(path))[0]
        with open(path) as fh:
            for line in fh:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                yield session_id, event


def active(stamps):
    """Sum the working time spanned by a list of timestamps.

    Gaps longer than IDLE are treated as breaks and excluded.

    Args:
        stamps: List of timezone-aware datetimes for a single run.

    Returns:
        A timedelta of the active (non-idle) time across those stamps.
    """
    stamps = sorted(stamps)
    return sum(((b - a) for a, b in zip(stamps, stamps[1:]) if (b - a) <= IDLE), timedelta())


def fmt(d):
    """Format a timedelta as compact hours and minutes.

    Args:
        d: The timedelta to format.

    Returns:
        A string like ``"1h 05m"``.
    """
    t = int(d.total_seconds())
    return f"{t // 3600}h {t // 60 % 60:02d}m"

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


def usage_tokens(event):
    """Extract token counts from a transcript event's usage block.

    Only assistant events carry a usage block; any other event (or an
    assistant event predating a given field) yields zeroes for the missing
    counts rather than raising.

    Args:
        event: A parsed transcript event.

    Returns:
        A dict with integer keys ``"input"``, ``"output"``, ``"cache_write"``,
        and ``"cache_read"``.
    """
    usage = (event.get("message") or {}).get("usage") or {}
    return {
        "input": usage.get("input_tokens") or 0,
        "output": usage.get("output_tokens") or 0,
        "cache_write": usage.get("cache_creation_input_tokens") or 0,
        "cache_read": usage.get("cache_read_input_tokens") or 0,
    }


def sum_tokens(*token_dicts):
    """Add together any number of usage_tokens()-shaped dicts.

    Args:
        *token_dicts: Dicts as returned by usage_tokens().

    Returns:
        A dict with the same keys, each the sum across all inputs.
    """
    total = {"input": 0, "output": 0, "cache_write": 0, "cache_read": 0}
    for tokens in token_dicts:
        for key in total:
            total[key] += tokens.get(key, 0)
    return total


def fmt_tokens(n):
    """Format a token count compactly, abbreviating thousands/millions/billions.

    Args:
        n: The token count to format.

    Returns:
        A string like ``"142"``, ``"38K"``, ``"5.1M"``, ``"2.0G"``, or
        ``"1.2T"``.
    """
    if n >= 1_000_000_000_000:
        return f"{n / 1_000_000_000_000:.1f}T"
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}G"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)

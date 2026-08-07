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

    Plain (unitless) counts get a trailing space in place of a suffix
    letter, so that right-aligning a column of these strings lines up the
    digits regardless of whether any individual value has a suffix — e.g.
    ``"12 "`` and ``"12K"`` both put their final digit in the same column.

    Args:
        n: The token count to format.

    Returns:
        A string like ``"142 "``, ``"38K"``, ``"5.1M"``, ``"2.0G"``, or
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
    return f"{n} "


# ANSI colors for token-count suffixes, matching the low-to-high heat scale
# bin/progress-bar uses for its color-coded bars (blue < green < yellow <
# red), and the same escape codes as includes/colors.bash's IBlue/IGreen/
# IYellow/IRed.
_SUFFIX_COLORS = {
    "K": "\033[94m",
    "M": "\033[92m",
    "G": "\033[93m",
    "T": "\033[91m",
}
_COLOR_OFF = "\033[0m"


def color_tokens(n, width=7):
    """Format a token count, right-aligned, with its unit suffix colored.

    ANSI color codes are invisible characters that inflate a string's
    length without changing its rendered width, so the width-alignment
    must happen first and the color codes must be spliced in afterward —
    wrapping this function's result in another width format spec would
    miscount the invisible bytes and misalign the column.

    Args:
        n: The token count to format.
        width: The field width to right-align the plain digits+suffix to,
            before any color codes are added.

    Returns:
        A right-aligned, width-padded string with an ANSI-colored suffix
        (or no color, for a plain/unitless count).
    """
    padded = f"{fmt_tokens(n):>{width}}"
    suffix = padded[-1]
    color = _SUFFIX_COLORS.get(suffix)
    if not color:
        return padded
    return f"{padded[:-1]}{color}{suffix}{_COLOR_OFF}"


# Generic low-to-high heat scale for any 0-1 intensity value, matching
# bin/progress-bar's percentage bands (blue < 20%, green 20-49%, yellow
# 50-79%, red >= 80%) so a heatmap-style script reads consistently with
# everything else in bin/ that colors by magnitude.
_HEAT_BLOCKS = (" ", "░", "▒", "▓", "█")


def heat_ansi(fraction):
    """Return the ANSI color for a 0-1 intensity fraction.

    Args:
        fraction: A value from 0.0 to 1.0, e.g. a bucket's share of the
            busiest bucket in view.

    Returns:
        An ANSI color escape code string (blue/green/yellow/red by band).
    """
    pct = fraction * 100
    if pct >= 80:
        return "\033[91m"  # IRed
    if pct >= 50:
        return "\033[93m"  # IYellow
    if pct >= 20:
        return "\033[92m"  # IGreen
    return "\033[94m"  # IBlue


def heat_block(fraction):
    """Return a density block character for a 0-1 intensity fraction.

    Meant to be combined with heat_ansi() for a compact colored heatmap
    cell — density and color both track intensity.

    Args:
        fraction: A value from 0.0 to 1.0.

    Returns:
        One of " ", "░", "▒", "▓", "█", increasing in density with fraction.
    """
    if fraction <= 0:
        return _HEAT_BLOCKS[0]
    index = min(int(fraction * 4) + 1, 4)
    return _HEAT_BLOCKS[index]

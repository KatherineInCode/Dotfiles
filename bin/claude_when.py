#!/usr/bin/env python3
"""Time-of-day and day-of-week patterns in Claude Code, from session transcripts.

Walks every session log in ~/.claude/projects/, buckets active time by the
hour and weekday it happened in (local time), and prints one of three views.

    python3 claude_when.py                  # active time by hour of day
    python3 claude_when.py --by weekday      # active time by day of week
    python3 claude_when.py --by grid         # hour x weekday heatmap

Active time uses the same idle-gap cutoff as claude_models.py/claude_time.py
(active()), with one addition: a gap is attributed to the bucket of its
*start* timestamp rather than split across a boundary it straddles — a gap
from 23:58 to 00:03 counts entirely toward 23:00 on the day it started.
"""
import argparse
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta

from claude_sessions import IDLE, fmt, heat_ansi, heat_block, iter_events

WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_COLOR_OFF = "\033[0m"
_PROGRESS_BAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "progress-bar")

parser = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--by", choices=("hour", "weekday", "grid"), default="hour",
                     help="View to print (default: hour)")
args = parser.parse_args()


def bar(fraction, width=20):
    """Render a colored progress bar for a 0-1 intensity fraction.

    Shells out to bin/progress-bar so the bar matches the one used
    elsewhere in this repo (e.g. the statusline's context-usage bar)
    instead of a second, drifting reimplementation.

    Args:
        fraction: A value from 0.0 to 1.0.
        width: The bar's width in characters.

    Returns:
        The colored bar string, or an empty string if bin/progress-bar
        can't be found or run.
    """
    pct = str(round(max(0.0, min(1.0, fraction)) * 100))
    try:
        result = subprocess.run(
            [_PROGRESS_BAR, "-w", str(width), "-n", pct],
            capture_output=True, text=True, check=True)
        return result.stdout.rstrip("\n")
    except (OSError, subprocess.CalledProcessError):
        return ""


# Build a weekday x hour grid of active time and raw event counts.
active_grid = defaultdict(lambda: defaultdict(timedelta))  # [weekday][hour]
count_grid = defaultdict(lambda: defaultdict(int))          # [weekday][hour]

sessions = defaultdict(list)
for session_id, event in iter_events():
    ts = event.get("timestamp")
    if not ts:
        continue
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    sessions[session_id].append(dt)
    count_grid[dt.weekday()][dt.hour] += 1

for session_id, stamps in sessions.items():
    stamps.sort()
    for a, b in zip(stamps, stamps[1:]):
        gap = b - a
        if gap <= IDLE:
            active_grid[a.weekday()][a.hour] += gap

if not sessions:
    print("No session activity found in ~/.claude/projects/")
    sys.exit(0)


def trim_range(counts):
    """Find the index range spanning the first through last non-empty bucket.

    Drops only leading/trailing all-empty buckets (e.g. the dead overnight
    hours), not an isolated quiet bucket in the middle of an otherwise busy
    stretch.

    Args:
        counts: Ordered list of per-bucket event counts.

    Returns:
        A (start, end) tuple for slicing. If every bucket is empty, returns
        (0, len(counts)) so the view still prints instead of disappearing.
    """
    nonzero = [i for i, count in enumerate(counts) if count > 0]
    if not nonzero:
        return 0, len(counts)
    return nonzero[0], nonzero[-1] + 1


def print_bucket_view(header, labels, active_by_bucket, count_by_bucket):
    """Print a single-dimension active-time table with an intensity bar.

    Args:
        header: Column header for the bucket label ("hour" or "day").
        labels: Ordered display labels for each bucket (hour strings, or
            weekday abbreviations).
        active_by_bucket: List of timedeltas, active time per bucket, in
            the same order as labels.
        count_by_bucket: List of ints, event count per bucket, in the same
            order as labels.
    """
    busiest = max(active_by_bucket, default=timedelta())
    max_seconds = busiest.total_seconds() or 1
    print(f"{header:5} {'active':>8}  {'events':>7}  bar")
    for label, spent, count in zip(labels, active_by_bucket, count_by_bucket):
        fraction = spent.total_seconds() / max_seconds
        print(f"{label:5} {fmt(spent):>8}  {count:7}  {bar(fraction)}")


if args.by == "hour":
    active_by_hour = [sum((active_grid[w][h] for w in range(7)), timedelta()) for h in range(24)]
    count_by_hour = [sum(count_grid[w][h] for w in range(7)) for h in range(24)]
    labels = [f"{h:02d}" for h in range(24)]
    start, end = trim_range(count_by_hour)
    print_bucket_view("hour", labels[start:end], active_by_hour[start:end], count_by_hour[start:end])

elif args.by == "weekday":
    active_by_day = [sum(active_grid[w].values(), timedelta()) for w in range(7)]
    count_by_day = [sum(count_grid[w].values()) for w in range(7)]
    start, end = trim_range(count_by_day)
    print_bucket_view("day", list(WEEKDAY_NAMES[start:end]), active_by_day[start:end], count_by_day[start:end])

else:  # "grid"
    busiest = timedelta()
    for w in range(7):
        for h in range(24):
            busiest = max(busiest, active_grid[w][h])
    max_seconds = busiest.total_seconds() or 1

    row_counts = [sum(count_grid[w][h] for w in range(7)) for h in range(24)]
    col_counts = [sum(count_grid[w].values()) for w in range(7)]
    row_start, row_end = trim_range(row_counts)
    col_start, col_end = trim_range(col_counts)
    hours = range(row_start, row_end)
    weekdays = range(col_start, col_end)

    # Each column is 4 chars wide (1 separator space + 3-char content) in
    # both the header and the data rows, so they line up. Pad the plain
    # 2-char block to that width *before* adding color — ANSI codes are
    # invisible characters that would otherwise throw off the padding.
    print("    " + "".join(f" {WEEKDAY_NAMES[w]:>3}" for w in weekdays))
    for h in hours:
        row = [f"{h:02d}  "]
        for w in weekdays:
            fraction = active_grid[w][h].total_seconds() / max_seconds
            plain_cell = f"{heat_block(fraction) * 2:<3}"
            color = heat_ansi(fraction) if fraction > 0 else ""
            cell = f"{color}{plain_cell}{_COLOR_OFF}" if color else plain_cell
            row.append(f" {cell}")
        print("".join(row))

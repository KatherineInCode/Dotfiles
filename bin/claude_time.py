#!/usr/bin/env python3
"""Time and token usage in Claude Code, grouped by git branch.

Walks every session log in ~/.claude/projects/, buckets events by the git
branch each was recorded on, and prints active time and token usage per
branch. Token counts are raw counts, not dollar costs — there's no
per-model pricing here to keep in sync.

    python3 claude_time.py                    # all branches, most active first
    python3 claude_time.py vfo                 # only branches matching this substring
    python3 claude_time.py --sort branch       # alphabetical
    python3 claude_time.py --sort last -r      # most-recently-touched branches first

Magnitude sort keys (active, in, out, cache, events, turns) default to
descending (biggest first); branch/first/last default to ascending.
--reverse/-r flips whichever direction is the default for the chosen key.

"events" counts every logged event tagged with the branch (user turns,
tool results, meta events, sidechain — everything). "turns" counts only
interactive assistant turns (main thread, non-sidechain), matching how
claude_models.py defines it — a narrower, arguably truer measure of actual
back-and-forth on that branch.
"""
import argparse
import sys
from collections import defaultdict
from datetime import datetime

from claude_sessions import active, color_tokens, fmt, iter_events, sum_tokens, usage_tokens

SORT_KEYS = ("active", "in", "out", "cache", "events", "turns", "branch", "first", "last")
DESCENDING_BY_DEFAULT = {"active", "in", "out", "cache", "events", "turns"}  # branch/first/last are ascending

parser = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("needle", nargs="?", default="",
                     help="Only show branches matching this substring")
parser.add_argument("--sort", choices=SORT_KEYS, default="active",
                     help="Sort key (default: active)")
parser.add_argument("-r", "--reverse", action="store_true",
                     help="Reverse the default sort direction for --sort")
args = parser.parse_args()
needle = args.needle.lower()
reverse = (args.sort in DESCENDING_BY_DEFAULT) ^ args.reverse


def matches(branch):
    """Report whether a branch passes the command-line substring filter.

    Args:
        branch: The branch name to check.

    Returns:
        True when no filter was given, or the needle appears in the branch
        name (case-insensitive).
    """
    return not needle or needle in branch.lower()


def sort_value(branch, total, entry):
    """Compute the value to sort a branch row by.

    Args:
        branch: The branch name.
        total: The branch's active timedelta.
        entry: The branch's ``{"stamps": [...], "tokens": {...}, "turns":
            int}`` dict.

    Returns:
        The value corresponding to the module-level ``args.sort`` key.
    """
    if args.sort == "branch":
        return branch.lower()
    if args.sort == "first":
        return min(entry["stamps"])
    if args.sort == "last":
        return max(entry["stamps"])
    if args.sort == "events":
        return len(entry["stamps"])
    if args.sort == "turns":
        return entry["turns"]
    if args.sort in ("in", "out"):
        return entry["tokens"][{"in": "input", "out": "output"}[args.sort]]
    if args.sort == "cache":
        return entry["tokens"]["cache_write"] + entry["tokens"]["cache_read"]
    return total  # "active"


# Collect timestamps, token usage, and turn counts per branch from every transcript.
by_branch = defaultdict(lambda: {"stamps": [], "tokens": sum_tokens(), "turns": 0})
for _, event in iter_events():
    branch, ts = event.get("gitBranch"), event.get("timestamp")
    if branch and ts and matches(branch):
        entry = by_branch[branch]
        entry["stamps"].append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
        entry["tokens"] = sum_tokens(entry["tokens"], usage_tokens(event))
        if event.get("type") == "assistant" and not event.get("isSidechain"):
            entry["turns"] += 1

rows = [(active(v["stamps"]), branch, v) for branch, v in by_branch.items()]
if not rows:
    print("No matching branches found in ~/.claude/projects/")
    sys.exit(0)

rows.sort(key=lambda row: sort_value(row[1], row[0], row[2]), reverse=reverse)

print(f"{'branch':46} {'active':>10}  {'events':>7}  {'turns':>6}  {'in':>7} {'out':>7} {'cache':>7}  "
      f"first        last")
for total, branch, entry in rows:
    stamps = entry["stamps"]
    tokens = entry["tokens"]
    cache = tokens["cache_write"] + tokens["cache_read"]
    print(f"{branch[:46]:46} {fmt(total):>10}  {len(stamps):7}  {entry['turns']:6}  "
          f"{color_tokens(tokens['input'])} {color_tokens(tokens['output'])} {color_tokens(cache)}  "
          f"{min(stamps).strftime('%Y-%m-%d')}   {max(stamps).strftime('%Y-%m-%d')}")

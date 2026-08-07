#!/usr/bin/env python3
"""Time and token usage in Claude Code, grouped by git branch.

Walks every session log in ~/.claude/projects/, buckets events by the git
branch each was recorded on, and prints active time and token usage per
branch. Token counts are raw counts, not dollar costs — there's no
per-model pricing here to keep in sync.

    python3 claude_time.py            # all branches
    python3 claude_time.py vfo        # only branches matching this substring
"""
import sys
from collections import defaultdict
from datetime import datetime

from claude_sessions import active, color_tokens, fmt, iter_events, sum_tokens, usage_tokens

needle = sys.argv[1].lower() if len(sys.argv) > 1 else ""


def matches(branch):
    """Report whether a branch passes the command-line substring filter.

    Args:
        branch: The branch name to check.

    Returns:
        True when no filter was given, or the needle appears in the branch
        name (case-insensitive).
    """
    return not needle or needle in branch.lower()


# Collect timestamps and token usage per branch from every transcript.
by_branch = defaultdict(lambda: {"stamps": [], "tokens": sum_tokens()})
for _, event in iter_events():
    branch, ts = event.get("gitBranch"), event.get("timestamp")
    if branch and ts and matches(branch):
        entry = by_branch[branch]
        entry["stamps"].append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
        entry["tokens"] = sum_tokens(entry["tokens"], usage_tokens(event))

rows = sorted(
    ((active(v["stamps"]), branch, v) for branch, v in by_branch.items()),
    reverse=True,
)
if not rows:
    print("No matching branches found in ~/.claude/projects/")
    sys.exit(0)

print(f"{'branch':46} {'active':>10}  {'events':>7}  {'in':>7} {'out':>7} {'cache':>7}  first        last")
for total, branch, entry in rows:
    stamps = entry["stamps"]
    tokens = entry["tokens"]
    cache = tokens["cache_write"] + tokens["cache_read"]
    print(f"{branch[:46]:46} {fmt(total):>10}  {len(stamps):7}  "
          f"{color_tokens(tokens['input'])} {color_tokens(tokens['output'])} {color_tokens(cache)}  "
          f"{min(stamps).strftime('%Y-%m-%d')}   {max(stamps).strftime('%Y-%m-%d')}")

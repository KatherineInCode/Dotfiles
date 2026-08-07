#!/usr/bin/env python3
"""Time spent in Claude Code, grouped by git branch.

Walks every session log in ~/.claude/projects/, buckets events by the git
branch each was recorded on, and prints active time per branch.

    python3 claude_time.py            # all branches
    python3 claude_time.py vfo        # only branches matching this substring
"""
import sys
from collections import defaultdict
from datetime import datetime

from claude_sessions import active, fmt, iter_events

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


# Collect timestamps per branch from every transcript.
by_branch = defaultdict(list)
for _, event in iter_events():
    branch, ts = event.get("gitBranch"), event.get("timestamp")
    if branch and ts and matches(branch):
        by_branch[branch].append(datetime.fromisoformat(ts.replace("Z", "+00:00")))

rows = sorted(((active(v), k, len(v)) for k, v in by_branch.items()), reverse=True)
if not rows:
    print("No matching branches found in ~/.claude/projects/")
    sys.exit(0)

print(f"{'branch':46} {'active':>10}  {'events':>7}  first        last")
for total, branch, count in rows:
    stamps = by_branch[branch]
    print(f"{branch[:46]:46} {fmt(total):>10}  {count:7}  "
          f"{min(stamps).strftime('%Y-%m-%d')}   {max(stamps).strftime('%Y-%m-%d')}")

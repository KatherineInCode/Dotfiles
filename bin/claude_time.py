#!/usr/bin/env python3
"""Time spent in Claude Code, grouped by git branch.
    python3 claude_time.py            # all branches
    python3 claude_time.py vfo        # only branches matching this substring
"""
import glob, json, os, sys
from collections import defaultdict
from datetime import datetime, timedelta

IDLE = timedelta(minutes=5)   # gaps longer than this are breaks, not work

needle = sys.argv[1].lower() if len(sys.argv) > 1 else ""
by_branch = defaultdict(list)

for path in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
    with open(path) as fh:
        for line in fh:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            branch, ts = event.get("gitBranch"), event.get("timestamp")
            if branch and ts and needle in branch.lower():
                by_branch[branch].append(datetime.fromisoformat(ts.replace("Z", "+00:00")))

def active(stamps):
    stamps.sort()
    return sum(((b - a) for a, b in zip(stamps, stamps[1:]) if (b - a) <= IDLE), timedelta())

def fmt(d):
    t = int(d.total_seconds())
    return f"{t // 3600}h {t // 60 % 60:02d}m"

rows = sorted(((active(v), k, len(v)) for k, v in by_branch.items()), reverse=True)
if not rows:
    print("No matching branches found in ~/.claude/projects/")
    sys.exit(0)
print(f"{'branch':46} {'active':>10}  {'events':>7}  first        last")
for total, branch, count in rows:
    s = by_branch[branch]
    print(f"{branch[:46]:46} {fmt(total):>10}  {count:7}  "
          f"{min(s).strftime('%Y-%m-%d')}   {max(s).strftime('%Y-%m-%d')}")
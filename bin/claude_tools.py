#!/usr/bin/env python3
"""Tool-use breakdown for Claude Code, reconstructed from session transcripts.

Walks every session log in ~/.claude/projects/, tallies every tool_use block
by tool name (Bash, Edit, Read, Write, Agent, ...), and prints counts sorted
by frequency. Subagent (sidechain) tool calls are included, since they're
real tool invocations regardless of which thread made them.

    python3 claude_tools.py           # every tool
    python3 claude_tools.py bash      # only tools matching this substring
"""
import argparse
import sys
from collections import Counter

from claude_sessions import iter_events

parser = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("needle", nargs="?", default="",
                     help="Only show tools matching this substring")
args = parser.parse_args()
needle = args.needle.lower()


def matches(tool_name):
    """Report whether a tool name passes the command-line substring filter.

    Args:
        tool_name: The tool name to check.

    Returns:
        True when no filter was given, or the needle appears in the tool
        name (case-insensitive).
    """
    return not needle or needle in tool_name.lower()


# Tally every tool_use block across every transcript.
counts = Counter()
for _, event in iter_events():
    if event.get("type") != "assistant":
        continue
    content = (event.get("message") or {}).get("content")
    if not isinstance(content, list):
        continue
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            name = block.get("name")
            if name:
                counts[name] += 1

if not counts:
    print("No tool use found in ~/.claude/projects/")
    sys.exit(0)

total = sum(counts.values())
rows = [(name, count) for name, count in counts.most_common() if matches(name)]

if not rows:
    print(f"No tools matching '{needle}' found in ~/.claude/projects/")
    sys.exit(0)

print(f"{'count':>8}  {'%':>6}  tool")
for name, count in rows:
    print(f"{count:8}  {count / total * 100:5.1f}%  {name}")
print(f"\n{total:8}  {'':>6}  total tool calls (all tools, unfiltered)")

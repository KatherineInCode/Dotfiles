#!/usr/bin/env python3
"""Model-usage timeline for Claude Code, reconstructed from session transcripts.

Walks every session log in ~/.claude/projects/, collapses each session's
assistant turns into consecutive runs of the same model and effort level, and
prints a chronological timeline of what was active when — flagging mid-session
switches of either — along with token usage per run.

    python3 claude_models.py                    # every session, chronological
    python3 claude_models.py opus                # only runs matching this substring
    python3 claude_models.py high                # (matches model and effort, e.g. "high")
    python3 claude_models.py --sort active       # longest-active runs first
    python3 claude_models.py --sort cache -r     # least cache tokens first

--sort applies to both the timeline and the totals-by-model/effort table
below it. Magnitude sort keys (active, in, out, cache, turns) default to
descending (biggest first); "when" defaults to ascending (oldest first).
--reverse/-r flips whichever direction is the default for the chosen key.

Times are shown in local time. Sidechain (subagent) turns and synthetic
messages are ignored so the timeline reflects the interactive model only.
Token counts are raw counts, not dollar costs — there's no per-model pricing
here to keep in sync.
"""
import argparse
import sys
from collections import defaultdict
from datetime import datetime, timedelta

from claude_sessions import active, color_tokens, fmt, iter_events, sum_tokens, usage_tokens

SORT_KEYS = ("when", "active", "in", "out", "cache", "turns")
DESCENDING_BY_DEFAULT = {"active", "in", "out", "cache", "turns"}  # "when" is ascending

parser = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("needle", nargs="?", default="",
                     help="Only show runs matching this substring (model or effort)")
parser.add_argument("--sort", choices=SORT_KEYS, default="when",
                     help="Sort key for both tables (default: when)")
parser.add_argument("-r", "--reverse", action="store_true",
                     help="Reverse the default sort direction for --sort")
args = parser.parse_args()
needle = args.needle.lower()
reverse = (args.sort in DESCENDING_BY_DEFAULT) ^ args.reverse


def collapse(events):
    """Collapse time-ordered assistant turns into consecutive same-model/effort runs.

    Args:
        events: List of (datetime, model, effort, tokens) tuples for one
            session, any order; ``effort`` may be None when the turn
            predates the field, and ``tokens`` is a usage_tokens()-shaped
            dict for that turn.

    Returns:
        A list of runs in chronological order, each a dict with keys
        ``model`` (str), ``effort`` (str or None), ``stamps`` (list of
        datetimes), and ``tokens`` (usage_tokens()-shaped dict, summed
        across the whole run).
    """
    runs = []
    for ts, model, effort, tokens in sorted(events, key=lambda e: e[0]):
        if runs and runs[-1]["model"] == model and runs[-1]["effort"] == effort:
            runs[-1]["stamps"].append(ts)
            runs[-1]["tokens"] = sum_tokens(runs[-1]["tokens"], tokens)
        else:
            runs.append({"model": model, "effort": effort, "stamps": [ts], "tokens": tokens})
    return runs


def short_model(model):
    """Trim the redundant ``claude-`` prefix from a model id for display.

    Args:
        model: A full model id such as ``"claude-opus-4-8"``.

    Returns:
        The model id without a leading ``claude-``.
    """
    return model[len("claude-"):] if model.startswith("claude-") else model


def sort_value(spent, tokens, turns, when):
    """Compute the value to sort a timeline row or totals row by.

    Args:
        spent: The row's active timedelta.
        tokens: The row's usage_tokens()-shaped token dict.
        turns: The row's turn count.
        when: The row's representative timestamp (a run's start, or a
            totals group's earliest run start).

    Returns:
        The value corresponding to the module-level ``args.sort`` key.
    """
    if args.sort == "when":
        return when
    if args.sort == "active":
        return spent
    if args.sort == "in":
        return tokens["input"]
    if args.sort == "out":
        return tokens["output"]
    if args.sort == "cache":
        return tokens["cache_write"] + tokens["cache_read"]
    return turns  # "turns"


# Collect (timestamp, model, effort, tokens) per session from every transcript.
sessions = defaultdict(list)
for session_id, event in iter_events():
    if event.get("type") != "assistant" or event.get("isSidechain"):
        continue
    ts = event.get("timestamp")
    model = (event.get("message") or {}).get("model")
    if not ts or not model or model.startswith("<"):
        continue
    sessions[session_id].append((
        datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(),
        model,
        event.get("effort"),
        usage_tokens(event),
    ))


def matches(model, effort):
    """Report whether a run passes the command-line substring filter.

    Args:
        model: The run's full model id.
        effort: The run's effort level, or None.

    Returns:
        True when no filter was given, or the needle appears in the combined
        "model effort" text (case-insensitive).
    """
    return not needle or needle in f"{model} {effort or ''}".lower()


# Flatten every session's runs into one timeline, tracking mid-session switches.
timeline = []          # (start, model, effort, active, tokens, count, session_id, is_switch)
totals = defaultdict(lambda: {"active": timedelta(), "tokens": sum_tokens(), "turns": 0, "first": None})
for session_id, events in sessions.items():
    runs = collapse(events)
    for index, run in enumerate(runs):
        stamps = run["stamps"]
        spent = active(stamps)
        start = min(stamps)
        key = (run["model"], run["effort"])
        totals[key]["active"] += spent
        totals[key]["tokens"] = sum_tokens(totals[key]["tokens"], run["tokens"])
        totals[key]["turns"] += len(stamps)
        if totals[key]["first"] is None or start < totals[key]["first"]:
            totals[key]["first"] = start
        if not matches(run["model"], run["effort"]):
            continue
        timeline.append(
            (start, run["model"], run["effort"], spent, run["tokens"], len(stamps), session_id, index > 0)
        )

if not timeline:
    print("No matching model usage found in ~/.claude/projects/")
    sys.exit(0)

timeline.sort(
    key=lambda row: sort_value(row[3], row[4], row[5], row[0]),
    reverse=reverse,
)
print(f"{'when':16}  {'model':18} {'effort':7} {'active':>8}  {'in':>7} {'out':>7} {'cache':>7}  "
      f"{'turns':>6}  {'session':8}  switch")
for start, model, effort, spent, tokens, count, session_id, is_switch in timeline:
    marker = "↳ switched" if is_switch else ""
    cache = tokens["cache_write"] + tokens["cache_read"]
    print(f"{start.strftime('%Y-%m-%d %H:%M'):16}  {short_model(model):18} {effort or '-':7} "
          f"{fmt(spent):>8}  {color_tokens(tokens['input'])} {color_tokens(tokens['output'])} "
          f"{color_tokens(cache)}  {count:6}  {session_id[:8]:8}  {marker}")

print(f"\n{'total by model / effort':26}  {'active':>8}  {'in':>7} {'out':>7} {'cache':>7}  {'turns':>6}")
sorted_totals = sorted(
    totals.items(),
    key=lambda kv: sort_value(kv[1]["active"], kv[1]["tokens"], kv[1]["turns"], kv[1]["first"]),
    reverse=reverse,
)
for (model, effort), total in sorted_totals:
    if not matches(model, effort):
        continue
    tokens = total["tokens"]
    cache = tokens["cache_write"] + tokens["cache_read"]
    print(f"{short_model(model) + ' / ' + (effort or '-'):26}  {fmt(total['active']):>8}  "
          f"{color_tokens(tokens['input'])} {color_tokens(tokens['output'])} {color_tokens(cache)}  "
          f"{total['turns']:6}")

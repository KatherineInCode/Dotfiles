#!/usr/bin/env python3
"""Model-usage timeline for Claude Code, reconstructed from session transcripts.

Walks every session log in ~/.claude/projects/, collapses each session's
assistant turns into consecutive runs of the same model and effort level, and
prints a chronological timeline of what was active when — flagging mid-session
switches of either.

    python3 claude_models.py           # every session
    python3 claude_models.py opus      # only runs matching this substring
    python3 claude_models.py high      # (matches model and effort, e.g. "high")

Times are shown in local time. Sidechain (subagent) turns and synthetic
messages are ignored so the timeline reflects the interactive model only.
"""
import sys
from collections import defaultdict
from datetime import datetime, timedelta

from claude_sessions import active, fmt, iter_events

needle = sys.argv[1].lower() if len(sys.argv) > 1 else ""


def collapse(events):
    """Collapse time-ordered assistant turns into consecutive same-model/effort runs.

    Args:
        events: List of (datetime, model, effort) tuples for one session, any
            order; ``effort`` may be None when the turn predates the field.

    Returns:
        A list of runs in chronological order, each a dict with keys ``model``
        (str), ``effort`` (str or None), and ``stamps`` (list of datetimes).
    """
    runs = []
    for ts, model, effort in sorted(events, key=lambda e: e[0]):
        if runs and runs[-1]["model"] == model and runs[-1]["effort"] == effort:
            runs[-1]["stamps"].append(ts)
        else:
            runs.append({"model": model, "effort": effort, "stamps": [ts]})
    return runs


def short_model(model):
    """Trim the redundant ``claude-`` prefix from a model id for display.

    Args:
        model: A full model id such as ``"claude-opus-4-8"``.

    Returns:
        The model id without a leading ``claude-``.
    """
    return model[len("claude-"):] if model.startswith("claude-") else model


# Collect (timestamp, model, effort) per session from every transcript.
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
timeline = []          # (start, model, effort, active, count, session_id, is_switch)
totals = defaultdict(timedelta)
for session_id, events in sessions.items():
    runs = collapse(events)
    for index, run in enumerate(runs):
        stamps = run["stamps"]
        spent = active(stamps)
        totals[(run["model"], run["effort"])] += spent
        if not matches(run["model"], run["effort"]):
            continue
        timeline.append(
            (min(stamps), run["model"], run["effort"], spent, len(stamps), session_id, index > 0)
        )

if not timeline:
    print("No matching model usage found in ~/.claude/projects/")
    sys.exit(0)

timeline.sort(key=lambda row: row[0])
print(f"{'when':16}  {'model':18} {'effort':7} {'active':>8}  {'turns':>6}  {'session':8}  switch")
for start, model, effort, spent, count, session_id, is_switch in timeline:
    marker = "↳ switched" if is_switch else ""
    print(f"{start.strftime('%Y-%m-%d %H:%M'):16}  {short_model(model):18} {effort or '-':7} "
          f"{fmt(spent):>8}  {count:6}  {session_id[:8]:8}  {marker}")

print(f"\n{'total by model / effort':26}  {'active':>8}")
for (model, effort), spent in sorted(totals.items(), key=lambda kv: kv[1], reverse=True):
    if not matches(model, effort):
        continue
    print(f"{short_model(model) + ' / ' + (effort or '-'):26}  {fmt(spent):>8}")

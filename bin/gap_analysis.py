#!/usr/bin/env python3
"""Measure cache-miss causes and gap distribution from Claude Code transcripts.

Answers the question "would ENABLE_PROMPT_CACHING_1H=1 pay for itself here?"
without needing an experiment — every fact required is already in the local
session logs.

A cold turn is directly observable: cache_creation >> cache_read means the
prefix had to be rebuilt rather than re-read. Pairing that with the gap since
the previous request tells you WHY it went cold:

  gap > 60 min   -> would still miss under a 1-hour TTL (no help)
  5-60 min       -> a 1-hour TTL would have SAVED this one
  gap < 5 min    -> TTL wasn't the cause (model switch, MCP reconnect, upgrade)

Reads nothing but token counts and timestamps. No message content is read,
printed, or written anywhere, and nothing leaves the machine.

Usage:
  python3 gap_analysis.py [options] [file.jsonl ...]

  With no file arguments it reads every transcript under ~/.claude/projects.

Options:
  --redact      Key each row by session id instead of project path. Use this
                for output you are sending to someone else -- project
                directories encode your working directory.
  --summary     Print only the break-even percentage and the verdict.
  --verbose     Show the per-session table, gap distribution and full arithmetic.
  --top N       With --verbose, show only the N largest sessions.
  -h, --help    Show this message.
  --version     Print the version and exit.

Also reports how many keep-alive pings would have paid for this user: pinging
re-reads the context at 0.10x to reset the TTL, which synthesises a longer
effective TTL while keeping the cheap 1.25x write rate.
"""
import json, sys, glob, os, collections, math
from datetime import datetime

__version__ = "1.18"

W5M, W1H, READ = 1.25, 2.00, 0.10
RATE_ASSUMED = 5.00                         # Opus 5 input $/MTok, used throughout
RATE = {"claude-opus-5": 5.00, "claude-opus-4-8": 5.00, "claude-sonnet-5": 3.00,
        "claude-sonnet-4-6": 3.00, "claude-haiku-4-5-20251001": 1.00}

BREAK_EVEN = (W1H - W5M) / (W1H - READ)     # 0.395 — see "the decision" below

# Keep-alive ping model. A ping re-reads the whole context at 0.10x, which resets
# the TTL. Capped at N consecutive unanswered pings it synthesises an effective
# TTL of TTL + N x INTERVAL while still paying the cheap 1.25x write rate.
# The marginal Nth ping is worth firing only if more than READ/(W5M-READ) of the
# gaps that reach it end in the interval it buys.
# Two variants, because the setting you actually run changes the answer. Under a
# 1-hour TTL a rebuild costs 2.00x rather than 1.25x AND each ping covers 12x more
# wall-clock, so more pings become worth firing.
PING_VARIANTS = (
    dict(name="5-min TTL", ttl=300.0, interval=285.0, wmult=W5M,
         note="pings every 4:45"),
    dict(name="1-hour TTL", ttl=3600.0, interval=3300.0, wmult=W1H,
         note="ENABLE_PROMPT_CACHING_1H=1 set, pings every 55 min"),
)
PING_SCAN = 25                              # caps evaluated
PING_ROWS = 10                              # rows printed
BORDERLINE = 0.03                            # +/- 3pp around it reads as a tie
DEFAULT_TOP = None   # show every session; --top N trims the list


def ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def requests(path):
    """Deduped, time-ordered requests carrying usage."""
    seen, out = set(), []
    for line in open(path, errors="replace"):
        try:
            d = json.loads(line)
        except Exception:
            continue
        m = d.get("message") or {}
        u = m.get("usage") or d.get("usage")
        if not u:
            continue
        key = m.get("id") or d.get("requestId") or d.get("uuid")
        if key in seen:
            continue
        seen.add(key)
        t = ts(d.get("timestamp") or "")
        if not t:
            continue
        out.append(dict(t=t, model=m.get("model") or "?",
                        effort=d.get("effort"), ver=d.get("version"),
                        side=d.get("isSidechain"),
                        read=u.get("cache_read_input_tokens", 0),
                        write=u.get("cache_creation_input_tokens", 0),
                        out=u.get("output_tokens", 0)))
    out.sort(key=lambda r: r["t"])
    return out


def label_for(path, redact):
    """A row label the developer can recognise. Project directories encode the
    working directory, so --redact falls back to the opaque session id for
    output that will be shared with someone else."""
    sid = os.path.basename(path).split(".")[0][:8]
    if redact:
        return sid
    parts = [p for p in os.path.basename(os.path.dirname(path)).split("-") if p]
    tail = "-".join(parts[-2:]) if len(parts) >= 2 else (parts[0] if parts else "?")
    return f"{tail[:20]} {sid[:6]}"


def analyse_one(path):
    """Per-session stats. Summing these reproduces the global totals exactly."""
    rs = requests(path)
    total_w = saveable = 0
    buckets = collections.Counter()
    btok = collections.Counter()
    gap_events = []                         # (gap seconds, write tokens) for cold rebuilds
    causes = collections.Counter()          # write tokens by why they were written
    gaps, cold = [], 0
    for i, r in enumerate(rs):
        total_w += r["write"]
        if i == 0:
            causes["Session Start, First Prefix Write"] += r["write"]
            continue
        prev = rs[i - 1]
        _cold = r["write"] > max(r["read"], 1) and r["write"] > 10_000
        _g = (r["t"] - prev["t"]).total_seconds()
        if not r["write"]:
            pass
        elif not _cold:
            causes["Ordinary Turn Append"] += r["write"]
        elif _g > 300:
            causes["__idle__"] += r["write"]     # split by window in the report
        elif r["model"] != prev["model"]:
            causes["Cold: Model Switch"] += r["write"]
        elif r["effort"] != prev["effort"]:
            causes["Cold: Effort Switch"] += r["write"]
        elif r["ver"] != prev["ver"]:
            causes["Cold: Claude Code Upgrade"] += r["write"]
        elif r["side"] != prev["side"]:
            causes["Cold: Subagent Boundary"] += r["write"]
        else:
            causes["Cold: Cause Not Listed"] += r["write"]
        gap = (r["t"] - rs[i - 1]["t"]).total_seconds()
        gaps.append(gap)
        if not (r["write"] > max(r["read"], 1) and r["write"] > 10_000):
            continue
        cold += 1
        gap_events.append((gap, r["write"]))
        if gap > 3600:
            buckets[">60 min — 1h TTL would NOT have helped"] += 1
            btok[">60 min — 1h TTL would NOT have helped"] += r["write"]
        elif gap > 300:
            buckets["5-60 min — a 1h TTL WOULD have saved this"] += 1
            btok["5-60 min — a 1h TTL WOULD have saved this"] += r["write"]
            saveable += r["write"]
        else:
            buckets["<5 min — TTL not the cause (switch/reconnect/upgrade)"] += 1
            btok["<5 min — TTL not the cause (switch/reconnect/upgrade)"] += r["write"]
    return dict(path=path, n=len(rs), gaps=gaps, cold=cold, buckets=buckets,
                btok=btok, total_w=total_w, saveable=saveable,
                gap_events=gap_events, causes=causes)


def costs(total_w, saveable, rate=RATE_ASSUMED):
    """Write-side cost under each TTL.

    Under 5-min (what actually happened): every cache_creation token at 1.25x.
    Under 1-hour (counterfactual): the rebuilds caused by 5-60 min gaps would
    not have occurred, so those tokens become cache READS at 0.1x; every write
    that DOES still happen costs 2x instead of 1.25x.

    An earlier version applied the 2x premium to the full observed write volume,
    including the rebuilds a 1-hour TTL would have prevented. That double-counted
    and reversed the verdict.
    """
    still = max(total_w - saveable, 0)
    return (total_w * W5M * rate / 1e6,
            (still * W1H + saveable * READ) * rate / 1e6)


def verdict_for(share):
    if share >= BREAK_EVEN + BORDERLINE:
        return "enable"
    if share >= BREAK_EVEN - BORDERLINE:
        return "borderline"
    return "leave default"


def human(tok):
    if tok >= 1e9:
        return f"{tok / 1e9:.1f}B"
    if tok >= 1e6:
        return f"{tok / 1e6:.1f}M"
    if tok >= 1e3:
        return f"{tok / 1e3:.0f}K"
    return str(tok)


def print_table(sessions, top, redact):
    rows = sorted(sessions, key=lambda s: s["total_w"], reverse=True)
    shown, hidden = (rows, []) if top is None else (rows[:top], rows[top:])
    hdr = (f"{'Session':<28}{'Requests':>9}{'Writes':>9}{'Gap-caused':>12}"
           f"{'$ 5-min':>10}{'$ 1-hour':>10}  {'Enable 1H'}")
    print(hdr)
    print("-" * (len(hdr) + 7))
    for s in shown:
        if not s["total_w"]:
            continue
        share = s["saveable"] / s["total_w"]
        c5, c1 = costs(s["total_w"], s["saveable"])
        print(f"{label_for(s['path'], redact):<28}{s['n']:>9,}"
              f"{human(s['total_w']):>9}{share * 100:>11.0f}%"
              f"{c5:>10,.2f}{c1:>10,.2f}  {verdict_for(share)}")
    tw = sum(s["total_w"] for s in sessions)
    sv = sum(s["saveable"] for s in sessions)
    c5, c1 = costs(tw, sv)
    print("-" * (len(hdr) + 7))
    print(f"{'ALL SESSIONS':<28}{sum(s['n'] for s in sessions):>9,}"
          f"{human(tw):>9}{sv / tw * 100 if tw else 0:>11.0f}%"
          f"{c5:>10,.2f}{c1:>10,.2f}  {verdict_for(sv / tw if tw else 0)}")
    print("\n  The TTL applies to every session, so this column is hindsight, "
          "not a per-session choice.")
    if hidden:
        ht = sum(s["total_w"] for s in hidden)
        print(f"\n  ({len(hidden)} smaller session(s) not shown, {human(ht)} of "
              f"writes — included in the ALL SESSIONS row. Use --top to see them.)")


KNOWN_FLAGS = {"--redact", "--summary", "--top", "-h", "--help", "--version",
               "--verbose"}


def _derive(gap_events, v):
    """(pings needed to bridge, write tokens) for gaps this variant would act on."""
    return [(max(1, math.ceil((g - v["ttl"]) / v["interval"])), w)
            for g, w in gap_events if g > v["ttl"]]


def ping_net(derived, cap, wmult):
    """Net value of allowing at most `cap` consecutive keep-alive pings.

    Bridged gap: the rebuild (wmult) becomes cap-many reads plus one warm read,
    saving w x (wmult - READ - READ*n). Un-bridged: the pings are spent and the
    rebuild is still paid, costing cap x w x READ.
    """
    saved = sum(w * (wmult - READ - READ * n) * RATE_ASSUMED / 1e6
                for n, w in derived if n <= cap)
    waste = sum(cap * w * READ * RATE_ASSUMED / 1e6
                for n, w in derived if n > cap)
    return saved - waste


def best_cap(gap_events, v):
    derived = _derive(gap_events, v)
    if not derived:
        return 0, 0.0
    scored = [(k, ping_net(derived, k, v["wmult"])) for k in range(1, PING_SCAN + 1)]
    k, net = max(scored, key=lambda kv: kv[1])
    return (k, net) if net > 0 else (0, 0.0)


def report_pings(gap_events, ttl_delta, base_cost):
    """How many keep-alive pings would have paid, under each TTL setting."""
    print("\n--- keep-alive ping ---")
    print("  A ping re-reads the context at 0.10x, resetting the TTL. Capped at N")
    print("  unanswered pings it synthesises a longer effective TTL. The marginal")
    print("  ping pays only if more than READ/(rebuild-READ) of the gaps reaching")
    print("  it end in the interval it buys.")
    out = {}
    for v in PING_VARIANTS:
        derived = _derive(gap_events, v)
        thresh = READ / (v["wmult"] - READ)
        print(f"\n  == {v['name']} ({v['note']}) ==")
        print(f"     rebuild {v['wmult']:.2f}x -> a ping must beat "
              f"{thresh * 100:.1f}% hazard")
        if not derived:
            print("     no gaps beyond this TTL — nothing for a keep-alive to do")
            out[v["name"]] = (0, 0.0)
            continue
        print(f"\n     {'ping':>4}{'eff TTL':>11}{'reach it':>10}{'end here':>10}"
              f"{'hazard':>9}{'net if capped here':>21}")
        for k in range(1, PING_ROWS + 1):
            reach = sum(1 for n, _ in derived if n >= k)
            ends = sum(1 for n, _ in derived if n == k)
            if not reach:
                break
            eff = (v["interval"] * k + v["ttl"]) / 60
            eff_s = f"{eff:.1f}m" if eff < 120 else f"{eff / 60:.1f}h"
            print(f"     {k:>4}{eff_s:>11}{reach:>10}{ends:>10}"
                  f"{ends / reach * 100:>8.1f}%"
                  f"{ping_net(derived, k, v['wmult']):>+20,.2f}")
        beyond = sum(1 for n, _ in derived if n > PING_ROWS)
        if beyond:
            print(f"     {'>' + str(PING_ROWS):>4}{'':>11}{beyond:>10}")
        cap, net = best_cap(gap_events, v)
        out[v["name"]] = (cap, net)
        if cap:
            eff = (v["interval"] * cap + v["ttl"]) / 60
            eff_s = f"{eff:.1f} min" if eff < 120 else f"{eff / 60:.1f} hours"
            print(f"\n     -> best cap {cap} ping(s), an effective TTL of {eff_s}, "
                  f"worth ${net:+,.2f}")
        else:
            print("\n     -> no cap pays: a keep-alive is not worth running here")
    c5 = out.get("5-min TTL", (0, 0.0))
    c1 = out.get("1-hour TTL", (0, 0.0))
    print("\n  what each configuration costs:")
    print(f"    {'change nothing':<32}${base_cost:>9,.2f}")
    print(f"    {'5-min TTL + ' + str(c5[0]) + ' ping(s)':<32}"
          f"${base_cost - c5[1]:>9,.2f}   saves ${c5[1]:,.2f}")
    print(f"    {'1-hour TTL alone':<32}${base_cost - ttl_delta:>9,.2f}"
          f"   saves ${ttl_delta:,.2f}")
    print(f"    {'1-hour TTL + ' + str(c1[0]) + ' ping(s)':<32}"
          f"${base_cost - ttl_delta - c1[1]:>9,.2f}   saves "
          f"${ttl_delta + c1[1]:,.2f}")
    return c5, c1


def clock(seconds):
    """MM:SS up to 100 minutes, then H:MM:SS. Never decimal -- a reader should not
    have to convert 2.8 hours in their head."""
    seconds = int(round(seconds))
    if seconds < 6000:
        return f"{seconds // 60}:{seconds % 60:02d}"
    return f"{seconds // 3600}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


def report_headline(nsess, nreq, sessions, total_w, share, cost_5m, cost_1h,
                    cap5, net5, cap1, net1):
    """Default output. Costs first, all measured against the CURRENT 5-minute TTL;
    reasons and savings second."""
    events = [e for s_ in sessions for e in s_["gap_events"]]
    price = lambda w: w * W5M * RATE_ASSUMED / 1e6
    v5, v1 = PING_VARIANTS
    eff5 = v5["ttl"] + cap5 * v5["interval"]        # what pings alone would reach
    eff1 = v1["ttl"] + cap1 * v1["interval"]        # ...with the 1-hour TTL as well
    w_ping = sum(w for g, w in events if v5["ttl"] < g <= eff5)
    w_ttl = sum(w for g, w in events if v5["ttl"] < g <= v1["ttl"])

    print(f"gap_analysis.py {__version__}")
    print(f"{nsess} sessions, {nreq:,} requests, "
          f"{total_w / 1e6:,.1f}M cache-write tokens")
    print(f"Your cache expires after {clock(v5['ttl'])} of inactivity.\n")

    # One line per recommendation, non-overlapping, summing to the total. The cost
    # of the fixes (a higher write rate, the pings themselves) belongs in the
    # recommendation that incurs it -- not here, where we are sizing the problem.
    w_ttl = sum(w for g, w in events if v5["ttl"] < g <= v1["ttl"])
    w_ping = sum(w for g, w in events if v1["ttl"] < g <= eff1) if cap1 else 0
    w_other = max(total_w - w_ttl - w_ping, 0)
    L = 42
    print("What Your Cache Writes Cost\n")
    print(f"  {'All Cache Writes':<{L}}${price(total_w):>8,.2f}   100%")
    print(f"    {'Rebuilt After Idle Of ' + clock(v5['ttl']) + ' To ' + clock(v1['ttl']):<{L-2}}"
          f"${price(w_ttl):>8,.2f}{w_ttl / total_w * 100:>6.0f}%")
    if cap1:
        print(f"    {'Rebuilt After Idle Of ' + clock(v1['ttl']) + ' To ' + clock(eff1):<{L-2}}"
              f"${price(w_ping):>8,.2f}{w_ping / total_w * 100:>6.0f}%")
    print(f"    {'Other Reasons':<{L-2}}"
          f"${price(w_other):>8,.2f}{w_other / total_w * 100:>6.0f}%")
    causes = collections.Counter()
    for s_ in sessions:
        causes.update(s_["causes"])
    w_beyond = max(causes.pop("__idle__", 0) - w_ttl - w_ping, 0)
    sub = [(f"Idle Beyond {clock(eff1)}", w_beyond)] if w_beyond else []
    sub += [(k, v) for k, v in causes.most_common() if v]
    for label, w in sorted(sub, key=lambda kv: -kv[1]):
        print(f"      {label:<{L-4}}${price(w):>8,.2f}"
              f"{w / total_w * 100:>6.1f}%")

    print("\nRecommendations\n")
    ttl_saves = cost_5m - cost_1h
    n = 1
    if ttl_saves > 0:
        print(f"  {n}. Set ENABLE_PROMPT_CACHING_1H=1 before starting Claude Code")
        print(f"     Recovers the {clock(v5['ttl'])} to {clock(v1['ttl'])} line above. "
              f"Net ${ttl_saves:,.2f} after the")
        print(f"     higher write rate a longer TTL charges.")
        n += 1
    else:
        print(f"  {n}. Leave the cache TTL alone")
        print(f"     Recovering that line would cost ${-ttl_saves:,.2f} more than it "
              f"saves, because")
        print(f"     only {share * 100:.0f}% of your writes are rebuilds and it needs "
              f"{BREAK_EVEN * 100:.0f}%.")
        n += 1
    final = cost_1h if ttl_saves > 0 else cost_5m
    if ttl_saves > 0 and cap1:
        print(f"\n  {n}. Install our keep-alive script, set to give up after {cap1} "
              f"unanswered pings")
        print(f"     Recovers the {clock(v1['ttl'])} to {clock(eff1)} line. "
              f"Net ${net1:,.2f} after the cost")
        print(f"     of the pings themselves.")
        final -= net1
        n += 1
    elif cap5:
        print(f"\n  {n}. Install our keep-alive script, set to give up after {cap5} "
              f"unanswered pings")
        print(f"     Extends cache life to {clock(v5['ttl'] + cap5 * v5['interval'])}. "
              f"Net ${net5:,.2f}.")
        final -= net5
        n += 1
    print(f"\n  {n}. Install our status line to see when your cache next expires")
    print(f"     Shows a live countdown and what a rebuild would cost at your")
    print(f"     current context size, so the items above are visible as you work.")
    saved = cost_5m - final
    print(f"\n  Together your cache writes would cost ${final:,.2f} instead of "
          f"${cost_5m:,.2f} —")
    print(f"  a saving of ${saved:,.2f} ({saved / cost_5m * 100:.0f}%)")

    print("\n  --verbose for per-session detail and the arithmetic")


def main():
    argv = sys.argv[1:]
    if "--version" in argv:
        print(f"gap_analysis.py {__version__}")
        return
    if "-h" in argv or "--help" in argv:
        print(__doc__.strip())
        return
    # Fail loudly on a mistyped flag. Silently ignoring "--redacted" would print
    # project paths while the user believed they were redacted.
    unknown = [a for a in argv if a.startswith("-") and a not in KNOWN_FLAGS]
    if unknown:
        print(f"unknown option(s): {' '.join(unknown)}\n", file=sys.stderr)
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    redact = "--redact" in argv
    summary = "--summary" in argv
    verbose = "--verbose" in argv
    top = DEFAULT_TOP
    if "--top" in argv:
        i = argv.index("--top")
        try:
            top = int(argv[i + 1]); argv.pop(i + 1)
        except (IndexError, ValueError):
            pass
    paths = [a for a in argv if not a.startswith("--")]
    if not paths:
        paths = glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))

    sessions = [analyse_one(p) for p in paths]
    total_w = sum(s["total_w"] for s in sessions)
    saveable = sum(s["saveable"] for s in sessions)
    share = saveable / total_w if total_w else 0.0
    cost_5m, cost_1h = costs(total_w, saveable)
    delta = cost_5m - cost_1h

    ping_events = [e for s_ in sessions for e in s_["gap_events"]]
    if summary:
        k5, n5 = best_cap(ping_events, PING_VARIANTS[0])
        k1, n1 = best_cap(ping_events, PING_VARIANTS[1])
        print(f"{share * 100:.0f}% gap-caused (break-even {BREAK_EVEN * 100:.0f}%) -> "
              f"{'ENABLE 1H' if delta > 0 else 'LEAVE DEFAULT'} ${delta:+,.2f}; "
              f"ping cap 5m={k5} (${n5:+,.2f}) 1h={k1} (${n1:+,.2f}); "
              f"best combo ${delta + n1:+,.2f}")
        return

    n = sum(s["n"] for s in sessions)
    k5, nt5 = best_cap(ping_events, PING_VARIANTS[0])
    k1, nt1 = best_cap(ping_events, PING_VARIANTS[1])
    report_headline(len(paths), n, sessions, total_w, share,
                    cost_5m, cost_1h, k5, nt5, k1, nt1)
    if not verbose:
        return
    print(f"\n{'=' * 68}\ntranscripts: {len(paths)}   "
          f"requests with usage: {n:,}\n")
    start_w = sum(s_["causes"].get("Session Start, First Prefix Write", 0)
                  for s_ in sessions)
    print("session shape:")
    print(f"  requests per session       {n / len(paths):>12,.1f}")
    print(f"  prefix tokens per start    {start_w / len(paths):>12,.0f}\n")

    gaps = sorted(g for s in sessions for g in s["gaps"])
    if gaps:
        def pct(p):
            return gaps[min(int(len(gaps) * p), len(gaps) - 1)]
        print("gap between consecutive requests (seconds):")
        for label, p in (("p50", .50), ("p75", .75), ("p90", .90), ("p99", .99)):
            print(f"  {label} {pct(p):>10,.0f}s")
        over5 = sum(1 for g in gaps if g > 300)
        over60 = sum(1 for g in gaps if g > 3600)
        print(f"  gaps > 5 min : {over5:,} ({over5 / len(gaps) * 100:.1f}%)")
        print(f"  gaps > 60 min: {over60:,} ({over60 / len(gaps) * 100:.1f}%)\n")

    buckets, btok = collections.Counter(), collections.Counter()
    for s in sessions:
        buckets.update(s["buckets"]); btok.update(s["btok"])
    print(f"cold prefix rebuilds detected: {sum(s['cold'] for s in sessions)}")
    for b, c in buckets.most_common():
        tok = btok[b]
        # Only the 5-60 min bucket has a saving attached: those writes become
        # 0.1x reads under a 1-hour TTL. The other buckets get written either
        # way, so quoting a dollar figure against them would be meaningless.
        gain = (f"   worth ${tok * (W5M - READ) * 5.00 / 1e6:,.2f}"
                if b.startswith("5-60") else "")
        print(f"  {c:>5}  {b:<54}{human(tok):>8} tok{gain}")

    print("\n--- per session ---")
    print_table(sessions, top, redact)

    print("\n--- the decision ---")
    print(f"  observed cache writes            {total_w:>14,} tokens")
    print(f"    of which rebuilds a 1h TTL")
    print(f"    would have prevented           {saveable:>14,} tokens")
    print(f"    still written either way       {max(total_w - saveable, 0):>14,} tokens")
    print(f"\n  write-side cost at 5-min TTL     ${cost_5m:>10.2f}   (all writes x1.25)")
    print(f"  write-side cost at 1-hour TTL    ${cost_1h:>10.2f}   "
          f"(x2.00 on what remains, x0.10 on the rest)")
    win = lose = 0.0
    nwin = nlose = 0
    for s_ in sessions:
        if not s_["total_w"]:
            continue
        a, b = costs(s_["total_w"], s_["saveable"])
        if a - b > 0:
            win += a - b; nwin += 1
        else:
            lose += b - a; nlose += 1
    print(f"\n  applied globally, as it must be:")
    print(f"    {nwin} session(s) benefit                 ${win:>+10,.2f}")
    print(f"    {nlose} session(s) made worse              ${-lose:>+10,.2f}")
    print(f"    net                                    ${win - lose:>+10,.2f}")

    still = max(total_w - saveable, 0)
    print(f"\n  gain on rebuilds a 1h TTL prevents  ${saveable * (W5M - READ) * 5.00 / 1e6:>+10,.2f}"
          f"   ({human(saveable)} x {W5M - READ:.2f})")
    print(f"  premium on writes that still happen ${-still * (W1H - W5M) * 5.00 / 1e6:>+10,.2f}"
          f"   ({human(still)} x {W1H - W5M:.2f})")
    print(f"\n  -> {'ENABLE the 1-hour TTL' if delta > 0 else 'LEAVE the default'}"
          f"   (1-hour TTL is ${delta:+.2f} vs 5-min)")
    if total_w:
        print(f"     break-even needs {BREAK_EVEN * 100:.0f}% of write volume to be "
              f"gap-caused rebuilds; here it is {share * 100:.0f}%")
    report_pings(ping_events, delta, cost_5m)

    print(f"\n  NB priced at Opus rates throughout, and write-side only — this is not\n"
          f"  your bill. Sessions on cheaper models scale down proportionally; the\n"
          f"  ratio, and so the verdict, is unchanged.")


if __name__ == "__main__":
    main()

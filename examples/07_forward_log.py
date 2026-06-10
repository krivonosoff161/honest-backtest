# -*- coding: utf-8 -*-
"""Layer 6 — log the decision BEFORE the outcome exists; score only what you couldn't know."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from backtest_sanity import ForwardLog                              # noqa: E402
from backtest_sanity._synth import toy_returns                      # noqa: E402

rets = toy_returns(40, edge=0.001, seed=3)          # synthetic 'future' the logger can't peek at

with tempfile.TemporaryDirectory() as tmp:
    log = ForwardLog(path=str(Path(tmp) / "forward_log.jsonl"))

    # t=0..29: record a decision per period — naive rule: repeat yesterday's sign.
    # The outcome (rets[t]) is NOT written here; at decision time it doesn't exist yet.
    for t in range(1, 31):
        side = "long" if rets[t - 1] > 0 else "short"
        log.record({"id": t, "type": "decision", "side": side})

    # later, as each period closes, append the realized outcome under the same id
    for t in range(1, 31):
        log.record({"id": t, "type": "outcome", "ret": float(rets[t])})

    # replay: join decisions with outcomes by id — this is the only honest scoreboard
    rows = log.rows()
    decisions = {r["id"]: r for r in rows if r["type"] == "decision"}
    outcomes = {r["id"]: r for r in rows if r["type"] == "outcome"}
    pnl = [(o["ret"] if decisions[i]["side"] == "long" else -o["ret"])
           for i, o in outcomes.items()]
    hits = sum(1 for x in pnl if x > 0)

    print("decisions logged: %d, outcomes joined: %d" % (len(decisions), len(outcomes)))
    print("hit-rate: %d/%d, mean per-period pnl: %.5f" % (hits, len(pnl), sum(pnl) / len(pnl)))

print("\nLesson: the naive rule looked plausible, and forward shows a coin-flip — that IS the point.")
print("A backtest can be re-run until it flatters you; an append-only forward log cannot:")
print("decisions are timestamped before outcomes, so the scoreboard can't be rewritten.")
print("Everything in layers 1-5 only means 'not obviously broken' — this layer is the evidence.")

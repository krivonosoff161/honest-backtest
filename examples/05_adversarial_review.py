# -*- coding: utf-8 -*-
"""Layer 7 — an AI panel tries to REFUTE a plausible-but-fake finding."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from backtest_sanity import adversarial_review           # noqa: E402

claim = "Strategy X has a real edge: +0.4% per trade across 40 backtests."


# In production each verifier is an LLM call (wire to the sibling `llm-router`) with a
# different skeptical lens. Here: deterministic stand-ins that encode those lenses.
def lens_multiple_testing(c):   # 40 backtests -> a winner by luck is likely
    return "40 backtests" in c


def lens_costs(c):              # 0.4%/trade is near typical round-trip costs -> suspect
    return "0.4%" in c


def lens_reproduce(c):          # default to skeptical if no out-of-sample evidence is cited
    return "out-of-sample" not in c.lower()


res = adversarial_review(claim, [lens_multiple_testing, lens_costs, lens_reproduce])
print("claim:", res["claim"])
print("refuted by %d/%d verifiers -> rejected: %s" % (res["refuted"], res["n"], res["rejected"]))
print("\nLesson: one pass rationalizes; a skeptical panel refutes. Wire the verifiers to an LLM.")

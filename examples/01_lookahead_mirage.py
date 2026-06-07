# -*- coding: utf-8 -*-
"""Layer 1 — a feature that peeks at the future looks 'predictive'. Catch it."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from backtest_sanity import lookahead_correlation       # noqa: E402
from backtest_sanity._synth import toy_returns          # noqa: E402

future = toy_returns(500, edge=0.0, seed=1)                       # tomorrow's return (unknowable today)
honest_feature = toy_returns(500, edge=0.0, seed=2)              # an honest signal: no future info
peeking_feature = future + toy_returns(500, sigma=0.002, seed=3)  # leaks the future

print("honest  feature corr with the future it 'predicts': %.3f" % lookahead_correlation(honest_feature, future))
print("peeking feature corr with the future it 'predicts': %.3f" % lookahead_correlation(peeking_feature, future))
print("\nLesson: a |corr| near 1 with the very bar you claim to predict = look-ahead, not skill.")

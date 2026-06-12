# -*- coding: utf-8 -*-
"""Layer 3 ext -- a 'great' Sharpe deflates once you admit how many things you tried."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np                                                      # noqa: E402

from backtest_sanity import (                                           # noqa: E402
    deflated_sharpe_ratio, minimum_track_record_length, probabilistic_sharpe_ratio,
)
from backtest_sanity._synth import toy_returns                          # noqa: E402

# a candidate with a modest real (synthetic!) edge, and pure-noise for contrast
candidate = toy_returns(500, edge=0.002, sigma=0.01, seed=42)
noise = toy_returns(500, edge=0.0, sigma=0.01, seed=43)

psr_cand = probabilistic_sharpe_ratio(candidate)
psr_noise = probabilistic_sharpe_ratio(noise)
print("PSR -- P(true Sharpe > 0), adjusted for length/skew/kurtosis:")
print("  candidate (thin synthetic edge): PSR=%.3f  (per-period SR=%.3f, n=%d)"
      % (psr_cand["psr"], psr_cand["sharpe"], psr_cand["n"]))
print("  pure noise:                      PSR=%.3f  (per-period SR=%.3f)"
      % (psr_noise["psr"], psr_noise["sharpe"]))

# the same candidate was the BEST of a parameter search -- admit it
rng = np.random.default_rng(7)
search_small = list(rng.normal(0.0, 0.15, 5))     # 5 variants tried
search_large = list(rng.normal(0.0, 0.15, 100))   # 100 variants tried
dsr_small = deflated_sharpe_ratio(candidate, trial_sharpes=search_small)
dsr_large = deflated_sharpe_ratio(candidate, trial_sharpes=search_large)
print("\nDSR -- same track record, deflated by how many variants were tried:")
print("  after   5 trials: expected-max-SR(luck)=%.3f -> DSR=%.3f"
      % (dsr_small["expected_max_sharpe"], dsr_small["dsr"]))
print("  after 100 trials: expected-max-SR(luck)=%.3f -> DSR=%.3f"
      % (dsr_large["expected_max_sharpe"], dsr_large["dsr"]))

# how long must the track record be before this Sharpe means anything?
for conf in (0.90, 0.95, 0.99):
    r = minimum_track_record_length(candidate, confidence=conf)
    print("MinTRL @ %.0f%% confidence: %d periods needed (have %d) -> %s"
          % (conf * 100, round(r["min_n"]), r["n"],
             "enough" if r["sufficient"] else "keep collecting"))

print("\nLesson: a Sharpe is a sample estimate, not a fact. Admit every variant you"
      "\ntried and the bar rises; none of this certifies an edge -- it only refuses"
      "\nto be impressed too early.")

# -*- coding: utf-8 -*-
"""Layer 5 — a real edge is a plateau across parameters; a lone spike is tuning luck."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np                                                  # noqa: E402

from backtest_sanity import param_sweep, subperiod_stability        # noqa: E402
from backtest_sanity._synth import toy_returns                      # noqa: E402


def trend_filter_score(series):
    """'Strategy': take tomorrow's return when the rolling mean over `w` bars is positive."""
    def score(w: int) -> float:
        roll = np.convolve(series, np.ones(w) / w, mode="valid")[:-1]   # mean up to yesterday
        fwd = series[w:]
        picked = fwd[roll > 0]
        return float(picked.mean()) if picked.size else 0.0
    return score


grid = list(range(5, 60, 5))

noise = toy_returns(1500, edge=0.0, seed=11)        # pure noise: any 'best window' is luck
real = toy_returns(1500, edge=0.002, seed=11)       # constant real edge: every window sees it

sweep_noise = param_sweep(trend_filter_score(noise), grid)
sweep_real = param_sweep(trend_filter_score(real), grid)


def verdict(sweep) -> str:
    if sweep["median"] <= 0:
        return "best window has NO neighbourhood support -> tuning luck"
    if sweep["spike_ratio"] >= 1.5:
        return "spike %.1fx over the median -> likely overfit" % sweep["spike_ratio"]
    return "plateau (best/median %.1fx) -> structure" % sweep["spike_ratio"]


print("param sweep over rolling windows %s" % grid)
print("  pure noise : best=%+.5f median=%+.5f  <- %s"
      % (sweep_noise["best"], sweep_noise["median"], verdict(sweep_noise)))
print("  real edge  : best=%+.5f median=%+.5f  <- %s"
      % (sweep_real["best"], sweep_real["median"], verdict(sweep_real)))

stab_noise = subperiod_stability(noise, n_periods=4)
stab_real = subperiod_stability(real, n_periods=4)
print("\nsub-period stability (4 chunks, positive chunks of 4):")
print("  pure noise : %d/4 consistent=%s" % (stab_noise["positive_periods"], stab_noise["consistent"]))
print("  real edge  : %d/4 consistent=%s" % (stab_real["positive_periods"], stab_real["consistent"]))

print("\nLesson: don't trust the best parameter — trust the neighbourhood. "
      "A spike over the grid median is overfitting; a plateau plus sign-stable sub-periods is structure.")

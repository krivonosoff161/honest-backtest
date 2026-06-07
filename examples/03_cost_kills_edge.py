# -*- coding: utf-8 -*-
"""Layer 4 — a real but thin edge, eaten by trading costs."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from backtest_sanity import apply_costs, bootstrap_ci    # noqa: E402
from backtest_sanity._synth import toy_returns           # noqa: E402

rets = toy_returns(3000, edge=0.001, sigma=0.01, seed=5)   # a tiny *real* edge (+0.1%/period)
res = apply_costs(rets, fee=0.001, slippage=0.0005, turnover=1.0)

print("gross mean: %+.5f | net mean: %+.5f | cost drag: %.5f" % (
    res["gross_mean"], res["net_mean"], res["cost_drag"]))
print("survives costs:", res["survives_costs"])
_, lo, hi = bootstrap_ci(res["net"])
print("net mean 95%% CI: [%+.5f, %+.5f]" % (lo, hi))
print("\nLesson: gross is positive, net is not — the edge was smaller than the cost of trading it.")

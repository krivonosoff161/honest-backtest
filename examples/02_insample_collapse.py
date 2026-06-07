# -*- coding: utf-8 -*-
"""Layer 2 — pick the best parameter in-sample, watch it collapse out-of-sample."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np                                       # noqa: E402
from backtest_sanity import walk_forward                 # noqa: E402
from backtest_sanity._synth import toy_returns           # noqa: E402

rets = toy_returns(2400, edge=0.0, seed=7)   # pure noise: NO real edge exists


def strat_return(r, lookback):
    """Causal toy strategy: long if the previous `lookback` mean was positive."""
    r = np.asarray(r, dtype=float)
    pnl = [(1.0 if r[t - lookback:t].mean() > 0 else -1.0) * r[t] for t in range(lookback, len(r))]
    return float(np.mean(pnl)) if pnl else 0.0


params = [3, 5, 8, 13, 21, 34]
ins = rets[:1200]
best = max(params, key=lambda p: strat_return(ins, p))
print("best param in-sample: %d  | in-sample mean: %+.5f" % (best, strat_return(ins, best)))

oos = [strat_return(rets[te[0]:te[-1] + 1], best) for _, te in walk_forward(len(rets), 1200, 300)]
print("walk-forward OOS mean with that 'best' param: %+.5f" % np.mean(oos))
print("\nLesson: 'best in-sample' on noise is luck; out-of-sample it collapses to ~0.")

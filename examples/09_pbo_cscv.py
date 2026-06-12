# -*- coding: utf-8 -*-
"""Layer 3 ext -- PBO: how often is the in-sample winner an out-of-sample loser?"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np                                                      # noqa: E402

from backtest_sanity import probability_of_backtest_overfitting        # noqa: E402

# a parameter sweep: 24 variants x 480 periods, ALL pure noise (no real edge)
rng = np.random.default_rng(0)
sweep_noise = rng.normal(0.0, 0.01, (480, 24))

res_noise = probability_of_backtest_overfitting(sweep_noise, n_blocks=8)
print("sweep of 24 pure-noise variants (CSCV, %d train/test splits):"
      % res_noise["n_combinations"])
print("  PBO = %.2f  -- the in-sample 'winner' lands in the bottom half"
      % res_noise["pbo"])
print("  out-of-sample about half the time: selection found luck, not structure.")

# same sweep, but one variant carries a real (synthetic!) edge
sweep_edge = sweep_noise.copy()
sweep_edge[:, 5] += 0.004

res_edge = probability_of_backtest_overfitting(sweep_edge, n_blocks=8)
print("\nsame sweep + one genuinely stronger variant:")
print("  PBO = %.2f  -- the winner keeps winning out-of-sample, so the"
      % res_edge["pbo"])
print("  selection process is no longer convicted of overfitting.")

print("\nLesson: report PBO for the whole search, not the best curve. PBO ~0.5 on"
      "\nyour sweep means the leaderboard is a lottery; a low PBO is merely a"
      "\nfailure to convict -- forward evidence still decides.")

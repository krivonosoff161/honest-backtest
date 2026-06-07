# -*- coding: utf-8 -*-
"""Layer 3 — torture 40 random 'strategies'; some 'win' by luck. Correct for it."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from backtest_sanity import benjamini_hochberg, permutation_test   # noqa: E402
from backtest_sanity._synth import toy_returns                     # noqa: E402

# 40 independent 'strategies', NONE with a real edge (all pure noise)
strategies = [toy_returns(500, edge=0.0, seed=100 + i) for i in range(40)]
pvals = [permutation_test(s, n_perm=1000, seed=i)["p_value"] for i, s in enumerate(strategies)]

naive = sum(1 for p in pvals if p < 0.05)
survive = sum(1 for _, rej in benjamini_hochberg(pvals, alpha=0.05) if rej)

print("strategies tested: %d (all pure noise, zero real edge)" % len(strategies))
print("'significant' at p<0.05 naively: %d  (~%.0f expected by chance)" % (naive, len(strategies) * 0.05))
print("survive Benjamini-Hochberg FDR control: %d" % survive)
print("\nLesson: test enough things and some win by luck. Correct for it, or you trade noise.")

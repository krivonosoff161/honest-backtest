# Examples — read them in order

Seven scripts, one self-deception each, all on **synthetic** data (no keys, no
network, deterministic seeds). Each prints the failure it catches and a
one-line lesson. Together they walk the seven layers of
[the architecture](../docs/architecture.md).

```bash
python examples/01_lookahead_mirage.py
python examples/02_insample_collapse.py
python examples/03_cost_kills_edge.py
python examples/04_multiple_testing.py
python examples/05_adversarial_review.py
python examples/06_robustness_plateau.py
python examples/07_forward_log.py
```

| # | Layer | Demonstrates | What you should see |
|---|---|---|---|
| 01 | 1 data integrity | a "predictor" that peeks at the bar it predicts | honest feature corr ≈ 0, peeking feature corr ≈ 1 |
| 02 | 2 splits | best in-sample parameter collapsing out-of-sample | in-sample mean shrinks toward 0 on walk-forward OOS |
| 03 | 4 costs | a real but thin edge eaten by fees + slippage | gross mean > 0, net mean < 0 |
| 04 | 3 significance | 40 pure-noise strategies, some "win" by luck | 1–2 naively significant (≈ chance) → 0 survive BH correction |
| 05 | 7 adversarial | a panel of skeptics refuting a flattering claim | majority refute → finding rejected |
| 06 | 5 robustness | lone best-parameter spike vs a plateau | noise: best window without neighbourhood support; real edge: plateau + 4/4 stable sub-periods |
| 07 | 6 forward | append-only decision→outcome log | a plausible naive rule scoring a coin-flip forward — that *is* the lesson |

**What the examples do NOT prove**

- They prove the *checks work on synthetic failures* — not that your strategy
  is good, and not that these checks catch every failure on real data.
- The significance examples assume i.i.d. returns; real returns are not
  (see the note in the README).
- No example implies profitability anywhere: the kit kills bad strategies
  cheaply, it does not bless good ones.

# Examples — read them in order

Nine scripts, one self-deception each, all on **synthetic** data (no keys, no
network, deterministic seeds). Each prints the failure it catches and a
one-line lesson. Together they walk the seven layers of
[the architecture](../docs/architecture.md) (08–09 extend layer 3 with the
named overfitting statistics).

```bash
python examples/01_lookahead_mirage.py
python examples/02_insample_collapse.py
python examples/03_cost_kills_edge.py
python examples/04_multiple_testing.py
python examples/05_adversarial_review.py
python examples/06_robustness_plateau.py
python examples/07_forward_log.py
python examples/08_deflated_sharpe.py
python examples/09_pbo_cscv.py
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
| 08 | 3+ overfitting stats | PSR/DSR/MinTRL: a Sharpe deflating under multiplicity | DSR collapses from ~1.0 to ~0 as admitted trials go 5 → 100 |
| 09 | 3+ overfitting stats | PBO via CSCV on a parameter sweep | pure-noise sweep: PBO ≈ 0.5; one real (synthetic) edge: PBO → 0 |

**What the examples do NOT prove**

- They prove the *checks work on synthetic failures* — not that your strategy
  is good, and not that these checks catch every failure on real data.
- The significance examples (including PSR/DSR/MinTRL/PBO) assume i.i.d.
  returns; real returns are not (see the note in the README).
- No example implies profitability anywhere: the kit kills bad strategies
  cheaply, it does not bless good ones.

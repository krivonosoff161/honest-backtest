# honest-backtest

[![Tests](https://github.com/krivonosoff161/honest-backtest/actions/workflows/tests.yml/badge.svg)](https://github.com/krivonosoff161/honest-backtest/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)

**A layered validation architecture for trading backtests — and the AI step that tries to kill your finding instead of blessing it.**

Most backtests lie. A strategy looks brilliant in-sample, then dies out-of-sample; a thin edge gets eaten by costs; look-ahead bias sneaks in; run enough variations and one "wins" by luck. This repo is the **architecture for catching those lies before they cost money** — seven layers of checks, each with a worked example on **synthetic** data showing the exact failure it catches.

> Distilled from real research discipline, rebuilt clean on synthetic data. No strategy, no real numbers — the value is the *method*, not an edge.

---

## ⚠️ This is not a panacea — read first

This kit **reduces** self-deception. It does **not** eliminate it.

- It's **one** validation approach among many — not proof of a real edge.
- **The choice and combination of components is itself a degree of freedom.** Which checks, which splits, which parameters, which thresholds, what counts as "passing" — pick enough variants and one will pass by luck. *The validation pipeline is itself a multiple-comparisons problem.* Researcher bias doesn't vanish; it moves up a level.
- Passing every check means **"not obviously broken"**, not **"true"**. The only real test is **forward / out-of-time / live**.

**Use it to kill bad strategies cheaply — not to bless good ones.**

---

## The architecture (7 layers)

| # | Layer | Catches | Module | Example |
|---|---|---|---|---|
| 1 | **Data integrity** | look-ahead, survivorship, out-of-order bars | `data_checks` | [01](examples/01_lookahead_mirage.py) |
| 2 | **Validation splits** | judging on data you fitted to | `splits` — holdout · walk-forward · purged k-fold | [02](examples/02_insample_collapse.py) |
| 3 | **Significance** | luck dressed as edge | `significance` — bootstrap CI · permutation · Bonferroni/BH | [04](examples/04_multiple_testing.py) |
| 4 | **Costs** | an edge thinner than fees + slippage | `costs` — gross vs net | [03](examples/03_cost_kills_edge.py) |
| 5 | **Robustness** | a lucky spike vs a real plateau | `robustness` — param sweep · sub-period stability | [06](examples/06_robustness_plateau.py) |
| 6 | **Forward** | everything above is just "not broken yet" | `forward.ForwardLog` | [07](examples/07_forward_log.py) |
| 7 | **AI adversarial review** | a single pass rationalizes | `adversarial_review` | [05](examples/05_adversarial_review.py) |

Each layer is a small, independent function — use one, or stack them.

---

## Install

```bash
git clone https://github.com/krivonosoff161/honest-backtest
cd honest-backtest
pip install -e .          # numpy is the only dependency
```

Python **3.9+**. Verified on Windows; pure Python + numpy, runs on Linux/macOS.

## Run the examples (synthetic, no keys)

```bash
python examples/01_lookahead_mirage.py    # a peeking feature looks "predictive"
python examples/02_insample_collapse.py   # best-in-sample collapses out-of-sample
python examples/03_cost_kills_edge.py      # a real edge, eaten by costs
python examples/04_multiple_testing.py     # 40 noise strategies, ~2 "win" by luck
python examples/05_adversarial_review.py   # an AI panel refutes a fake finding
python examples/06_robustness_plateau.py    # lucky spike vs parameter plateau
python examples/07_forward_log.py           # append-only forward log = the only evidence
python -m pytest -q                        # the toolkit's own tests
```

> Statistical note: the significance layer (bootstrap, sign-flip permutation) treats
> observations as **i.i.d.** Real returns are autocorrelated, so those p-values/CIs are
> optimistic on real data — good enough to kill bad ideas cheaply, not to certify good ones.

Reading order and what each example does (and does **not**) prove: [examples/README.md](examples/README.md).

---

## Docs

- [Architecture](docs/architecture.md) — the seven layers and the meta-caveat.
- [Project map](docs/project-map.md) — modules, what exists vs not included, reviewer checklist.
- [Use cases](docs/use-cases.md) — workflows, what this is *not*, residual risk.

---

## The AI layer (layer 7)

A single model pass tends to *rationalize* a finding. An adversarial **panel** refutes it:
run N independent verifiers, each prompted to **kill** the claim (and to default to "refuted"
when unsure); if a majority refute, drop it. Diversity beats redundancy — give each verifier a
different lens (correctness · does-it-reproduce · already-priced · cost-realism).

`adversarial_review(claim, verifiers)` is LLM-agnostic — inject `verify(claim) -> bool`
callables. Wire them to the sibling **[llm-router](https://github.com/krivonosoff161/llm-router)**
for real LLM calls, or pass deterministic fakes for offline tests (see [example 05](examples/05_adversarial_review.py)).

---

## What's intentionally *not* here

- No real strategy, parameters, or performance numbers — only the methods (all textbook) on synthetic data.
- Not a backtesting *engine* (use backtrader / vectorbt for that) — this is the **validation layer** you wrap around one.
- Not a promise. See the panacea note above.

## License

MIT — see [LICENSE](LICENSE). **Not financial advice**; for research and education.

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

## Role in the trading stack

`honest-backtest` is the skeptical validation layer for AI-assisted trading
research:

```text
AI / Strategy Lab proposes an idea
honest-backtest tries to falsify it
forward/paper evidence decides whether it deserves more attention
live execution stays outside this repository
```

That distinction matters. The AI step can help search, summarize, and challenge
ideas, but its output is not a signal until it survives deterministic validation,
cost checks, robustness checks, adversarial review, and forward logging.

This repo does not contain private strategy logic, broker integration, exchange
keys, or a promise of profitability. It is the validator you put between
"interesting idea" and "maybe worth paper tracking."

Portfolio-level documentation authority and public/private storage rules live in
the [Documentation Contract](https://github.com/krivonosoff161/krivonosoff161/blob/main/docs/documentation-contract.md).
This repository owns validation methods and synthetic examples; it must not
publish private trading edge, live parameters, or candidate rankings.

---

## The architecture (7 layers)

| # | Layer | Catches | Module | Example |
|---|---|---|---|---|
| 1 | **Data integrity** | look-ahead, survivorship, out-of-order bars | `data_checks` | [01](examples/01_lookahead_mirage.py) |
| 2 | **Validation splits** | judging on data you fitted to | `splits` — holdout · walk-forward · purged k-fold | [02](examples/02_insample_collapse.py) |
| 3 | **Significance** | luck dressed as edge | `significance` — bootstrap CI · permutation · Bonferroni/BH | [04](examples/04_multiple_testing.py) |
| 3+ | **Named overfitting stats** | a "great" Sharpe born from trying many things | `overfit` — PSR · DSR · MinTRL · PBO (CSCV) | [08](examples/08_deflated_sharpe.py) · [09](examples/09_pbo_cscv.py) |
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
python examples/08_deflated_sharpe.py       # PSR / DSR / MinTRL — a Sharpe deflates under multiplicity
python examples/09_pbo_cscv.py              # PBO via CSCV — is the in-sample winner an OOS loser?
python -m pytest -q                        # the toolkit's own tests
```

> Statistical note: the significance layer (bootstrap, sign-flip permutation, and the
> PSR/DSR/MinTRL/PBO family) treats observations as **i.i.d.** Real returns are
> autocorrelated, so those p-values/CIs/probabilities are optimistic on real data —
> good enough to kill bad ideas cheaply, not to certify good ones. The named
> overfitting statistics **reduce false confidence; they do not prove profitability**
> (assumptions and reading guide: [docs/overfitting-statistics.md](docs/overfitting-statistics.md)).

Reading order and what each example does (and does **not**) prove: [examples/README.md](examples/README.md).

---

## Docs

- [Architecture](docs/architecture.md) — the seven layers and the meta-caveat.
- [Project map](docs/project-map.md) — modules, what exists vs not included, reviewer checklist.
- [Use cases](docs/use-cases.md) — workflows, what this is *not*, residual risk.
- [Named overfitting statistics](docs/overfitting-statistics.md) — PSR · DSR · MinTRL · PBO (CSCV): assumptions, how to read them, how they gate Strategy Lab candidates.
- [Strategy Discovery Lab](docs/strategy-discovery-lab.md) — planned experimental hypothesis sandbox before validation.
- [Strategy Lab storage](docs/strategy-lab-storage.md) — local data-root layout and manifest rules.
- [Strategy Lab data model](docs/strategy-lab-data-model.md) — experiment, result, candidate and registry records.
- [Strategy Lab runtime](docs/strategy-lab-runtime.md) — queues, budgets, reports, Grafana and Obsidian boundaries.
- [Strategy Lab LLM loop](docs/strategy-lab-llm-loop.md) — provider-neutral research coordinator design.
- [Strategy Lab roadmap](docs/strategy-lab-roadmap.md) — phased build plan.

---

## Experimental: Strategy Discovery Lab

A planned sandbox for logging and triaging strategy hypotheses before they
enter the seven-layer validation gauntlet. It is not part of the stable API,
does not include real market data, and does not claim to find profitable
strategies.

```text
strategy_lab generates candidates
backtest_sanity tries to reject them
forward evidence decides whether they deserve more attention
```

See [docs/strategy-discovery-lab.md](docs/strategy-discovery-lab.md).

The first implemented slice is a read-only inventory command. It writes
manifests and summaries to a private output directory:

```bash
python -m strategy_lab.cli inventory \
  --source-root <read-only-research-source> \
  --tick-root <optional-read-only-tick-root> \
  --out-dir <private-research-output>
```

The command inventories available files and schemas. It does not run
strategies, simulations, LLM calls, or validation.

The next experimental slice is a file-based registry and experiment queue:

```bash
python -m strategy_lab.cli registry-init \
  --out-dir <private-research-output>

python -m strategy_lab.cli queue-plan \
  --plan <experiment-plan.json> \
  --out-dir <private-research-output>

python -m strategy_lab.cli registry-add \
  --entry <registry-entry.json> \
  --out-dir <private-research-output>
```

Queued plans require explicit budgets and cannot enable LLM calls inside the
deterministic runner. Registry entries are research records only; statuses such
as `approved`, `profitable`, `ready`, or `live` are rejected.

Alibaba Model Studio / DashScope live calls are opt-in. Check local setup
without a network call:

```bash
python -m strategy_lab.cli llm-doctor
```

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

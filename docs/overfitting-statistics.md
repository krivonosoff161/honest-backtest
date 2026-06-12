# Named overfitting statistics -- PSR / DSR / MinTRL / PBO

The `backtest_sanity.overfit` module implements the four statistics
systematic-trading reviewers ask for by name. They extend layer 3
(significance) of [the architecture](architecture.md). The methods follow the
published definitions by Bailey, Lopez de Prado et al.; the implementation
here is numpy-only and independent.

**These are statistical skepticism tools.** Each one answers a narrow
question of the form *"could this number be luck?"* -- none of them answers
*"will this make money?"*. They reduce false confidence; they do not prove
profitability, and passing all of them still only means **"not obviously
broken"**.

## The four statistics

### Probabilistic Sharpe Ratio (PSR)

`probabilistic_sharpe_ratio(returns, benchmark_sr=0.0)`

The probability that the *true* Sharpe ratio exceeds a benchmark, given the
observed track record. It penalizes short samples, negative skew and fat
tails: two strategies with the same point-estimate Sharpe get very different
PSRs if one is short and fat-tailed.

- Sharpe is **per-period** (not annualized); the benchmark must match.
- PSR ~ 1.0 means "hard to explain by estimation noise" -- it says nothing
  about costs, regime change, or how many things you tried.

### Minimum Track Record Length (MinTRL)

`minimum_track_record_length(returns, benchmark_sr=0.0, confidence=0.95)`

How many observations the track record must contain before the observed
Sharpe clears the benchmark at the chosen confidence -- assuming the observed
Sharpe/skew/kurtosis persist, which is generous. If the observed Sharpe does
not exceed the benchmark, `min_n` is infinite: no amount of history rescues
it. An insufficient track record means "keep collecting forward evidence",
never "trust it anyway".

### Deflated Sharpe Ratio (DSR)

`deflated_sharpe_ratio(returns, trial_sharpes)`

A backtest is rarely one experiment -- it is the best of many. DSR re-runs PSR
against the Sharpe that *pure luck* would hand the best of N trials, with the
luck-spread estimated from the trials themselves. More trials, or a wider
spread of trial outcomes, raise the bar.

- `trial_sharpes` must contain **every variant tried, including abandoned
  ones**. Feeding it only survivors understates the deflation and defeats the
  point. This is the honesty bottleneck: the statistic is only as good as
  your record of what you tried.

### Probability of Backtest Overfitting (PBO, via CSCV)

`probability_of_backtest_overfitting(trial_returns, n_blocks=8, metric=None, max_combinations=200)`

Takes the **whole search** -- a `(time x trials)` matrix of per-period returns
for every variant -- and asks: when we pick the in-sample winner, how often is
it a below-median performer out-of-sample? Time is cut into even blocks and
every half/half block combination is used as a train/test split
(combinatorially symmetric cross-validation).

- Pure noise gives PBO ~ 0.5 (the winner is random out-of-sample).
- A genuinely dominant variant pulls PBO toward 0.
- PBO well above 0.5 means selection actively favors what fails forward.
- Combinatorics are bounded by `max_combinations` (deterministic evenly
  spaced subset; the count used is reported).

## Shared assumptions and limitations

- **i.i.d.-style assumptions.** The PSR/DSR sampling distribution assumes
  stationary, weakly dependent returns; CSCV ignores dependence across
  blocks. Real returns are autocorrelated and volatility-clustered, so all
  of these numbers are **optimistic on real data**.
- **Per-period scale.** No annualization anywhere; compare like with like.
- **Population moments** (`ddof=0`), as in the original papers.
- **Degenerate inputs fail loudly.** Series shorter than 3 observations,
  zero-variance series, NaN/inf, single-trial DSR, odd block counts and
  too-short PBO matrices raise `ValueError` instead of returning a number
  that looks meaningful.
- **The meta-caveat still applies.** Choosing which of these statistics to
  run, with which thresholds, is itself a degree of freedom. They make
  self-deception more expensive, not impossible.

## How they gate a private Strategy Discovery Lab

The [Strategy Discovery Lab](strategy-discovery-lab.md) generates candidate
hypotheses by the batch -- which is exactly the situation these statistics
exist for: many trials, one flattering leaderboard.

The division of labor:

1. **Strategy Lab generates candidates** (parameter sweeps, hypothesis
   families) and -- critically -- records *every* variant tried.
2. **honest-backtest pressures them statistically**: PBO on the full sweep
   matrix convicts or fails to convict the *search process*; DSR deflates the
   surviving candidate's Sharpe by the size of that search; PSR/MinTRL say
   whether the track record is even long enough to mean anything.
3. **Only candidates that pass these basic gates become forward-paper
   candidates** (`needs_forward` in the lab's lifecycle). Passing the gates
   grants more *attention*, never live permission.
4. **The public repo carries the method only.** Private strategy results,
   parameters, and real-data numbers stay in the private lab; everything
   here runs on synthetic data.

A practical reading of the gates: PBO ~ 0.5 on a sweep means the lab's
leaderboard for that family is a lottery -- discard the family, not just the
worst variants. A candidate whose DSR is low after admitting the full search
was probably the luckiest of many. None of these outcomes is bad news; each
one is a cheap kill that saved a forward-test slot.

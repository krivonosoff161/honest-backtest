# Use cases

## Who this is for

- Individual quant researchers and hobbyists who keep "discovering" strategies
  that die out-of-sample.
- Students/teachers who need **runnable demonstrations** of look-ahead bias,
  multiple testing, and cost drag on synthetic data.
- Maintainers of open-source strategy repos who want a cheap validation
  gauntlet before merging performance claims.
- Anyone reviewing AI-generated trading research, where confident-but-wrong
  backtests are the default failure mode.

## The problem it solves

Most backtests flatter their author. The failure modes are textbook —
look-ahead, in-sample tuning, luck across many trials, ignored costs,
parameter cherry-picks — but checking them is tedious, so it gets skipped.
This kit makes each check a one-function call with a worked example, cheap
enough that there's no excuse to skip it.

**The framing matters: it kills bad strategies cheaply. It does not certify
good ones.**

## Practical workflows

**1. The pre-excitement gauntlet.**
Before getting attached to a result: `timestamp_monotonic` +
`lookahead_correlation` (layer 1) → re-test on `walk_forward` splits (2) →
`permutation_test` + BH correction if you tried variants (3) → `apply_costs`
(4). Most "discoveries" die in under an hour of compute, which is the cheapest
possible outcome.

**2. Parameter honesty check.**
You found "the best lookback = 23"? `param_sweep` over the neighbourhood: a
lone spike over the grid median is tuning luck; a plateau plus
`subperiod_stability` is structure (example 06 shows both on synthetic data).

**3. Forward discipline.**
Once a strategy survives layers 1–5, stop re-backtesting: log every decision
with `ForwardLog` *before* outcomes exist, append outcomes later, and score the
join (example 07). Append-only JSONL means the scoreboard can't be quietly
rewritten.

**4. Adversarial review of a writeup.**
Feed the claim to `adversarial_review` with several skeptical verifiers (LLM
or human-written rules), each with a different lens: correctness,
reproducibility, already-priced, cost-realism. Majority refute → back to work.

**5. Teaching.**
Each example (01–07) demonstrates exactly one failure mode in ~25 lines on
synthetic data — usable directly in a course or an onboarding doc.

**6. Strategy discovery governance (planned).**
A future Strategy Discovery Lab can run many strategy and filter hypotheses,
but the validation toolkit remains the skeptical gate. The useful output is a
private registry entry such as "needs forward evidence on this synthetic cluster",
not a profitability claim.

## What this is not

- **Not a profitability tool.** Passing all seven layers means "not obviously
  broken", never "this makes money".
- **Not a backtesting engine** — wrap it around backtrader/vectorbt/your own.
- **Not a live strategy search daemon.** The Strategy Discovery Lab docs
  describe a planned offline research architecture, not shipped execution code.
- **Not robust statistics under all regimes.** The significance layer assumes
  i.i.d. observations; real returns are autocorrelated and regime-switching,
  which makes these p-values optimistic. Use them as a cheap first kill-test,
  not as proof.
- **Not a substitute for live/forward testing** — layer 6 exists precisely
  because layers 1–5 aren't.

## Limitations and residual risk

- **The pipeline itself is a researcher degree of freedom**: choose enough
  check-combinations and thresholds and something passes by luck. Fix the
  gauntlet *before* running it.
- i.i.d. bootstrap/permutation understate uncertainty on dependent data; block
  bootstrap is not implemented.
- `param_sweep`'s spike ratio is a heuristic, not a test statistic — there is
  no significance level on "plateau vs spike".
- `ForwardLog` is an honest log, not an execution simulator: it doesn't model
  fills, latency, or capacity.
- All examples are synthetic by design; nothing here validates your *data
  pipeline* (corporate actions, point-in-time universes) beyond the layer-1
  smells.

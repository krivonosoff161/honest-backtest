# Trading Portfolio Roadmap: Validator Projection

Status: **CURRENT**

- Verified: 2026-08-30
- Verified against: `a392333caf0d74d39fbb502b3aef98a0e51b5b9d`
- Scope: honest-backtest's bounded projection of the shared Trading Portfolio map
- Evidence: [machine projection](trading-portfolio-roadmap.yaml) and
  [validation bridge](validation-bridge-contract.md)
- Residual risks: the projection becomes stale when either repository changes
  its contract or verified base.
- Next gate: update and validate both projections in a coordinated review.

The canonical portfolio map is owned by `trading-bot-v2`. This repository keeps
only a pinned validator-module projection needed to check the boundary. It does
not copy producer code, private candidates, runtime state, or operational
authority. The `krivonosoff161` profile may integrate a sanitized manifest only
after the canonical owner has merged and published it.

| Field | Verified value |
|---|---|
| Module | `honest_backtest_validation` |
| Owner | `honest-backtest` |
| Status | implemented bounded |
| Authority | none |
| Input | public-safe, versioned candidate artifact with full trial provenance |
| Output | bounded skeptical verdict; strongest positive ceiling is paper/forward observation |
| Excluded | strategies, rankings, private data, execution, profitability claims |

## Relationship

```text
trading-bot-v2 owns research and paper lifecycle
  -> sends a public-safe validation artifact
honest-backtest owns skeptical validation
  -> returns a bounded verdict
trading-bot-v2 owns any later paper observation

no edge, runtime row, credential, account, recipient, or authority crosses
```

The machine projection records the exact upstream schema version, commit, and
content hash reviewed for this alignment. The digest is calculated over
canonical UTF-8 text with LF line endings, so a Windows CRLF checkout has the
same identity while any semantic content change remains detectable. A hash
match proves document identity, not operational readiness or statistical quality.
It also records a content-addressed implementation snapshot: this keeps the
review binding valid after a GitHub squash merge changes the commit object, but
still rejects any source-tree drift from the reviewed implementation.

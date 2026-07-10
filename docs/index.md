# Documentation Index

Status: **ACTIVE**. `honest-backtest` is a validation toolkit, not a trading
engine or a profitability claim.

## Read Order

1. [Repository README](../README.md): scope, examples, and limitations.
2. [Project Map](project-map.md): module ownership and what is shipped.
3. [Architecture](architecture.md): seven validation layers.
4. [Public API](api-reference.md): supported `backtest_sanity` surface.
5. [Strategy Lab Experimental API](strategy-lab-experimental.md): local/private
   inventory, registry, queue, and guarded LLM tooling.
6. [Validation Bridge Contract](validation-bridge-contract.md): public-safe
   candidate, verdict, and forward-evidence boundary.

## Stable And Experimental Surfaces

| Surface | Status | Contract |
|---|---|---|
| `backtest_sanity` exports | stable public API | Small pure validation functions and `ForwardLog`; see `api-reference.md`. |
| `examples/01..09` | stable teaching examples | Synthetic, deterministic demonstrations. |
| `strategy_lab` package and CLI | experimental | File-based private research sandbox; schemas may change. |
| Live Alibaba provider | explicit opt-in experimental | Requires explicit cost acceptance and environment gates. |

## Related Documents

- [Assumptions and overfitting statistics](overfitting-statistics.md)
- [Use cases and residual risk](use-cases.md)
- [Strategy Lab storage](strategy-lab-storage.md)
- [Strategy Lab data model](strategy-lab-data-model.md)
- [Strategy Lab runtime](strategy-lab-runtime.md)
- [Strategy Lab LLM loop](strategy-lab-llm-loop.md)
- [Strategy Lab roadmap](strategy-lab-roadmap.md)

## Integration Boundary

The sibling `trading-bot-v2` project may submit a public-safe candidate summary
to its local validation bridge. This repository never receives exchange keys,
private trade rows, candidate rankings, or execution authority. A generic
`backtest_sanity` pass means only `needs_forward`, never live permission. A
producer bridge may map a complete hard-validation result to
`PAPER_FORWARD_READY` under the public contract; that still permits only
paper/forward observation and never execution.

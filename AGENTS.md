# Honest Backtest Agent Contract

Read and follow these canonical global contracts first:

- `E:\AI\workbench\contracts\GLOBAL_AGENT_CONTRACT.md`
- `E:\AI\workbench\contracts\GIT_OPERATING_CONTRACT.md`

Resolve the exact checkout through `E:\AI\workbench\registry\projects.yaml`.

## Project

- Registry id: `honest-backtest` for stable `main`; use the explicit registered task-worktree id when one exists.
- Purpose: separate skeptical validation layer for the trading research stack. It tries to falsify weak backtests and records synthetic, deterministic evidence.
- Classification: public research/validation product. Private strategy data and live execution stay outside this repository.

## Start Sequence

1. Run `wb git-preflight` for the registry id that resolves to this exact checkout.
2. Read local `SESSION.md`, then `TASK.md` only when its status is active.
3. Read `README.md`, `docs/index.md`, `docs/architecture.md`, `docs/project-map.md`, and `docs/strategy-lab-roadmap.md`.
4. Search existing modules, tests, examples, and documented commands before proposing a new surface.
5. State verified facts, causal chain, scope, and the minimal plan before changes.

## Project Boundaries

- Keep this repository separate from `trading-bot-v2`; integration is through explicit artifacts and documented contracts, not by moving repositories or copying private strategy code.
- Default work is deterministic and synthetic. Do not read or publish private strategy logic, candidate rankings, real parameters, market/account data, or local Strategy Lab outputs.
- Passing validation means only "not rejected by these checks". Never convert it into a profitability, safety, or deployment claim.
- No `.env`, credentials, external model calls, broker/private exchange endpoints, order placement, live trading, or control of trading/project processes without a new action-specific user instruction.
- Treat LLM review as a proposal. Deterministic tests and evidence own statistical values, gates, promotion, and verdicts.
- Global secret, money, process, destructive-action, evidence, and Git boundaries remain mandatory.

## Change And Verification

- Work only on an approved task branch/worktree; stable `main` is not an agent editing branch.
- Preserve unrelated and unknown work and stage only explicit paths.
- Run repository checks proportional to the change; statistical or numerical behavior requires focused tests plus the full suite.
- Keep local Strategy Lab data, reports, caches, model output, and runtime files out of public Git.
- Follow the global checkpoint/commit/push/PR/merge authority model and report only checks actually completed.

## Continuity

- `SESSION.md` is a compact local current-state snapshot, not a transcript and not a tracked product file.
- `TASK.md` contains one bounded local task and never grants authority by itself.
- Historical handoffs and experiment artifacts are evidence only, not current instructions or execution authority.

## Completion

- Update `SESSION.md`, close or deactivate `TASK.md`, and record exact checks, dirty state, next safe step, residual risk, and any authority still required.

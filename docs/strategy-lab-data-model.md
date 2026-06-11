# Strategy Lab Data Model

## Design principle

The lab should store research evidence, not just final scores. A future
reviewer must be able to answer:

- what was tested;
- on which data;
- with which parameters;
- under which market regime;
- what failed;
- what survived;
- what should be tested forward.

## Core records

### `StrategySpec`

```json
{
  "strategy_id": "volume_breakout",
  "family": "volume",
  "version": "0.1",
  "description": "Breakout after relative volume expansion.",
  "supported_timeframes": ["1m", "5m", "15m"],
  "parameter_schema": {
    "volume_multiplier": "float",
    "lookback_bars": "int",
    "stop_atr": "float",
    "take_profit_atr": "float"
  }
}
```

### `ExperimentPlan`

```json
{
  "experiment_id": "exp_...",
  "created_at": "UTC timestamp",
  "created_by": "human|rule|llm",
  "hypothesis": "A synthetic volume expansion pattern may lead continuation in a high-volatility asset cluster.",
  "assets": ["SYNTH-A", "SYNTH-B"],
  "asset_cluster": "synthetic_high_vol",
  "timeframes": ["1m", "5m"],
  "strategy_ids": ["volume_breakout"],
  "parameter_grid": {},
  "filters": {},
  "cost_model": "example_cost_model_v1",
  "data_window": {
    "train": ["YYYY-MM-DD", "YYYY-MM-DD"],
    "validation": ["YYYY-MM-DD", "YYYY-MM-DD"],
    "forward": ["YYYY-MM-DD", "YYYY-MM-DD"]
  },
  "budgets": {
    "max_variants": 1000,
    "max_runtime_seconds": 900,
    "stop_if_bad_after": 100
  }
}
```

### `TradeSimulation`

```json
{
  "experiment_id": "exp_...",
  "variant_id": "var_...",
  "trade_id": "trade_...",
  "symbol": "SYNTH-A",
  "timeframe": "5m",
  "side": "long",
  "entry_ts": "UTC timestamp",
  "entry_price": 0.0,
  "stop_price": 0.0,
  "target_price": 0.0,
  "exit_ts": "UTC timestamp",
  "exit_price": 0.0,
  "exit_reason": "stop|target|time|signal_flip|end_of_data",
  "gross_return_pct": 0.0,
  "net_return_pct": 0.0,
  "mfe_pct": 0.0,
  "mae_pct": 0.0,
  "fees_pct": 0.0,
  "slippage_pct": 0.0
}
```

### `VariantMetrics`

```json
{
  "variant_id": "var_...",
  "experiment_id": "exp_...",
  "strategy_id": "volume_breakout",
  "parameter_hash": "sha256...",
  "asset_cluster": "synthetic_high_vol",
  "timeframe": "5m",
  "trade_count": 0,
  "spam_rate": 0.0,
  "win_rate": 0.0,
  "profit_factor_net": 0.0,
  "max_drawdown_pct": 0.0,
  "median_mfe_pct": 0.0,
  "median_mae_pct": 0.0,
  "mfe_mae_ratio": 0.0,
  "time_to_mfe_median_min": 0.0,
  "cost_survived": false,
  "split_survived": false,
  "robustness": "unknown|spike|plateau|weak",
  "candidate_status": "rejected|weak|needs_forward|research_note"
}
```

### `RegistryEntry`

```json
{
  "registry_id": "reg_...",
  "created_at": "UTC timestamp",
  "strategy_id": "volume_breakout",
  "status": "needs_forward",
  "asset_cluster": "synthetic_high_vol",
  "market_regime": "synthetic_momentum",
  "timeframe": "5m",
  "filters": {
    "benchmark_regime": "not_down",
    "spread_max_pct": 0.15
  },
  "works_when": ["relative volume is high", "price expands range"],
  "fails_when": ["benchmark sells off fast", "liquidity is thin"],
  "evidence_refs": ["exp_..."],
  "review_notes": "Needs forward evidence before use as a confirmation factor."
}
```

## Metrics before PnL

The lab should not rank only by PnL. Early filters should prefer structural
signals:

- MFE vs MAE;
- signal spam rate;
- trade count adequacy;
- time to favorable excursion;
- cost survival;
- drawdown;
- split stability;
- parameter plateau;
- regime specificity;
- asset-cluster specificity.

PnL can be a metric, but it must not be the only gate.

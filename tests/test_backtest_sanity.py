# -*- coding: utf-8 -*-
"""Offline deterministic tests for the validation toolkit (seeded, no network)."""
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from backtest_sanity import (  # noqa: E402
    ForwardLog, adversarial_review, apply_costs, benjamini_hochberg, bonferroni,
    bootstrap_ci, holdout, lookahead_correlation, param_sweep, permutation_test,
    purged_kfold, subperiod_stability, timestamp_monotonic, walk_forward,
)
from backtest_sanity._synth import toy_returns  # noqa: E402


# layer 3 — significance
def test_bootstrap_ci_zero_edge_spans_zero():
    _, lo, hi = bootstrap_ci(toy_returns(1000, edge=0.0, seed=1), seed=0)
    assert lo < 0 < hi


def test_permutation_zero_edge_high_p():
    assert permutation_test(toy_returns(800, edge=0.0, seed=2), n_perm=500, seed=0)["p_value"] > 0.05


def test_permutation_strong_edge_low_p():
    assert permutation_test(toy_returns(800, edge=0.01, sigma=0.005, seed=3), n_perm=500, seed=0)["p_value"] < 0.05


def test_bonferroni():
    assert bonferroni([0.02, 0.3, 0.3, 0.3, 0.3], 0.05)[0][1] is False    # 0.02*5 = 0.10 > 0.05
    assert bonferroni([0.005, 0.3, 0.3, 0.3, 0.3], 0.05)[0][1] is True    # 0.005*5 = 0.025 <= 0.05


def test_benjamini_hochberg_shape():
    bh = benjamini_hochberg([0.01, 0.2, 0.3, 0.4, 0.5], 0.05)
    assert len(bh) == 5 and bh[0][1] in (True, False)


# layer 2 — splits
def test_holdout():
    tr, te = holdout(100, 0.3)
    assert len(tr) == 70 and len(te) == 30 and max(tr) < min(te)


def test_walk_forward_advances():
    wf = walk_forward(1000, 600, 100)
    assert wf and all(max(tr) < min(te) for tr, te in wf)


def test_purged_kfold_no_overlap_and_gap():
    for tr, te in purged_kfold(100, k=5, purge=5):
        tr_s, te_s = set(tr), set(te)
        assert not (tr_s & te_s)
        assert (min(te) - 1) not in tr_s and (max(te) + 1) not in tr_s


# layer 4 — costs
def test_costs_kill_thin_edge():
    res = apply_costs(toy_returns(3000, edge=0.001, sigma=0.01, seed=4), fee=0.001, slippage=0.0005)
    assert res["gross_mean"] > 0 and res["net_mean"] < 0 and res["survives_costs"] is False


# layer 5 — robustness
def test_param_sweep_flags_spike():
    assert param_sweep(lambda p: 1.0 if p == 7 else 0.1, [1, 3, 7, 9])["spike_ratio"] > 1.5


def test_subperiod_stability_shape():
    s = subperiod_stability(toy_returns(400, edge=0.0, seed=6), 4)
    assert s["n_periods"] == 4 and len(s["period_means"]) == 4


# layer 6 — forward
def test_forward_log_roundtrip(tmp_path):
    log = ForwardLog(str(tmp_path / "f.jsonl"))
    log.record({"asset": "X", "side": "long"})
    rows = log.rows()
    assert len(rows) == 1 and rows[0]["asset"] == "X" and "logged_at" in rows[0]


# layer 7 — adversarial
def test_adversarial_majority_refute():
    res = adversarial_review("claim", [lambda c: True, lambda c: True, lambda c: False])
    assert res["refuted"] == 2 and res["rejected"] is True


def test_adversarial_minority_survives():
    res = adversarial_review("claim", [lambda c: True, lambda c: False, lambda c: False])
    assert res["rejected"] is False


# layer 1 — data integrity
def test_lookahead_corr_high_for_peeking():
    fut = toy_returns(500, seed=1)
    assert abs(lookahead_correlation(fut, fut)) > 0.95


def test_timestamp_monotonic():
    assert timestamp_monotonic([1, 2, 3]) is True
    assert timestamp_monotonic([1, 3, 2]) is False

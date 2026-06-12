# -*- coding: utf-8 -*-
"""Deterministic tests for the named anti-overfitting statistics (seeded, offline)."""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from backtest_sanity import (  # noqa: E402
    deflated_sharpe_ratio, minimum_track_record_length,
    probabilistic_sharpe_ratio, probability_of_backtest_overfitting,
)
from backtest_sanity._synth import toy_returns  # noqa: E402
from backtest_sanity.overfit import _norm_cdf, _norm_ppf  # noqa: E402


# helpers — normal CDF / inverse CDF round-trip
def test_norm_ppf_inverts_cdf():
    for p in (0.001, 0.05, 0.5, 0.95, 0.999):
        assert abs(_norm_cdf(_norm_ppf(p)) - p) < 1e-7


def test_norm_ppf_rejects_bounds():
    with pytest.raises(ValueError):
        _norm_ppf(0.0)
    with pytest.raises(ValueError):
        _norm_ppf(1.0)


# PSR
def test_psr_real_edge_beats_flat_noise():
    edge = probabilistic_sharpe_ratio(toy_returns(500, edge=0.01, sigma=0.01, seed=1))
    flat = probabilistic_sharpe_ratio(toy_returns(500, edge=0.0, sigma=0.01, seed=2))
    assert edge["psr"] > 0.99
    assert edge["psr"] > flat["psr"]
    assert 0.0 < flat["psr"] < 0.95


def test_psr_more_data_more_confidence():
    short = probabilistic_sharpe_ratio(toy_returns(30, edge=0.002, sigma=0.01, seed=3))
    long = probabilistic_sharpe_ratio(toy_returns(3000, edge=0.002, sigma=0.01, seed=3))
    assert long["psr"] > short["psr"]


def test_psr_rejects_degenerate_series():
    with pytest.raises(ValueError):
        probabilistic_sharpe_ratio([0.01, 0.02])           # too short
    with pytest.raises(ValueError):
        probabilistic_sharpe_ratio([0.01] * 100)            # zero variance
    with pytest.raises(ValueError):
        probabilistic_sharpe_ratio([0.01, float("nan"), 0.02, 0.0])


# MinTRL
def test_mintrl_rises_with_confidence_and_benchmark():
    rets = toy_returns(1000, edge=0.002, sigma=0.01, seed=4)
    base = minimum_track_record_length(rets, confidence=0.90)
    stricter = minimum_track_record_length(rets, confidence=0.99)
    higher_bar = minimum_track_record_length(rets, benchmark_sr=0.1, confidence=0.90)
    assert stricter["min_n"] > base["min_n"]
    assert higher_bar["min_n"] > base["min_n"]


def test_mintrl_infinite_when_sharpe_below_benchmark():
    rets = toy_returns(500, edge=0.0, sigma=0.01, seed=5)
    res = minimum_track_record_length(rets, benchmark_sr=1.0)
    assert res["min_n"] == float("inf") and res["sufficient"] is False


def test_mintrl_sufficient_for_strong_long_record():
    rets = toy_returns(2000, edge=0.01, sigma=0.01, seed=6)
    res = minimum_track_record_length(rets, confidence=0.95)
    assert res["sufficient"] is True and res["min_n"] < 2000


def test_mintrl_rejects_bad_confidence():
    with pytest.raises(ValueError):
        minimum_track_record_length(toy_returns(100, seed=7), confidence=1.0)


# DSR
def test_dsr_more_trials_lower_dsr():
    rets = toy_returns(500, edge=0.003, sigma=0.01, seed=8)
    few = deflated_sharpe_ratio(rets, trial_sharpes=[-0.05, 0.05])
    many = deflated_sharpe_ratio(rets, trial_sharpes=[-0.05, 0.05] * 25)
    assert many["expected_max_sharpe"] > few["expected_max_sharpe"]
    assert many["dsr"] < few["dsr"]


def test_dsr_below_psr_when_trials_exist():
    rets = toy_returns(500, edge=0.003, sigma=0.01, seed=9)
    psr = probabilistic_sharpe_ratio(rets)["psr"]
    dsr = deflated_sharpe_ratio(rets, trial_sharpes=[0.02, -0.03, 0.05, 0.1])["dsr"]
    assert dsr < psr


def test_dsr_rejects_single_trial():
    with pytest.raises(ValueError):
        deflated_sharpe_ratio(toy_returns(100, seed=10), trial_sharpes=[0.5])


# PBO / CSCV
def _noise_matrix(t=320, n=20, seed=0):
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, 0.01, (t, n))


def test_pbo_high_for_pure_noise():
    res = probability_of_backtest_overfitting(_noise_matrix(seed=11), n_blocks=8)
    assert res["pbo"] > 0.35       # noise winner is random OOS — around 0.5
    assert res["n_combinations"] == 70


def test_pbo_drops_for_genuinely_strong_variant():
    m = _noise_matrix(seed=12)
    m[:, 0] += 0.02                # one variant with a real (synthetic) edge
    noise = probability_of_backtest_overfitting(_noise_matrix(seed=12), n_blocks=8)
    strong = probability_of_backtest_overfitting(m, n_blocks=8)
    assert strong["pbo"] < noise["pbo"]
    assert strong["pbo"] < 0.1


def test_pbo_caps_combinations_deterministically():
    res = probability_of_backtest_overfitting(
        _noise_matrix(t=400, seed=13), n_blocks=12, max_combinations=50)
    again = probability_of_backtest_overfitting(
        _noise_matrix(t=400, seed=13), n_blocks=12, max_combinations=50)
    assert res["n_combinations"] == 50
    assert res["pbo"] == again["pbo"]


def test_pbo_rejects_bad_inputs():
    with pytest.raises(ValueError):
        probability_of_backtest_overfitting(np.zeros(100))          # 1-D
    with pytest.raises(ValueError):
        probability_of_backtest_overfitting(np.zeros((100, 1)))     # one trial
    with pytest.raises(ValueError):
        probability_of_backtest_overfitting(_noise_matrix(), n_blocks=7)   # odd
    with pytest.raises(ValueError):
        probability_of_backtest_overfitting(_noise_matrix(t=10), n_blocks=8)
    m = _noise_matrix()
    m[0, 0] = float("nan")
    with pytest.raises(ValueError):
        probability_of_backtest_overfitting(m)

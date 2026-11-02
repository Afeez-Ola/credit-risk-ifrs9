"""Unit tests for src/capital.py.

Run: uv run pytest
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from capital import (  # noqa: E402
    OUTPUT_FLOOR,
    PD_INPUT_FLOOR,
    SA_RETAIL_RW,
    breakeven_pd,
    floor_path,
    irb_retail_rw,
    portfolio_rwa,
    retail_correlation,
    share_below,
)


def test_correlation_bounds():
    assert retail_correlation(1e-9) == pytest.approx(0.16, abs=1e-6)
    assert retail_correlation(0.999) == pytest.approx(0.03, abs=1e-6)


def test_risk_weight_increases_with_pd_up_to_high_pd():
    pds = np.array([0.001, 0.01, 0.05, 0.1, 0.2])
    assert np.all(np.diff(irb_retail_rw(pds, 0.45)) > 0)


def test_risk_weight_is_linear_in_lgd():
    assert irb_retail_rw(0.02, 0.6) == pytest.approx(2 * irb_retail_rw(0.02, 0.3))


def test_pd_input_floor_applies():
    assert irb_retail_rw(0.0, 0.45) == pytest.approx(irb_retail_rw(PD_INPUT_FLOOR, 0.45))


def test_hand_computed_risk_weight():
    # PD 1%, LGD 45%: R = 0.03w + 0.16(1-w), w = (1-e^-0.35)/(1-e^-35)
    w = (1 - np.exp(-0.35)) / (1 - np.exp(-35))
    r = 0.03 * w + 0.16 * (1 - w)
    from scipy.stats import norm
    k = 0.45 * (norm.cdf((norm.ppf(0.01) + np.sqrt(r) * norm.ppf(0.999)) / np.sqrt(1 - r)) - 0.01)
    assert irb_retail_rw(0.01, 0.45) == pytest.approx(12.5 * k)


def test_breakeven_pd_hits_floor_exactly():
    for share in OUTPUT_FLOOR.values():
        p = breakeven_pd(share, 0.65)
        assert irb_retail_rw(p, 0.65) == pytest.approx(share * SA_RETAIL_RW, rel=1e-6)


def test_breakeven_rises_as_floor_phases_in():
    pds = [breakeven_pd(s, 0.65) for s in OUTPUT_FLOOR.values()]
    assert pds == sorted(pds)


def test_floor_path_never_below_irb_and_flags_binding():
    path = floor_path(irb_rwa=100.0, sa_rwa=180.0)
    assert (path["floored_rwa"] >= path["irb_rwa"]).all()
    # 2030: 0.725 x 180 = 130.5 > 100 -> binds; 2025: 90 < 100 -> does not
    assert not path.loc[path["year"] == 2025, "floor_binds"].item()
    assert path.loc[path["year"] == 2030, "floor_binds"].item()


def test_portfolio_rwa_and_share_below():
    pd_ = pd.Series([0.001, 0.2])
    ead = pd.Series([100.0, 300.0])
    r = portfolio_rwa(pd_, ead, 0.45)
    assert r["sa_rwa"] == pytest.approx(0.75 * 400)
    assert r["irb_rwa"] == pytest.approx(100 * irb_retail_rw(0.001, 0.45) + 300 * irb_retail_rw(0.2, 0.45))
    assert share_below(pd_, ead, 0.01) == pytest.approx(0.25)


def test_breakeven_edge_cases():
    assert breakeven_pd(0.725, 0.05) == 1.0          # tiny LGD: floor always binds
    assert breakeven_pd(0.0001, 0.65) == PD_INPUT_FLOOR  # negligible floor: never binds

"""Unit tests for src/stress.py on small hand-built frames.

Run: uv run pytest  (or: python -m pytest tests)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config import LGD, SICR_PD_FLOOR, TARGET  # noqa: E402
from stress import (  # noqa: E402
    apply_stress,
    calibration_drift_multiplier,
    first_breach,
    migration,
    reverse_stress_grid,
    severe_vintage_multiplier,
    summarise,
    vintage_default_rates,
)


def book() -> pd.DataFrame:
    """Three performing loans and one defaulted loan."""
    return pd.DataFrame(
        {
            TARGET: [0, 0, 0, 1],
            "pd_12m": [0.02, 0.06, 0.10, 0.30],
            "pd_origination": [0.02, 0.05, 0.04, 0.10],
            "term": [36, 36, 60, 36],
            "ead": [1000.0, 1000.0, 1000.0, 1000.0],
            "stage": [1, 1, 2, 3],
            "sample": ["train", "test", "test", "test"],
            "issue_d": pd.to_datetime(["2010-01-01", "2016-01-01", "2017-01-01", "2018-01-01"]),
        }
    )


def test_baseline_reproduces_input_stages():
    s = apply_stress(book(), 1.0)
    assert s["stage"].tolist() == [1, 1, 2, 3]
    assert migration(s) == 0


def test_stage3_is_fixed_and_fully_provisioned():
    s = apply_stress(book(), 2.5)
    assert s.loc[3, "stage"] == 3
    assert s.loc[3, "ecl"] == pytest.approx(LGD * 1000.0)


def test_stress_moves_loan_to_stage2():
    # loan 1: 0.06 * 2 = 0.12 >= 2 * 0.05 and >= floor -> Stage 2
    s = apply_stress(book(), 2.0)
    assert s.loc[1, "stage"] == 2
    assert migration(s) == 1


def test_floor_blocks_low_pd_migration():
    # loan 0: 0.02 * 2 = 0.04 doubles origination PD but is below the floor
    assert 0.04 < SICR_PD_FLOOR
    s = apply_stress(book(), 2.0)
    assert s.loc[0, "stage"] == 1


def test_pd_is_capped_at_one():
    s = apply_stress(book(), 50.0)
    assert s["pd_stress"].max() <= 1.0


def test_ecl_is_monotonic_in_multiplier():
    grid = reverse_stress_grid(book(), np.array([1.0, 1.5, 2.0, 3.0]))
    assert grid["performing_ecl"].is_monotonic_increasing
    assert grid.loc[0, "ecl_vs_base"] == pytest.approx(1.0)


def test_summary_total_row_adds_up():
    s = apply_stress(book(), 1.3)
    t = summarise(s, "x").set_index("stage")
    assert t.loc["total", "ecl"] == pytest.approx(t.drop("total")["ecl"].sum())


def test_calibration_drift_uses_test_sample_only():
    # test sample: observed 1/3 (one default in three), predicted mean (0.06 + 0.10 + 0.30) / 3
    m = calibration_drift_multiplier(book())
    assert m == pytest.approx((1 / 3) / (0.46 / 3))


def test_severe_multiplier_uses_mature_eligible_vintages():
    df = pd.DataFrame(
        {
            TARGET: [1] * 20 + [0] * 80 + [1] * 10 + [0] * 90 + [1] * 50 + [0] * 50,
            "issue_d": pd.to_datetime(["2008-06-01"] * 100 + ["2010-06-01"] * 100 + ["2016-06-01"] * 100),
        }
    )
    v = vintage_default_rates(df, min_loans=50)
    assert not v.loc[2016, "eligible"]          # young vintage excluded
    assert severe_vintage_multiplier(v) == pytest.approx(0.20 / 0.15)


def test_first_breach():
    grid = pd.DataFrame({"pd_multiplier": [1.0, 1.5, 2.0], "x": [0.1, 0.4, 0.9]})
    assert first_breach(grid, "x", 0.4) == 1.5
    assert first_breach(grid, "x", 2.0) is None

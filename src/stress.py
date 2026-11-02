"""Stress testing helpers for the IFRS 9 ECL model.

Pure functions, no file I/O, so they can be unit tested on small frames.
The runner script 09_stress_test.py does the reading and writing.

Design choices (documented in docs/model_risk_note.md):
- Stress is applied as a multiplier on the 12-month PD.
- Multipliers are derived from this dataset (calibration drift and the
  spread of vintage default rates), not from a regulatory scenario.
- Performing loans are re-staged under stress with the same SICR rule
  as 04_staging.py, so Stage 1 -> Stage 2 migration (the "cliff") is
  part of the result. Stage 3 (defaulted) is held fixed.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import LGD, SICR_PD_FLOOR, SICR_PD_RATIO, TARGET


@dataclass(frozen=True)
class Scenario:
    name: str
    pd_multiplier: float
    source: str


# ------------------------------------------------------------ derivation
def vintage_default_rates(df: pd.DataFrame, min_loans: int = 1000) -> pd.DataFrame:
    """Observed default rate by issue year, with a maturity flag.

    A vintage is 'mature' when even a 60-month loan issued that year could
    have reached its term by the last issue date in the data. Only mature
    vintages are used to size the severe scenario, because the dataset
    keeps resolved loans only, which biases young vintages toward early
    defaults.
    """
    year = df["issue_d"].dt.year
    last_year = int(year.max())
    out = (
        df.assign(vintage=year)
        .groupby("vintage")
        .agg(loans=(TARGET, "size"), default_rate=(TARGET, "mean"))
    )
    out["mature"] = out.index <= last_year - 5
    out["eligible"] = out["mature"] & (out["loans"] >= min_loans)
    return out


def calibration_drift_multiplier(df: pd.DataFrame) -> float:
    """Observed / predicted default rate on the out-of-time test sample."""
    test = df[df["sample"] == "test"]
    return float(test[TARGET].mean() / test["pd_12m"].mean())


def severe_vintage_multiplier(vintages: pd.DataFrame) -> float:
    """Worst eligible vintage default rate / loan-weighted average."""
    elig = vintages[vintages["eligible"]]
    if elig.empty:
        raise ValueError("No eligible vintages: lower min_loans or check data")
    avg = float(np.average(elig["default_rate"], weights=elig["loans"]))
    return float(elig["default_rate"].max() / avg)


# ------------------------------------------------------------ mechanics
def lifetime_pd(pd_12m: pd.Series, term_months: pd.Series) -> pd.Series:
    """Same constant-hazard simplification as 05_ecl.py."""
    return 1 - (1 - pd_12m) ** (term_months / 12)


def apply_stress(df: pd.DataFrame, multiplier: float) -> pd.DataFrame:
    """Return loan-level stage, PD and ECL under one PD multiplier."""
    out = df[[TARGET, "pd_12m", "pd_origination", "term", "ead", "stage"]].copy()
    out["stage_base"] = out["stage"]
    out["pd_stress"] = (out["pd_12m"] * multiplier).clip(upper=1.0)

    sicr = (out["pd_stress"] >= SICR_PD_RATIO * out["pd_origination"]) & (
        out["pd_stress"] >= SICR_PD_FLOOR
    )
    out["stage"] = np.where(out[TARGET] == 1, 3, np.where(sicr, 2, 1))

    pd_life = lifetime_pd(out["pd_stress"], out["term"])
    pd_ecl = out["pd_stress"].where(out["stage"] == 1, pd_life)
    pd_ecl = pd_ecl.where(out["stage"] != 3, 1.0)
    out["ecl"] = pd_ecl * LGD * out["ead"]
    return out


def summarise(stressed: pd.DataFrame, scenario: str) -> pd.DataFrame:
    """ECL, exposure and coverage by stage, plus a total row."""
    by_stage = stressed.groupby("stage").agg(
        loans=("ecl", "size"), exposure=("ead", "sum"), ecl=("ecl", "sum")
    )
    total = pd.DataFrame(
        {
            "loans": [by_stage["loans"].sum()],
            "exposure": [by_stage["exposure"].sum()],
            "ecl": [by_stage["ecl"].sum()],
        },
        index=pd.Index(["total"], name="stage"),
    )
    by_stage.index = by_stage.index.astype(str)
    res = pd.concat([by_stage, total])
    res["coverage_ratio"] = res["ecl"] / res["exposure"]
    res.insert(0, "scenario", scenario)
    return res.reset_index()


def migration(stressed: pd.DataFrame) -> int:
    """Number of loans moved from Stage 1 to Stage 2 by the stress."""
    return int(((stressed["stage_base"] == 1) & (stressed["stage"] == 2)).sum())


def reverse_stress_grid(
    df: pd.DataFrame, multipliers: np.ndarray
) -> pd.DataFrame:
    """Performing-book ECL and Stage 2 share across a multiplier grid."""
    rows = []
    for m in multipliers:
        s = apply_stress(df, float(m))
        perf = s[s["stage"] != 3]
        rows.append(
            {
                "pd_multiplier": round(float(m), 2),
                "performing_ecl": float(perf["ecl"].sum()),
                "stage2_loans": int((perf["stage"] == 2).sum()),
                "stage2_share_of_performing": float((perf["stage"] == 2).mean()),
            }
        )
    grid = pd.DataFrame(rows)
    base = grid.loc[grid["pd_multiplier"].sub(1.0).abs().idxmin(), "performing_ecl"]
    grid["ecl_vs_base"] = grid["performing_ecl"] / base
    return grid


def first_breach(grid: pd.DataFrame, column: str, threshold: float) -> float | None:
    """Smallest multiplier at which `column` reaches `threshold`."""
    hit = grid[grid[column] >= threshold]
    return None if hit.empty else float(hit["pd_multiplier"].iloc[0])

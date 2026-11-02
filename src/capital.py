"""Pillar 1 credit risk capital: IRB vs standardised, and the CRR3 output floor.

Pure functions, no file I/O; the runner is 10_capital.py.

Scope and simplifications (stated in docs/crr3_output_floor_brief.md):
- Performing (non-defaulted) exposures only. Defaulted exposures follow
  different rules under both approaches and are left out.
- Standardised approach: 75% risk weight for regulatory retail
  (Article 123 CRR). All loans are assumed to qualify as regulatory retail.
- IRB: the Basel / CRR "other retail" risk weight function (Article 154
  CRR), no maturity adjustment, 99.9% confidence, with a PD input floor.
- The output floor is applied here to this one portfolio. In law it
  applies to a bank's total risk-weighted assets, not portfolio by
  portfolio, so the portfolio view is illustrative.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm

SA_RETAIL_RW = 0.75          # Article 123 CRR, regulatory retail
PD_INPUT_FLOOR = 0.0005      # 0.05% retail PD input floor
CAPITAL_RATIO = 0.08         # Pillar 1 minimum, share of RWA
CONFIDENCE = 0.999

# Article 465(1) CRR III: output floor phase-in, share of standardised RWA
OUTPUT_FLOOR = {2025: 0.50, 2026: 0.55, 2027: 0.60, 2028: 0.65, 2029: 0.70, 2030: 0.725}


def retail_correlation(pd_: np.ndarray | float) -> np.ndarray | float:
    """Asset correlation for other retail exposures (3% to 16%)."""
    w = (1 - np.exp(-35 * pd_)) / (1 - np.exp(-35))
    return 0.03 * w + 0.16 * (1 - w)


def irb_retail_rw(pd_: np.ndarray | float, lgd: float) -> np.ndarray | float:
    """IRB risk weight (RWA per unit of EAD) for other retail exposures."""
    p = np.clip(pd_, PD_INPUT_FLOOR, 0.9999)
    r = retail_correlation(p)
    k = lgd * (
        norm.cdf((norm.ppf(p) + np.sqrt(r) * norm.ppf(CONFIDENCE)) / np.sqrt(1 - r)) - p
    )
    return k * 12.5


def breakeven_pd(floor_share: float, lgd: float) -> float:
    """PD below which the output floor binds for a single retail loan.

    Finds the lowest PD at which irb_retail_rw(pd, lgd) reaches
    floor_share x SA_RETAIL_RW. The retail risk weight curve peaks around
    PD 40% and then falls, so the crossing is located on a grid first.
    Returns the PD input floor if the floor never binds, and 1.0 if the
    IRB risk weight never reaches the floor (very low LGD).
    """
    target = floor_share * SA_RETAIL_RW
    grid = np.logspace(np.log10(PD_INPUT_FLOOR), np.log10(0.5), 400)
    above = np.nonzero(irb_retail_rw(grid, lgd) >= target)[0]
    if above.size == 0:
        return 1.0
    i = int(above[0])
    if i == 0:
        return PD_INPUT_FLOOR
    return float(brentq(lambda p: irb_retail_rw(p, lgd) - target, grid[i - 1], grid[i]))


def portfolio_rwa(pd_: pd.Series, ead: pd.Series, lgd: float) -> dict[str, float]:
    """IRB and standardised RWA for a set of performing exposures."""
    irb = float((irb_retail_rw(pd_.to_numpy(), lgd) * ead.to_numpy()).sum())
    sa = float(SA_RETAIL_RW * ead.sum())
    return {"ead": float(ead.sum()), "irb_rwa": irb, "sa_rwa": sa,
            "irb_to_sa": irb / sa if sa else float("nan")}


def floor_path(irb_rwa: float, sa_rwa: float) -> pd.DataFrame:
    """Floored RWA and capital for each phase-in year."""
    rows = []
    for year, share in OUTPUT_FLOOR.items():
        floor = share * sa_rwa
        floored = max(irb_rwa, floor)
        rows.append({
            "year": year,
            "floor_share": share,
            "floor_rwa": floor,
            "irb_rwa": irb_rwa,
            "floored_rwa": floored,
            "floor_binds": floor > irb_rwa,
            "add_on_rwa": floored - irb_rwa,
            "capital": CAPITAL_RATIO * floored,
        })
    return pd.DataFrame(rows)


def breakeven_table(lgds: list[float]) -> pd.DataFrame:
    """Breakeven PD for each phase-in year and LGD level."""
    rows = []
    for lgd in lgds:
        for year, share in OUTPUT_FLOOR.items():
            rows.append({"lgd": lgd, "year": year, "floor_share": share,
                         "breakeven_pd": breakeven_pd(share, lgd)})
    return pd.DataFrame(rows)


def share_below(pd_: pd.Series, ead: pd.Series, threshold: float) -> float:
    """Share of exposure with PD below a threshold."""
    return float(ead[pd_ < threshold].sum() / ead.sum())

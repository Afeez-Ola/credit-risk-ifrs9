"""10: Pillar 1 capital, IRB vs standardised, and the CRR3 output floor.

Question: does the CRR3 output floor bind for this consumer book, and how
does capital move under the stress scenarios from 09?

Outputs (reports/):
- capital_summary.csv       IRB vs SA RWA and capital, by scenario
- capital_floor_by_year.csv floored RWA 2025 to 2030, baseline
- capital_breakeven.csv     PD below which the floor binds, by LGD
- capital_by_grade.csv      IRB vs SA by Lending Club grade, baseline
- capital_dashboard.xlsx    the tables above in one workbook
- capital_rw_curve.png      IRB risk weight vs PD, with SA and floor lines

Run after 01 to 06 (and 09 is not required).
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from capital import (  # noqa: E402
    CAPITAL_RATIO,
    OUTPUT_FLOOR,
    SA_RETAIL_RW,
    breakeven_pd,
    breakeven_table,
    floor_path,
    irb_retail_rw,
    portfolio_rwa,
    share_below,
)
from config import EAD_FACTOR, LGD, REPORTS, SCENARIOS, SCORED_PARQUET, TARGET  # noqa: E402
from stress import (  # noqa: E402
    calibration_drift_multiplier,
    severe_vintage_multiplier,
    vintage_default_rates,
)

LGD_GRID = [0.10, 0.20, 0.30, 0.45, LGD]


def main() -> None:
    df = pd.read_parquet(SCORED_PARQUET)
    df["ead"] = df["loan_amnt"] * EAD_FACTOR
    perf = df[df[TARGET] == 0]
    print(f"Performing loans: {len(perf):,}  EAD {perf['ead'].sum() / 1e9:.2f}bn  "
          f"mean PD {perf['pd_12m'].mean():.4f}  LGD {LGD:.0%}")

    # ---- scenarios (same multipliers as 09) ---------------------------
    downside = next(s for n, _, s in SCENARIOS if n == "downside")
    scenarios = {
        "baseline": 1.0,
        "severe_vintage": severe_vintage_multiplier(vintage_default_rates(df)),
        "calibration_drift": calibration_drift_multiplier(df),
        "policy_downside": downside,
    }
    rows = []
    for name, m in scenarios.items():
        pd_s = (perf["pd_12m"] * m).clip(upper=1.0)
        r = portfolio_rwa(pd_s, perf["ead"], LGD)
        r.update(scenario=name, pd_multiplier=round(m, 3),
                 irb_capital=CAPITAL_RATIO * r["irb_rwa"],
                 sa_capital=CAPITAL_RATIO * r["sa_rwa"])
        rows.append(r)
    summary = pd.DataFrame(rows)[["scenario", "pd_multiplier", "ead", "irb_rwa", "sa_rwa",
                                  "irb_to_sa", "irb_capital", "sa_capital"]]
    base_irb = summary.loc[0, "irb_rwa"]
    summary["irb_rwa_vs_baseline"] = summary["irb_rwa"] / base_irb
    print("\n", summary.round(3).to_string(index=False))

    # ---- output floor path, baseline ------------------------------------
    base = summary.iloc[0]
    path = floor_path(base["irb_rwa"], base["sa_rwa"])
    print("\n", path.round(3).to_string(index=False))

    # ---- breakeven PD by LGD, and share of book below it ------------------
    be = breakeven_table(LGD_GRID)
    be["exposure_share_below"] = [
        share_below(perf["pd_12m"], perf["ead"], p) for p in be["breakeven_pd"]
    ]
    print("\n", be.round(5).to_string(index=False))

    # ---- by grade ------------------------------------------------------------
    grades = []
    for g, grp in perf.groupby("grade"):
        r = portfolio_rwa(grp["pd_12m"], grp["ead"], LGD)
        r.update(grade=g, loans=len(grp), mean_pd=float(grp["pd_12m"].mean()))
        grades.append(r)
    by_grade = pd.DataFrame(grades)[["grade", "loans", "mean_pd", "ead", "irb_rwa",
                                     "sa_rwa", "irb_to_sa"]]
    print("\n", by_grade.round(3).to_string(index=False))

    # ---- save ------------------------------------------------------------------
    REPORTS.mkdir(exist_ok=True)
    summary.to_csv(REPORTS / "capital_summary.csv", index=False)
    path.to_csv(REPORTS / "capital_floor_by_year.csv", index=False)
    be.to_csv(REPORTS / "capital_breakeven.csv", index=False)
    by_grade.to_csv(REPORTS / "capital_by_grade.csv", index=False)
    with pd.ExcelWriter(REPORTS / "capital_dashboard.xlsx") as xw:
        summary.to_excel(xw, sheet_name="Scenarios", index=False)
        path.to_excel(xw, sheet_name="Output floor", index=False)
        be.to_excel(xw, sheet_name="Breakeven PD", index=False)
        by_grade.to_excel(xw, sheet_name="By grade", index=False)

    grid = np.logspace(np.log10(0.0005), np.log10(0.5), 300)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for lgd in [0.20, 0.45, LGD]:
        ax.plot(grid, 100 * irb_retail_rw(grid, lgd), label=f"IRB other retail, LGD {lgd:.0%}")
    ax.axhline(100 * SA_RETAIL_RW, color="black", linewidth=1, label="Standardised 75%")
    full = OUTPUT_FLOOR[2030] * SA_RETAIL_RW
    ax.axhline(100 * full, color="grey", linestyle="--", linewidth=1,
               label="Output floor 2030 (72.5% x 75%)")
    ax.axvline(perf["pd_12m"].median(), color="#c55a11", linestyle=":", linewidth=1,
               label="Median PD of this book")
    ax.axvline(breakeven_pd(OUTPUT_FLOOR[2030], LGD), color="grey", linestyle=":", linewidth=1,
               label=f"Floor binds below this PD (2030, LGD {LGD:.0%})")
    ax.set_xscale("log")
    ax.set_xlabel("PD (log scale)")
    ax.set_ylabel("Risk weight (%)")
    ax.set_title("Where the CRR3 output floor binds for retail loans")
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(REPORTS / "capital_rw_curve.png", dpi=150)

    print(f"\n-> {REPORTS}/capital_*.csv, capital_dashboard.xlsx, capital_rw_curve.png")


if __name__ == "__main__":
    main()

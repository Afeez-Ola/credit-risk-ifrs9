"""09: Stress test and reverse stress test.

Question: what does a downturn do to ECL, and where does the model break?

Scenarios (PD multipliers), all derived from this dataset:
- baseline: 1.0
- calibration_drift: observed / predicted default rate on the
  out-of-time test sample (the model already under-predicts later
  vintages, see reports/calibration.csv)
- policy_downside: the judgemental 1.30 downside in config.SCENARIOS,
  kept for comparison
- severe_vintage: worst mature vintage default rate / average of mature
  vintages

Reverse stress test: the smallest PD multiplier that raises performing
ECL by 50%, and the smallest that pushes Stage 2 above 10% of the
performing book.

Run after 01 to 06. Outputs go to reports/.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from config import EAD_FACTOR, REPORTS, SCENARIOS, SCORED_PARQUET  # noqa: E402
from stress import (  # noqa: E402
    Scenario,
    apply_stress,
    calibration_drift_multiplier,
    first_breach,
    migration,
    reverse_stress_grid,
    severe_vintage_multiplier,
    summarise,
    vintage_default_rates,
)

ECL_BREACH = 1.5          # performing ECL up 50% vs baseline
STAGE2_BREACH = 0.10      # Stage 2 above 10% of performing loans
GRID = np.round(np.arange(1.0, 3.01, 0.05), 2)


def main() -> None:
    df = pd.read_parquet(SCORED_PARQUET)
    if "ead" not in df.columns:
        df["ead"] = df["loan_amnt"] * EAD_FACTOR

    # ---- derive scenarios -------------------------------------------
    vintages = vintage_default_rates(df)
    downside = next(s for n, _, s in SCENARIOS if n == "downside")
    scenarios = [
        Scenario("baseline", 1.0, "no stress"),
        Scenario("calibration_drift", calibration_drift_multiplier(df),
                 "OOT observed / predicted default rate"),
        Scenario("policy_downside", downside, "config.SCENARIOS (judgemental)"),
        Scenario("severe_vintage", severe_vintage_multiplier(vintages),
                 "worst mature vintage / mature average"),
    ]
    print(vintages.round(4))
    for s in scenarios:
        print(f"{s.name:<18} x{s.pd_multiplier:.3f}  ({s.source})")

    # ---- run scenarios ----------------------------------------------
    tables, moves = [], []
    for s in scenarios:
        stressed = apply_stress(df, s.pd_multiplier)
        tables.append(summarise(stressed, s.name))
        moves.append({"scenario": s.name, "pd_multiplier": s.pd_multiplier,
                      "source": s.source,
                      "stage1_to_stage2": migration(stressed)})
    summary = pd.concat(tables, ignore_index=True)
    base_total = summary.query("scenario == 'baseline' and stage == 'total'")["ecl"].iloc[0]
    summary["ecl_vs_baseline_total"] = summary["ecl"] / base_total
    print(summary.round(4).to_string(index=False))

    # ---- reverse stress test ----------------------------------------
    grid = reverse_stress_grid(df, GRID)
    ecl_hit = first_breach(grid, "ecl_vs_base", ECL_BREACH)
    s2_hit = first_breach(grid, "stage2_share_of_performing", STAGE2_BREACH)
    print(f"\nPerforming ECL +{ECL_BREACH - 1:.0%} first reached at x{ecl_hit}")
    print(f"Stage 2 > {STAGE2_BREACH:.0%} of performing first reached at x{s2_hit}")

    # ---- save ---------------------------------------------------------
    REPORTS.mkdir(exist_ok=True)
    vintages.to_csv(REPORTS / "vintage_default_rates.csv")
    pd.DataFrame(moves).to_csv(REPORTS / "stress_scenarios.csv", index=False)
    summary.to_csv(REPORTS / "stress_summary.csv", index=False)
    grid.to_csv(REPORTS / "stress_reverse.csv", index=False)

    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    ax1.plot(grid["pd_multiplier"], grid["ecl_vs_base"], color="#1f4e79",
             label="Performing ECL vs baseline")
    ax1.set_xlabel("PD multiplier")
    ax1.set_ylabel("Performing ECL / baseline")
    ax2 = ax1.twinx()
    ax2.plot(grid["pd_multiplier"], 100 * grid["stage2_share_of_performing"],
             color="#c55a11", linestyle="--", label="Stage 2 share (%)")
    ax2.set_ylabel("Stage 2 share of performing loans (%)")
    for s in scenarios[1:]:
        ax1.axvline(s.pd_multiplier, color="grey", linewidth=0.8, linestyle=":")
        ax1.text(s.pd_multiplier, ax1.get_ylim()[1], s.name, rotation=90,
                 va="top", ha="right", fontsize=8, color="grey")
    ax1.set_title("Reverse stress test: ECL and Stage 2 migration")
    fig.legend(loc="lower right", bbox_to_anchor=(0.86, 0.2), fontsize=8)
    fig.tight_layout()
    fig.savefig(REPORTS / "stress_curve.png", dpi=150)

    print(f"\n-> {REPORTS}/stress_summary.csv, stress_scenarios.csv, "
          "stress_reverse.csv, vintage_default_rates.csv, stress_curve.png")


if __name__ == "__main__":
    main()

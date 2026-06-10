"""05: Expected Credit Loss.

ECL = PD x LGD x EAD, probability-weighted across macro scenarios.
Stage 1 -> 12-month PD. Stage 2 and 3 -> lifetime PD.
LGD and EAD are assumptions (see config.py) -- stated limitation.
"""

import pandas as pd

from config import SCORED_PARQUET, REPORTS, LGD, EAD_FACTOR, SCENARIOS


def lifetime_pd(pd_12m: pd.Series, term_months: pd.Series) -> pd.Series:
    """Naive lifetime PD: constant hazard extended over the loan term.

    P(lifetime) = 1 - (1 - PD_12m)^(term_years)
    Simplification documented in the report; a vintage-based term
    structure would be the production-grade approach.
    """
    years = term_months / 12
    return 1 - (1 - pd_12m) ** years


def main() -> None:
    df = pd.read_parquet(SCORED_PARQUET)

    df["ead"] = df["loan_amnt"] * EAD_FACTOR
    df["pd_lifetime"] = lifetime_pd(df["pd_12m"], df["term"])

    # PD horizon depends on stage
    df["pd_ecl"] = df["pd_12m"].where(df["stage"] == 1, df["pd_lifetime"])
    df.loc[df["stage"] == 3, "pd_ecl"] = 1.0   # credit-impaired

    # Probability-weighted macro scenarios
    df["ecl"] = 0.0
    for name, weight, pd_scalar in SCENARIOS:
        scen_pd = (df["pd_ecl"] * pd_scalar).clip(upper=1.0)
        df["ecl"] += weight * scen_pd * LGD * df["ead"]

    # ---- portfolio summary ------------------------------------------
    summary = df.groupby("stage").agg(
        loans=("ecl", "size"),
        exposure=("ead", "sum"),
        ecl=("ecl", "sum"),
    )
    summary["coverage_ratio"] = summary["ecl"] / summary["exposure"]
    print(summary)

    REPORTS.mkdir(exist_ok=True)
    summary.to_csv(REPORTS / "ecl_summary.csv")
    df.to_parquet(SCORED_PARQUET)
    print(f"-> {REPORTS / 'ecl_summary.csv'}")

    # TODO: scenario sensitivity table (ECL under each scenario alone).
    # TODO: discounting at the effective interest rate (int_rate).


if __name__ == "__main__":
    main()

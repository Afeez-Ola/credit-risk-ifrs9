"""06: Model validation.

Discrimination (AUC/Gini, by segment), calibration (predicted vs
observed default rates by decile), stability (PSI between train and
test populations). Outputs feed the model documentation report.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from config import SCORED_PARQUET, REPORTS, TARGET


def calibration_table(df: pd.DataFrame, n_bins: int = 10) -> pd.DataFrame:
    """Predicted vs observed default rate by PD decile (test sample)."""
    test = df[df["sample"] == "test"].copy()
    test["decile"] = pd.qcut(test["pd_12m"], n_bins, labels=False)
    return test.groupby("decile").agg(
        loans=(TARGET, "size"),
        predicted=("pd_12m", "mean"),
        observed=(TARGET, "mean"),
    )


def psi(expected: pd.Series, actual: pd.Series, n_bins: int = 10) -> float:
    """Population Stability Index between two score distributions.

    Rule of thumb: < 0.10 stable, 0.10-0.25 monitor, > 0.25 shifted.
    """
    edges = np.quantile(expected, np.linspace(0, 1, n_bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    e = pd.cut(expected, edges).value_counts(normalize=True).sort_index()
    a = pd.cut(actual, edges).value_counts(normalize=True).sort_index()
    e, a = e.clip(lower=1e-6), a.clip(lower=1e-6)
    return float(((a - e) * np.log(a / e)).sum())


def main() -> None:
    df = pd.read_parquet(SCORED_PARQUET)
    train = df[df["sample"] == "train"]
    test = df[df["sample"] == "test"]

    # ---- discrimination ----------------------------------------------
    auc = roc_auc_score(test[TARGET], test["pd_12m"])
    print(f"Out-of-time AUC: {auc:.4f} | Gini: {2 * auc - 1:.4f}")

    # By grade: does the model rank-order within grades too?
    for g, grp in test.groupby("grade"):
        if grp[TARGET].nunique() == 2:
            g_auc = roc_auc_score(grp[TARGET], grp["pd_12m"])
            print(f"  grade {g}: AUC {g_auc:.3f} ({len(grp):,} loans)")

    # ---- calibration ----------------------------------------------------
    cal = calibration_table(df)
    print("\nCalibration by decile:\n", cal)

    # ---- stability -------------------------------------------------------
    score_psi = psi(train["pd_12m"], test["pd_12m"])
    print(f"\nScore PSI train->test: {score_psi:.4f}")

    REPORTS.mkdir(exist_ok=True)
    cal.to_csv(REPORTS / "calibration.csv")

    # TODO: calibration plot (predicted vs observed) -> reports/
    # TODO: PSI per feature to localize any drift.
    # TODO: write findings into reports/model_documentation.md


if __name__ == "__main__":
    main()

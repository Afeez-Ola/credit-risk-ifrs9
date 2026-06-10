"""04: IFRS 9 stage allocation.

Stage 1: performing, no significant increase in credit risk (SICR).
Stage 2: SICR since origination -> lifetime ECL.
Stage 3: credit-impaired (defaulted).

SICR rule implemented here: current PD at least SICR_PD_RATIO times the
origination PD AND above an absolute floor (SICR_PD_FLOOR). Both
parameters live in config.py and must be justified in the report.

NOTE on this dataset: all loans are resolved, so 'origination PD' and
'current PD' come from the same model score. For the portfolio exercise
we simulate a reporting date by treating the model PD as current PD and
a grade-based long-run average as origination PD. Document this clearly.
"""

import pandas as pd

from config import (
    SCORED_PARQUET, TARGET, SICR_PD_RATIO, SICR_PD_FLOOR,
)


def assign_stage(row) -> int:
    """Return IFRS 9 stage (1, 2 or 3) for a single exposure."""
    if row[TARGET] == 1:                      # proxy for credit-impaired
        return 3
    sicr = (
        row["pd_12m"] >= SICR_PD_RATIO * row["pd_origination"]
        and row["pd_12m"] >= SICR_PD_FLOOR
    )
    return 2 if sicr else 1


def main() -> None:
    df = pd.read_parquet(SCORED_PARQUET)

    # Origination PD proxy: long-run average PD of the loan's grade
    df["pd_origination"] = df.groupby("grade")["pd_12m"].transform("mean")

    df["stage"] = df.apply(assign_stage, axis=1)
    print(df["stage"].value_counts(normalize=True).sort_index())

    df.to_parquet(SCORED_PARQUET)
    print(f"-> {SCORED_PARQUET} (with stage column)")

    # TODO: add days-past-due backstop (30dpd -> Stage 2) if a dpd
    #       field is available in your dataset version.
    # TODO: sensitivity analysis: how stage shares move when
    #       SICR_PD_RATIO varies between 1.5 and 3.0.


if __name__ == "__main__":
    main()

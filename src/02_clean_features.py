"""02: Build the clean modeling table.

Target definition, at-origination feature selection, type fixes,
missing-value treatment, derived credit history length.
"""

import pandas as pd

from config import (
    RESOLVED_PARQUET, CLEAN_PARQUET, FEATURES, TARGET, BAD_STATUS,
)

EMP_MAP = {
    "< 1 year": 0, "1 year": 1, "2 years": 2, "3 years": 3,
    "4 years": 4, "5 years": 5, "6 years": 6, "7 years": 7,
    "8 years": 8, "9 years": 9, "10+ years": 10,
}


def main() -> None:
    df = pd.read_parquet(RESOLVED_PARQUET)

    # ---- target ----------------------------------------------------
    df[TARGET] = (df["loan_status"] == BAD_STATUS).astype(int)

    # ---- feature selection (robust to missing columns) -------------
    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        print("Missing from this dataset version:", missing)
    features = [c for c in FEATURES if c in df.columns]
    df = df[features + [TARGET]]

    # ---- type fixes -------------------------------------------------
    # term: " 36 months" -> 36  (unconditional: pandas>=3 uses 'str' dtype)
    df["term"] = df["term"].astype(str).str.extract(r"(\d+)").astype(int)

    for col in ["int_rate", "revol_util"]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].astype(str).str.rstrip("%").astype(float)

    # emp_length: ordinal; missing kept as its own signal (-1)
    df["emp_length"] = df["emp_length"].map(EMP_MAP).fillna(-1).astype(int)

    # ---- derived: credit history length at origination ---------------
    df["issue_d"] = pd.to_datetime(df["issue_d"], format="%b-%Y")
    df["earliest_cr_line"] = pd.to_datetime(
        df["earliest_cr_line"], format="%b-%Y"
    )
    df["credit_history_years"] = (
        (df["issue_d"] - df["earliest_cr_line"]).dt.days / 365.25
    )
    df = df.drop(columns=["earliest_cr_line"])

    # ---- remaining numeric gaps: neutral median fill ------------------
    for col in ["mort_acc", "revol_util", "dti",
                "pub_rec_bankruptcies", "inq_last_6mths"]:
        df[col] = df[col].fillna(df[col].median())

    # ---- health check -------------------------------------------------
    print(f"Default rate: {df[TARGET].mean():.4f}")
    print(f"Remaining missing values: {df.isna().sum().sum()}")
    print(df.dtypes)

    df.to_parquet(CLEAN_PARQUET)
    print(f"-> {CLEAN_PARQUET}")


if __name__ == "__main__":
    main()

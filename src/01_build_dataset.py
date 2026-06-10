"""01: Filter the raw Lending Club CSV down to resolved loans.

Reads loan.csv in chunks, keeps Fully Paid / Charged Off only,
saves a parquet so the raw CSV is never read again.
"""

import pandas as pd

from config import RAW_CSV, RESOLVED_PARQUET, KEEP_STATUSES


def main() -> None:
    # Full-file status overview (fast: single column)
    status = pd.read_csv(RAW_CSV, usecols=["loan_status"])
    print(status["loan_status"].value_counts(), "\n")

    # Keep resolved loans only, chunked to spare RAM
    chunks = pd.read_csv(RAW_CSV, chunksize=200_000, low_memory=False)
    df = pd.concat(c[c["loan_status"].isin(KEEP_STATUSES)] for c in chunks)

    RESOLVED_PARQUET.parent.mkdir(exist_ok=True)
    df.to_parquet(RESOLVED_PARQUET)
    print(f"Saved {len(df):,} resolved loans, {df.shape[1]} columns")
    print(f"-> {RESOLVED_PARQUET}")


if __name__ == "__main__":
    main()

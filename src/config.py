"""Central configuration: paths, column lists, model settings."""

from pathlib import Path

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "reports"

RAW_CSV = DATA / "loan.csv"
RESOLVED_PARQUET = DATA / "loans_resolved.parquet"
CLEAN_PARQUET = DATA / "model_data_clean.parquet"
SCORED_PARQUET = DATA / "loans_scored.parquet"
PD_MODEL_FILE = DATA / "pd_model.joblib"

# ------------------------------------------------------------- statuses
GOOD_STATUS = "Fully Paid"
BAD_STATUS = "Charged Off"
KEEP_STATUSES = [GOOD_STATUS, BAD_STATUS]

# -------------------------------------------- forbidden (post-origination)
LEAKAGE_COLS = [
    "out_prncp", "out_prncp_inv", "total_pymnt", "total_pymnt_inv",
    "total_rec_prncp", "total_rec_int", "total_rec_late_fee",
    "recoveries", "collection_recovery_fee", "last_pymnt_d",
    "last_pymnt_amnt", "next_pymnt_d", "last_credit_pull_d",
    "last_fico_range_high", "last_fico_range_low", "pymnt_plan",
    "debt_settlement_flag", "settlement_status", "settlement_date",
    "settlement_amount", "settlement_percentage", "settlement_term",
    "hardship_flag", "hardship_type", "hardship_reason", "hardship_status",
]

# ----------------------------------------- usable at-origination features
FEATURES = [
    "loan_amnt", "term", "int_rate", "installment", "grade", "sub_grade",
    "emp_length", "home_ownership", "annual_inc", "verification_status",
    "purpose", "dti", "delinq_2yrs",
    "inq_last_6mths", "open_acc", "pub_rec", "revol_bal", "revol_util",
    "total_acc", "mort_acc", "pub_rec_bankruptcies",
    "earliest_cr_line", "issue_d", "addr_state", "application_type",
]

CATEGORICAL = [
    "grade", "sub_grade", "home_ownership", "verification_status",
    "purpose", "addr_state", "application_type",
]

TARGET = "default_flag"

# ------------------------------------------------------------- modeling
TRAIN_QUANTILE = 0.8        # time-based split: oldest 80% train
RANDOM_STATE = 42

# ----------------------------------------------------- IFRS 9 parameters
# SICR rule: lifetime PD at reporting date vs at origination
SICR_PD_RATIO = 2.0         # Stage 2 if PD has at least doubled
SICR_PD_FLOOR = 0.05        # ...and absolute PD above this floor

# Assumption-based LGD/EAD (documented limitations)
LGD = 0.65                  # unsecured consumer lending assumption
EAD_FACTOR = 1.0            # term loans: EAD = outstanding principal

# Macro scenarios: (name, weight, PD scalar)
SCENARIOS = [
    ("base", 0.60, 1.00),
    ("upside", 0.20, 0.85),
    ("downside", 0.20, 1.30),
]

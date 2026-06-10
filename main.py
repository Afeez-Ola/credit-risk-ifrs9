import pandas as pd


leakage_cols = [
    "out_prncp", "out_prncp_inv", "total_pymnt", "total_pymnt_inv",
    "total_rec_prncp", "total_rec_int", "total_rec_late_fee",
    "recoveries", "collection_recovery_fee", "last_pymnt_d",
    "last_pymnt_amnt", "next_pymnt_d", "last_credit_pull_d",
    "last_fico_range_high", "last_fico_range_low", "pymnt_plan",
    "debt_settlement_flag", "settlement_status", "settlement_date",
    "settlement_amount", "settlement_percentage", "settlement_term",
    "hardship_flag", "hardship_type", "hardship_reason", "hardship_status",
]

features = [
    "loan_amnt", "term", "int_rate", "installment", "grade", "sub_grade",
    "emp_length", "home_ownership", "annual_inc", "verification_status",
    "purpose", "dti", "delinq_2yrs", "fico_range_low", "fico_range_high",
    "inq_last_6mths", "open_acc", "pub_rec", "revol_bal", "revol_util",
    "total_acc", "mort_acc", "pub_rec_bankruptcies",
    "earliest_cr_line", "issue_d", "addr_state", "application_type",
]



df = pd.read_parquet("loans_resolved.parquet")

# Target
df["default_flag"] = (df["loan_status"] == "Charged Off").astype(int)

# Keep only features + target
df = df[features + ["default_flag"]]

# Quick health check
print(df["default_flag"].mean())          # ~0.20
print(df.isna().mean().sort_values(ascending=False).head(10))
df.to_parquet("model_data.parquet")

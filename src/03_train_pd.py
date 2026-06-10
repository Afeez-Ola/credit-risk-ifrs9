"""03: Train the PD model.

Out-of-time split (train on older vintages, test on later ones),
logistic regression baseline, AUC/Gini. Saves model + scored loans.
"""

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config import (
    CLEAN_PARQUET, SCORED_PARQUET, PD_MODEL_FILE,
    CATEGORICAL, TARGET, TRAIN_QUANTILE, RANDOM_STATE,
)


def main() -> None:
    df = pd.read_parquet(CLEAN_PARQUET)

    # ---- out-of-time split -----------------------------------------
    cutoff = df["issue_d"].quantile(TRAIN_QUANTILE)
    train = df[df["issue_d"] <= cutoff]
    test = df[df["issue_d"] > cutoff]
    print(f"Train: {len(train):,} loans up to {cutoff:%Y-%m}")
    print(f"Test:  {len(test):,} loans after")

    num_cols = [c for c in df.columns
                if c not in CATEGORICAL + [TARGET, "issue_d"]]

    X_train, y_train = train[CATEGORICAL + num_cols], train[TARGET]
    X_test, y_test = test[CATEGORICAL + num_cols], test[TARGET]

    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ("num", StandardScaler(), num_cols),
    ])

    model = Pipeline([
        ("prep", pre),
        ("clf", LogisticRegression(max_iter=1000,
                                   random_state=RANDOM_STATE)),
    ])

    model.fit(X_train, y_train)

    # ---- evaluation ---------------------------------------------------
    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    print(f"Out-of-time AUC: {auc:.4f}  |  Gini: {2 * auc - 1:.4f}")

    # ---- persist model + PD scores for staging/ECL ---------------------
    joblib.dump(model, PD_MODEL_FILE)
    df["pd_12m"] = model.predict_proba(df[CATEGORICAL + num_cols])[:, 1]
    df["sample"] = (df["issue_d"] <= cutoff).map(
        {True: "train", False: "test"}
    )
    df.to_parquet(SCORED_PARQUET)
    print(f"-> {PD_MODEL_FILE}\n-> {SCORED_PARQUET}")

    # TODO (challenger): XGBoost with identical split, compare AUC.
    # TODO (banking convention): WOE binning + scorecard variant.


if __name__ == "__main__":
    main()

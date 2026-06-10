"""07: XGBoost challenger vs logistic regression champion.

Identical data, identical out-of-time split, so the comparison is fair.
"""

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

from config import CLEAN_PARQUET, CATEGORICAL, TARGET, TRAIN_QUANTILE, RANDOM_STATE

df = pd.read_parquet(CLEAN_PARQUET)

cutoff = df["issue_d"].quantile(TRAIN_QUANTILE)
train = df[df["issue_d"] <= cutoff]
test = df[df["issue_d"] > cutoff]

num_cols = [c for c in df.columns if c not in CATEGORICAL + [TARGET, "issue_d"]]
X_train, y_train = train[CATEGORICAL + num_cols], train[TARGET]
X_test, y_test = test[CATEGORICAL + num_cols], test[TARGET]

pre = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
], remainder="passthrough")  # trees don't need scaling

model = Pipeline([
    ("prep", pre),
    ("clf", XGBClassifier(
        n_estimators=400,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="auc",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )),
])

model.fit(X_train, y_train)
auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
print(f"XGBoost OOT AUC: {auc:.4f} | Gini: {2*auc - 1:.4f}")
print("Champion (logistic) was: AUC 0.7013 | Gini 0.4026")
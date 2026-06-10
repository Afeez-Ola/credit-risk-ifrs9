# credit-risk-ifrs9

End to end IFRS 9 expected credit loss model on Lending Club data:
PD modeling, stage allocation, LGD/EAD assumptions, ECL computation,
and model validation.

## Pipeline

Scripts run in order. Each reads the output of the previous one.

```
src/
  config.py             Paths, feature lists, leakage columns, settings
  01_build_dataset.py   Filter resolved loans from raw CSV -> parquet
  02_clean_features.py  Target, feature selection, cleaning -> model table
  03_train_pd.py        Time-based split, logistic regression PD, AUC/Gini
  04_staging.py         IFRS 9 stage allocation (SICR rules)
  05_ecl.py             LGD/EAD assumptions, ECL = PD x LGD x EAD
  06_validation.py      Discrimination, calibration, stability (PSI)
```

## Setup

```bash
uv sync
```

Place `loan.csv` (Kaggle Lending Club dataset) in `data/`.

## Run

## Results

PD model (logistic regression, out-of-time test on 242,856 loans
issued after 2016-10):

| Metric | Value |
|---|---|
| AUC | 0.7013 |
| Gini | 0.4026 |
| Score PSI (train -> test) | 0.011 |

The model rank-orders risk even within Lending Club grades
(within-grade AUC 0.59 to 0.65), adding information beyond the
lender's own rating. Calibration analysis shows observed default
rates exceeding predictions in mid deciles, reflecting worsening
post-2016 vintages and motivating recalibration with a margin of
conservatism.

Portfolio ECL by stage (see reports/ecl_summary.csv):
Stage 1: 1.03M loans, 12.7% coverage | Stage 2: 9.7k loans, 41.1% |
Stage 3: 262k loans, 63.1%.

| Model | OOT AUC | Gini |
|---|---|---|
| Logistic regression (champion) | 0.7013 | 0.4026 |
| XGBoost (challenger) | 0.7122 | 0.4243 |

The modest challenger lift indicates the predictive ceiling lies in the at-origination information set, not model capacity. The interpretable champion is retained as the primary model.

```bash
uv run python src/01_build_dataset.py
uv run python src/02_clean_features.py
uv run python src/03_train_pd.py
uv run python src/04_staging.py
uv run python src/05_ecl.py
uv run python src/06_validation.py
```

## Key methodology decisions

- **Leakage control**: only information available at loan origination is
  used as model input. All payment, recovery, hardship, and settlement
  fields are excluded (see `LEAKAGE_COLS` in `config.py`).
- **Out-of-time validation**: the model is trained on older vintages and
  tested on later ones, mirroring how a deployed model is used.
- **Population**: resolved loans only (Fully Paid / Charged Off).
  Pre-policy-change loans and the 31 ambiguous "Default" records are
  excluded.

## Stated limitations

- FICO scores are not present in this public dataset version; `grade`,
  `sub_grade`, and `int_rate` act as credit quality proxies.
- LGD and EAD are assumption-based, not modeled from recovery data.
- Macroeconomic scenario weights are illustrative.

## Author

Bolaji — MSc Quantitative Asset and Risk Management, University of
Economics in Katowice.

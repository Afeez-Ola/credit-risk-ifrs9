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
uv add pandas pyarrow scikit-learn matplotlib
```

Place `loan.csv` (Kaggle Lending Club dataset) in `data/`.

## Run

```bash
uv run python src/01_build_dataset.py
uv run python src/02_clean_features.py
uv run python src/03_train_pd.py
# 04-06 as they are implemented
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

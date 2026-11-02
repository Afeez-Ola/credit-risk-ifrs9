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
  07_challenger.py      XGBoost challenger on the same out-of-time split
  08_sicr_sensitivity.py  Stage 2 share and ECL as the SICR threshold moves
  stress.py             Stress testing functions (unit tested in tests/)
  09_stress_test.py     Data-derived stress scenarios + reverse stress test
docs/
  model_risk_note.md    Validation-style findings and recommended actions
  stress_test_memo.md   One-page summary of the stress test
```

## Setup

```bash
uv sync
```

Place `loan.csv` (Kaggle Lending Club dataset) in `data/`.

## Run

```bash
uv run python src/01_build_dataset.py
uv run python src/02_clean_features.py
uv run python src/03_train_pd.py
uv run python src/04_staging.py
uv run python src/05_ecl.py
uv run python src/06_validation.py
uv run python src/07_challenger.py
uv run python src/08_sicr_sensitivity.py
uv run python src/09_stress_test.py
uv run pytest
```

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

## Stress testing

`09_stress_test.py` asks what a downturn does to ECL and which
assumption breaks first. Stress is a multiplier on the 12-month PD, and
performing loans are re-staged under each scenario so Stage 1 to Stage 2
migration is captured. Scenarios come from the data, not a regulator:

| Scenario | PD multiplier | Source |
|---|---|---|
| Calibration drift | 1.10 | Observed / predicted default rate, out-of-time sample |
| Policy downside | 1.30 | Judgemental downside in `config.py` |
| Severe vintage | from data | Worst mature vintage / mature average |

A reverse stress test finds the multiplier at which performing ECL rises
50% and at which Stage 2 exceeds 10% of performing loans. Outputs:
`reports/stress_summary.csv`, `stress_scenarios.csv`,
`stress_reverse.csv`, `vintage_default_rates.csv`, `stress_curve.png`.

Validation-style findings, including the SICR threshold sensitivity
(Stage 2 ECL 62.9m at 2.0x vs 482.0m at 1.5x), are in
[`docs/model_risk_note.md`](docs/model_risk_note.md).

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

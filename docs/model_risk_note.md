# Model risk note: IFRS 9 ECL model (Lending Club)

Written in the style of an independent validation finding. Figures are taken from the files in `reports/`, produced by scripts 03 to 08.

## 1. Scope and intended use
- **Model:** logistic regression 12-month PD, rule-based IFRS 9 staging, and ECL = PD x LGD x EAD weighted across three scenarios.
- **Portfolio:** resolved Lending Club consumer loans (Fully Paid or Charged Off), 1.30 million loans.
- **Intended use:** a learning and portfolio exercise showing the IFRS 9 workflow end to end. It is not fit for regulatory or accounting use (see section 3).

## 2. Evidence reviewed

| Area | Test | Result | Read |
|---|---|---|---|
| Discrimination | Out-of-time AUC / Gini (242,856 test loans) | 0.7013 / 0.4026 | Acceptable for application data only |
| Discrimination | Within-grade AUC | 0.59 to 0.65 | Adds information beyond the lender's grade |
| Benchmark | XGBoost challenger, same split | AUC 0.7122 | Small lift; champion kept for interpretability |
| Stability | Score PSI, train to test | 0.011 | Stable (below 0.10) |
| Calibration | Observed vs predicted default rate, test sample | 21.6% vs 19.6% (x1.10) | **Finding 1** |
| Staging | SICR ratio sensitivity | Stage 2 ECL 62.9m at 2.0x, 482.0m at 1.5x | **Finding 2** |

## 3. Findings

**Finding 1: the PD model under-predicts later vintages (medium).**
On the out-of-time sample, observed defaults are 1.10 times predicted overall. Observed exceeds predicted in every decile, and the gap is largest in the middle of the distribution: decile 6 is 26.2% observed against 22.5% predicted (x1.17). The top decile is close (x1.00). Rank ordering holds (stable PSI, AUC 0.70), so this is a level problem, not a ranking problem.
*Action:* recalibrate the intercept on recent vintages, or apply a margin of conservatism of at least the observed ratio. The stress test uses x1.10 as its "calibration drift" scenario.

**Finding 2: ECL depends heavily on one judgemental staging parameter (high).**
Lowering the SICR ratio from 2.0 to 1.5 moves Stage 2 from 9,680 loans (0.93%) to 74,978 loans (7.2%) and raises Stage 2 ECL from 62.9m to 482.0m, about 7.7 times higher. Raising it to 3.0 leaves 442 loans in Stage 2. Without data to justify 2.0, the reported ECL is largely a choice of threshold.
*Action:* justify the threshold against observed default rates by migration bucket, report the sensitivity next to the headline ECL, and add a days-past-due backstop if such a field is available.

**Finding 3: the SICR test does not measure deterioration (high).**
"Origination PD" is the grade average of the same model score, so a loan is Stage 2 when it is riskier than its grade peers, not when its risk has increased since origination. This is a dataset limitation (no second observation date), but it changes what Stage 2 means.
*Action:* state this wherever Stage 2 figures appear. A production model needs PD at origination stored and a PD at each reporting date.

**Finding 4: the Stage 3 population reflects a closed book (medium).**
Every charged-off loan is in Stage 3 (261,655 loans, 20.1% of the book, 63.1% coverage). That describes a historical, resolved portfolio, not a book at a reporting date, so total coverage (23.8%) is not comparable with a live consumer book.

**Finding 5: LGD, EAD, lifetime PD and discounting are simplified (medium).**
- LGD is a flat 65% assumption.
- EAD is the original loan amount, which overstates exposure on amortising loans.
- Lifetime PD assumes a constant hazard.
- ECL is not discounted at the effective interest rate.
Each of these biases ECL upward or adds unmeasured error.
*Action:* estimate LGD from the recovery fields (allowed for LGD, though excluded from PD features), amortise EAD, and build a vintage-based PD term structure.

**Finding 6: reproducibility gap (low, fixed).**
`07_challenger.py` imported `xgboost`, which was not listed in `pyproject.toml`, so a fresh `uv sync` could not run it. The dependency is now added, together with `pytest` for the stress test unit tests.

## 4. Stress testing
`src/09_stress_test.py` (added with this note) applies PD multipliers taken from the data:
- the calibration drift of finding 1 (x1.10)
- the judgemental downside in `config.py` (x1.30)
- a severe scenario sized from the worst mature vintage

It re-stages performing loans under each scenario, so the Stage 1 to Stage 2 cliff behind finding 2 shows up in the results. Results are in `reports/stress_*.csv` and `reports/stress_curve.png`.

| Scenario | PD x | Performing ECL | Stage 1 to 2 migrations | Total ECL |
|---|---|---|---|---|
| Severe vintage (2012 vs 2008 to 2013 average) | 1.045 | +5.2% | 3,916 | +2.1% |
| Calibration drift | 1.101 | +12.0% | 10,576 | +4.9% |
| Policy downside | 1.30 | +40.3% | 54,347 | +16.6% |

Reverse stress: performing ECL +50% at x1.40; Stage 2 above 10% of performing loans at x1.45.

**Finding 7: provisions are convex in PD because of staging (high).** A 30% PD shock raises performing ECL by 40% and Stage 2 ECL by 7.35 times, as loans cross the SICR threshold into lifetime ECL. This confirms finding 2 under stress.

**Finding 8: the history holds no usable severe scenario (medium).** The worst mature vintage is only 4.5% above the mature average, and the 2008 vintage (15.8%) defaulted less than 2012 (16.2%). The model's own calibration drift is a larger shock than any mature vintage.
*Action:* size severe scenarios from external macroeconomic data (for example unemployment-linked PD shifts) instead of this portfolio's history.

## 5. Overall view
The model ranks risk reasonably and is stable. The level of predicted PD is too low on recent vintages, and the ECL figure is driven more by staging and LGD/EAD assumptions than by the PD model. Priorities: (1) justify the SICR threshold, (2) recalibrate, (3) replace the flat LGD/EAD assumptions.

## 6. Recalibration triggers (proposed)
- Observed / predicted default rate on a new vintage outside 0.9 to 1.1.
- Score PSI above 0.10 against the development sample.
- Out-of-time AUC below 0.65.

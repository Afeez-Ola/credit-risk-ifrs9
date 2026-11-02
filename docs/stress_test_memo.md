# Stress testing a consumer IFRS 9 model: what moves and what breaks

*Olanrewaju Afeez Bolaji, MSc Quantitative Asset and Risk Management, University of Economics in Katowice*
*Code: github.com/Afeez-Ola/credit-risk-ifrs9 (`src/09_stress_test.py`, outputs in `reports/stress_*`)*

**The question.** A risk team needs to know two things about an ECL model: how much provisions rise in a downturn, and which assumption gives way first. I tested this on my IFRS 9 model built on 1,303,607 resolved Lending Club consumer loans (out-of-time AUC 0.70).

**Method.** I applied stress as a multiplier on the 12-month PD and re-staged every performing loan with the model's own SICR rule, so loans can migrate from Stage 1 to Stage 2. All scenarios come from the data, not from a regulator:
- **calibration drift (x1.101):** the model predicts 19.6% defaults on the out-of-time sample, while 21.6% defaulted
- **policy downside (x1.30):** the judgemental downside already in the model
- **severe vintage (x1.045):** the worst mature vintage (2012) against the 2008 to 2013 average

A reverse stress test finds the multiplier at which performing ECL rises 50%, and the one at which Stage 2 exceeds 10% of performing loans.

**Results.** Performing book: 1,041,952 loans, baseline ECL 1.86bn.

| Scenario | PD x | Performing ECL | Stage 1 to 2 migrations | Stage 2 ECL | Total ECL |
|---|---|---|---|---|---|
| Severe vintage | 1.045 | +5.2% | 3,916 | x1.41 | +2.1% |
| Calibration drift | 1.101 | +12.0% | 10,576 | x2.14 | +4.9% |
| Policy downside | 1.30 | +40.3% | 54,347 | x7.35 | +16.6% |

Reverse stress: performing ECL rises 50% at a PD multiplier of **x1.40**, and Stage 2 exceeds 10% of performing loans at **x1.45**.

**What breaks first: the staging rule.** Provisions rise faster than PD. A 30% PD shock raises performing ECL by 40%, because 54,347 loans cross the SICR threshold and move from 12-month to lifetime ECL; Stage 2 provisions rise 7.35 times. The same cliff appears when the threshold itself moves: at 1.5x instead of 2.0x origination PD, Stage 2 ECL is 482.0m instead of 62.9m with no change in borrower risk.

**A second finding: this dataset holds no real downturn.** The worst mature vintage is only 4.5% above the mature average. The 2008 vintage defaulted at 15.8%, below 2012, because Lending Club was small and selective at the time. The model's own drift on recent loans (x1.101) is a bigger shock than anything in the mature history, so a credible severe scenario needs external macro data rather than this portfolio's past.

**Limitations.**
1. The scenarios come from one lender's history, so this is not a macroeconomic or regulatory stress test.
2. "Origination PD" is a grade average, so Stage 2 measures relative risk, not deterioration over time.
3. LGD (flat 65%), EAD (original amount) and undiscounted ECL bias the absolute levels. The relative movements are the result.
4. The baseline here is a single unweighted scenario (total ECL 4.50bn), slightly different from the probability-weighted figure in `reports/ecl_summary.csv` (4.48bn).

Full findings: `docs/model_risk_note.md`.

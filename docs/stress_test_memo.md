# Stress testing a consumer IFRS 9 model: what moves and what breaks

*Olanrewaju Afeez Bolaji, MSc Quantitative Asset and Risk Management, University of Economics in Katowice*
*Code and data pipeline: github.com/Afeez-Ola/credit-risk-ifrs9*

**The question.** A risk team needs to know two things about an ECL model: how much provisions rise in a downturn, and which assumption gives way first. I tested this on my IFRS 9 model built on 1.30 million resolved Lending Club consumer loans (out-of-time AUC 0.70).

**Method.** I applied stress as a multiplier on the 12-month PD and re-staged every performing loan with the model's own SICR rule, so loans can migrate from Stage 1 to Stage 2. All scenarios come from the data, not from a regulator:
- calibration drift: the model under-predicts defaults on later vintages by a factor of 1.10
- the 1.30 judgemental downside already in the model
- a severe scenario sized from the worst mature vintage

I also ran a reverse stress test to find the multiplier at which performing ECL rises 50%, and the multiplier at which Stage 2 exceeds 10% of performing loans.

**Results.**

| Scenario | PD multiplier | Total ECL vs baseline | Stage 1 to 2 migrations |
|---|---|---|---|
| Calibration drift | 1.10 | [from stress_summary.csv] | [ ] |
| Policy downside | 1.30 | [ ] | [ ] |
| Severe vintage | [ ] | [ ] | [ ] |

Reverse stress: performing ECL +50% at x[ ]; Stage 2 above 10% at x[ ].

**What breaks first.** The staging rule. Moving the SICR threshold from 2.0x to 1.5x origination PD already raises Stage 2 ECL from 62.9m to 482.0m, a 7.7 times increase, with no change in borrower risk. In a downturn, the cliff between Stage 1 and Stage 2 drives provisions more than the PD level does. [Confirm with the reverse stress results.]

**Limitations.**
1. The scenarios come from one lender's history, so they are not a macroeconomic or regulatory stress test.
2. "Origination PD" is a grade average, so Stage 2 measures relative risk, not deterioration over time.
3. LGD (flat 65%), EAD (original amount) and undiscounted ECL bias the absolute numbers. The relative movements are the result.

Full findings: `docs/model_risk_note.md`.

# The CRR3 output floor: who it hits, and why a consumer lender should look elsewhere

*Olanrewaju Afeez Bolaji, MSc Quantitative Asset and Risk Management, University of Economics in Katowice*
*Code: github.com/Afeez-Ola/credit-risk-ifrs9 (`src/capital.py`, `src/10_capital.py`, outputs in `reports/capital_*`)*

## The question
CRR3, the EU implementation of the final Basel III reforms, has applied since 1 January 2025. Its best known change is the output floor: risk-weighted assets (RWA) from a bank's internal models (IRB) may not fall below a set share of what the standardised approach would give. The share phases in from 50% in 2025 to 72.5% in 2030 (Article 465(1) CRR III).

Does the floor matter for a high-yield unsecured consumer book, and if not, what does?

## Method
I used my IFRS 9 model of 1.3 million Lending Club consumer loans.
- **Scope:** performing loans only, with the model's 12-month PD and the model's 65% LGD assumption.
- **IRB RWA:** the CRR "other retail" risk weight function (Article 154 CRR).
- **Standardised RWA:** 75% for regulatory retail (Article 123 CRR).
- **Output floor:** applied for each phase-in year.
- **Stress:** the PD shocks from my stress test (x1.045, x1.101 and x1.30).

## Finding 1: the floor binds only for low-risk retail loans
The floor binds when a loan's IRB risk weight falls below the floor share of 75%. Solving the risk weight function gives the PD below which that happens:

| LGD | 2025 (50%) | 2027 (60%) | 2030 (72.5%) |
|---|---|---|---|
| 65% (this book's assumption) | PD below 0.35% | below 0.47% | below 0.66% |
| 45% | below 0.66% | below 0.96% | below 1.59% |
| 30% | below 1.78% | below 5.83% | below 12.3% |
| 20% (secured-like) | below 13.4% | below 20.5% | at every PD |

**Reading:** the floor is a problem for low-LGD, low-PD books, such as mortgages, prime cards and secured lending. In an unsecured book with high LGD it barely bites.

## Finding 2: for this book the bank's own model already costs far more
Performing book: 1,041,952 loans, exposure 14.73bn.
- Only **0.03%** of exposure has a PD below the 2030 breakeven (0.66%). The floor RWA in 2030 is 8.01bn against IRB RWA of 19.62bn, so IRB sits 2.45 times above the fully phased floor.
- IRB RWA is **1.78 times** standardised RWA. The gap widens with risk: grade A 1.30x, grade C 1.96x, grades E to G about 2.2x.
- Pillar 1 capital at 8%: **IRB 1.57bn vs standardised 0.88bn**, 0.69bn (78%) more on IRB.
- **LGD sensitivity:** if LGD were 30% instead of 65%, the floor would bind for 35% of exposure by 2030. The answer depends heavily on LGD, which is an assumption in this model.

## Finding 3: under stress, capital moves much less than provisions

| Scenario | PD x | IRB RWA vs baseline | IRB capital | Standardised capital |
|---|---|---|---|---|
| Baseline | 1.00 | 1.000 | 1.57bn | 0.88bn |
| Severe vintage | 1.045 | +1.1% | 1.59bn | 0.88bn |
| Calibration drift | 1.101 | +2.4% | 1.61bn | 0.88bn |
| Policy downside | 1.30 | +5.7% | 1.66bn | 0.88bn |

The same x1.30 shock raises performing ECL by 40% in my IFRS 9 stress test, but IRB RWA by only 5.7%. The reason is that most of this book sits on the flat upper part of the retail risk weight curve (mean PD from 5.9% in grade A to 47.6% in grade G), where extra PD adds little capital, while expected loss rises in proportion to PD.

## Implications for a lender like this
1. **The output floor is not the binding constraint.** Capital planning effort is better spent on PD calibration and on the IRB versus standardised choice.
2. **For high-PD, high-LGD retail, IRB costs more than the standardised approach (78% more here).** Keeping the portfolio on IRB has to be justified by risk sensitivity and management use, not by capital relief.
3. **In a downturn the pressure arrives through provisions, not capital.** For this book, stress testing should centre on IFRS 9 ECL and its effect on CET1 through retained earnings, not on RWA growth.
4. **LGD is the parameter to get right.** It decides whether the floor ever matters, so it deserves the next modelling effort, using the recovery fields this dataset contains.

## Limitations
1. **US book, EU rules.** Lending Club is a US portfolio, so applying CRR3 is illustrative.
2. **Floor scope.** In law the floor applies to a bank's total RWA, not portfolio by portfolio. A bank with a large low-risk book could still be floored overall, and this consumer book would then carry part of that cost.
3. **Regulatory retail is assumed.** It requires granularity and size conditions to hold.
4. **Parameters are not supervisor approved.** LGD is a flat 65% assumption, EAD is the original loan amount, and there is no downturn LGD or margin of conservatism.
5. **Defaulted exposures are excluded.**

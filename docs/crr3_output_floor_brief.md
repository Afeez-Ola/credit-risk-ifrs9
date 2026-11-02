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

## Finding 2: for this book the bank's own model already costs more
[From `reports/capital_summary.csv` and `capital_by_grade.csv`, fill after running `10_capital.py`.]
- Share of exposure with PD below the 2030 breakeven: [ ]%.
- IRB RWA / standardised RWA, baseline: [ ]x. Grade A: [ ]x; grade G: [ ]x.
- Pillar 1 capital at 8%: IRB [ ]bn vs standardised [ ]bn.

## Finding 3: under stress, IRB capital rises and standardised does not
[From `capital_summary.csv`.]

| Scenario | PD x | IRB RWA vs baseline | Standardised RWA |
|---|---|---|---|
| Severe vintage | 1.045 | [ ] | unchanged |
| Calibration drift | 1.101 | [ ] | unchanged |
| Policy downside | 1.30 | [ ] | unchanged |

Together with my IFRS 9 stress test (performing ECL +40% under the x1.30 shock), this shows the same shock hitting both provisions and capital at once.

## Implications for a lender like this
1. **The output floor is not the binding constraint.** Capital planning effort is better spent on PD calibration and on the IRB versus standardised choice for this portfolio.
2. **For high-PD, high-LGD retail, IRB can be more expensive than the standardised approach.** The business case for keeping the portfolio on IRB rests on risk sensitivity and management use, not on capital relief.
3. **IRB capital is procyclical, and so are IFRS 9 provisions.** Stress testing should combine the two. A downturn raises ECL and RWA at the same time.

## Limitations
1. **US book, EU rules.** Lending Club is a US portfolio, so applying CRR3 is illustrative.
2. **Floor scope.** In law the floor applies to a bank's total RWA, not portfolio by portfolio. A bank with a large low-risk book could still be floored overall, and this consumer book would then carry part of that cost.
3. **Regulatory retail is assumed.** It requires granularity and size conditions to hold.
4. **Parameters are not supervisor approved.** LGD is a flat 65% assumption, EAD is the original loan amount, and there is no downturn LGD or margin of conservatism.
5. **Defaulted exposures are excluded.**

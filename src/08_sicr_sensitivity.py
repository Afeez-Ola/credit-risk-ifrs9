"""08: SICR threshold sensitivity.

How do stage shares and ECL move as the SICR rule tightens or loosens?
Output feeds Section 3.2 of the model documentation.
"""

import pandas as pd

from config import SCORED_PARQUET, REPORTS, SICR_PD_FLOOR, LGD, SCENARIOS

df = pd.read_parquet(SCORED_PARQUET)
performing = df[df["stage"] != 3].copy()   # Stage 3 is fixed (defaulted)

# Pre-compute the pieces of ECL that don't depend on the rule
scen_weight = sum(w * s for _, w, s in SCENARIOS)   # blended PD scalar

rows = []
for ratio in [1.5, 2.0, 2.5, 3.0]:
    sicr = (
        (performing["pd_12m"] >= ratio * performing["pd_origination"])
        & (performing["pd_12m"] >= SICR_PD_FLOOR)
    )
    stage2 = performing[sicr]

    # Stage 2 ECL: lifetime PD, blended scenarios
    ecl2 = (
        (stage2["pd_lifetime"] * scen_weight).clip(upper=1.0)
        * LGD * stage2["ead"]
    ).sum()

    rows.append({
        "sicr_ratio": ratio,
        "stage2_loans": int(sicr.sum()),
        "stage2_share_pct": round(100 * sicr.mean(), 2),
        "stage2_ecl_m": round(ecl2 / 1e6, 1),
    })

result = pd.DataFrame(rows)
print(result.to_string(index=False))
result.to_csv(REPORTS / "sicr_sensitivity.csv", index=False)
print(f"\n-> {REPORTS / 'sicr_sensitivity.csv'}")
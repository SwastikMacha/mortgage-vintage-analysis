from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 

OUT = Path(r"C:\mortgage_data\clean")

pq, pk = OUT / "loans_precovid.parquet", OUT / "loans_precovid.pkl"
loans = pd.read_parquet(pq) if pq.exists() else pd.read_pickle(pk)
loans = loans.dropna(subset=["max_age"])

# months each loan could possibly be observed before the Dec-2019 cutoff
fp = pd.to_datetime(loans["first_pmt_date"], format="%Y%m")
loans["obs_age"] = (2019 - fp.dt.year) * 12 + (12 - fp.dt.month)


def vintage_table(df, by="vintage_year", max_mob=60):
    rows = []
    for v, g in df.groupby(by):
        n = len(g)
        for m in range(1, max_mob + 1):
            e = g[g["obs_age"] >= m]              # loans observable at age m
            if len(e) < 0.5 * n:                  # stop once under half the vintage is observable
                break
            cum_def = (e["first90"] <= m).sum()
            new_def = (e["first90"] == m).sum()
            at_risk = ((e["max_age"] >= m) & ~(e["first90"] < m)).sum()
            rows.append((v, m, len(e), cum_def, 100 * cum_def / len(e),
                         new_def, at_risk,
                         100 * new_def / at_risk if at_risk else np.nan))
    return pd.DataFrame(rows, columns=["vintage", "mob", "n_loans", "cum_defaults",
                                       "cum_default_pct", "new_defaults", "at_risk",
                                       "hazard_pct"])


# ---------------- Overall vintage curves ----------------
vt = vintage_table(loans)
vt.to_csv(OUT / "vintage_curves.csv", index=False)

matrix = vt.pivot(index="vintage", columns="mob", values="cum_default_pct")
matrix.to_csv(OUT / "vintage_matrix.csv")

# sanity check: cumulative curves must never go down
dips = matrix.diff(axis=1).lt(-1e-9)
if dips.any().any():
    print("Note: small dips at the tail (shrinking cohort) for vintages:",
          list(dips.any(axis=1)[dips.any(axis=1)].index))

print("\nCumulative 90+ DPD % at 12 / 24 / 36 months on book:")
print(matrix.reindex(columns=[12, 24, 36]).round(2))

# ---------------- Charts ----------------
fig, ax = plt.subplots(1, 2, figsize=(14, 5))
matrix.T.plot(ax=ax[0], title="Cumulative 90+ DPD rate by months on book")
ax[0].set_xlabel("Loan age (months)"); ax[0].set_ylabel("% of originated loans")

hz = vt.pivot(index="vintage", columns="mob", values="hazard_pct")
hz.T.rolling(3, min_periods=1).mean().plot(
    ax=ax[1], title="Monthly hazard of first 90+ DPD (3-month rolling avg)")
ax[1].set_xlabel("Loan age (months)"); ax[1].set_ylabel("% of at-risk loans")
plt.tight_layout()
plt.savefig(OUT / "vintage_curves.png", dpi=150)
plt.show()

# ---------------- Segment cuts (examples) ----------------
loans["fico_band"] = pd.cut(loans["fico"], [0, 620, 680, 740, 900],
                            labels=["<620", "620-679", "680-739", "740+"])
loans["ltv_band"] = pd.cut(loans["ltv"], [0, 70, 80, 90, 200],
                           labels=["<=70", "71-80", "81-90", ">90"])

seg = []
for col in ["fico_band", "ltv_band"]:
    for level, g in loans.groupby(col, observed=True):
        t = vintage_table(g)
        t["segment"] = f"{col}={level}"
        seg.append(t)
seg = pd.concat(seg, ignore_index=True)
seg.to_csv(OUT / "vintage_segments.csv", index=False)

print("\n24-month cumulative 90+ DPD % by segment and vintage:")
print(seg[seg["mob"] == 24].pivot(index="segment", columns="vintage",
                                  values="cum_default_pct").round(2))
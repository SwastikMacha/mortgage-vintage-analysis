from pathlib import Path
import pandas as pd

OUT = Path(r"C:\mortgage_data\clean")
loans = pd.read_parquet(OUT / "loans_precovid.parquet").dropna(subset=["max_age"])
fp = pd.to_datetime(loans["first_pmt_date"], format="%Y%m")
loans["obs_age"] = (2019 - fp.dt.year) * 12 + (12 - fp.dt.month)
loans["fico_band"] = pd.cut(loans["fico"], [0, 620, 680, 740, 900],
                            labels=["<620", "620-679", "680-739", "740+"])

e = loans[loans["obs_age"] >= 24].copy()            # loans observable at 24 months
e["d24"] = (e["first90"] <= 24).astype(int)

mix  = pd.crosstab(e["vintage_year"], e["fico_band"], normalize="index") * 100
rate = e.pivot_table(index="fico_band", columns="vintage_year",
                     values="d24", aggfunc="mean", observed=True) * 100

base = (mix.loc[2012] / 100).reindex(rate.index)    # reference mix = 2012
result = pd.DataFrame({
    "actual_24m":       e.groupby("vintage_year")["d24"].mean() * 100,
    "at_2012_mix":      rate.mul(base, axis=0).sum(),
})
result["mix_effect"]  = result["actual_24m"] - result["at_2012_mix"]
result["perf_effect"] = result["at_2012_mix"] - result.loc[2012, "actual_24m"]

print("\nShare of loans by FICO band (%):")
print(mix.round(1))
print("\nMix vs performance decomposition (24-month 90+ DPD %):")
print(result.round(2))
result.to_csv(OUT / "mix_shift.csv")
mix.round(2).reset_index().to_csv(OUT / "mix_by_fico.csv", index=False)
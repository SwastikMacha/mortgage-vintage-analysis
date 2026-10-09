import re
from pathlib import Path
import pandas as pd

# ---------------- SETTINGS ----------------
RAW = Path(r"C:\mortgage_data\raw")        # folder with the 16 txt files
OUT = Path(r"C:\mortgage_data\clean")      # keep this OUTSIDE OneDrive
YEARS = None                            # test with one year first; set to None for all 8
# ------------------------------------------

OUT.mkdir(parents=True, exist_ok=True)

ORIG_COLS = ["fico", "first_pmt_date", "first_time_buyer", "maturity_date", "msa", "mi_pct",
             "units", "occupancy", "cltv", "dti", "orig_upb", "ltv", "int_rate", "channel",
             "ppm_flag", "amort_type", "state", "prop_type", "zip3", "loan_seq", "purpose",
             "orig_term", "n_borrowers"]
PERF_USE = [0, 1, 2, 3, 4, 8]
PERF_NAMES = ["loan_seq", "report_period", "cur_upb", "delinq", "loan_age", "zero_bal_code"]


def year_of(p):
    return int(re.search(r"(\d{4})", p.name).group(1))


def pick(pattern):
    files = [f for f in sorted(RAW.glob(pattern)) if YEARS is None or year_of(f) in YEARS]
    if not files:
        raise SystemExit(f"No files matched {pattern} in {RAW}")
    return files


# ---------------- Origination ----------------
orig = []
for f in pick("sample_orig_*.txt"):
    df = pd.read_csv(f, sep="|", header=None, usecols=range(23), names=ORIG_COLS, dtype=str)
    df["vintage_year"] = year_of(f)
    orig.append(df)
    print("orig read:", f.name, len(df), flush=True)
orig = pd.concat(orig, ignore_index=True)

for c in ["fico", "cltv", "dti", "ltv", "orig_term", "orig_upb", "int_rate"]:
    orig[c] = pd.to_numeric(orig[c], errors="coerce")

# Freddie Mac uses 9999 / 999 for "unknown"
orig["fico"] = orig["fico"].where(orig["fico"] != 9999)
for c in ["dti", "ltv", "cltv"]:
    orig[c] = orig[c].where(orig[c] != 999)

orig["vintage_q"] = (orig["first_pmt_date"].str[:4] + "Q" +
                     ((orig["first_pmt_date"].str[4:6].astype(int) - 1) // 3 + 1).astype(str))

# ---------------- Performance -> one row per loan ----------------
parts = []
for f in pick("sample_perf_*.txt"):
    for ch in pd.read_csv(f, sep="|", header=None, usecols=PERF_USE, names=PERF_NAMES,
                          dtype=str, chunksize=1_000_000):
        ch["loan_age"] = pd.to_numeric(ch["loan_age"], errors="coerce")
        ch = ch[ch["report_period"].astype(int) <= 201912]
        d = pd.to_numeric(ch["delinq"], errors="coerce")        # 'RA', 'XX' become NaN
        is90 = (d >= 3) | (ch["delinq"] == "RA")                 # 90+ DPD or REO
        ch["age90"] = ch["loan_age"].where(is90)
        parts.append(ch.groupby("loan_seq").agg(max_age=("loan_age", "max"),
                                                first90=("age90", "min")))
    print("perf done:", f.name, flush=True)

# a loan can straddle two chunks, so combine the partial results
perf = pd.concat(parts).groupby(level=0).agg(max_age=("max_age", "max"),
                                             first90=("first90", "min"))

loans = orig.merge(perf, left_on="loan_seq", right_index=True, how="left")

try:
    loans.to_parquet(OUT / "loans_precovid.parquet")
    print("saved loans_precovid.parquet")
except ImportError:
    loans.to_pickle(OUT / "loans_precovid.pkl")
    print("pyarrow missing, saved loans_precovid.pkl instead")

print("shape:", loans.shape)
print("share of loans that hit 90+ DPD:", round(loans["first90"].notna().mean(), 4))
print("loans without performance rows:", loans["max_age"].isna().sum())
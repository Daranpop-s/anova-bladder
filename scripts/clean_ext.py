"""
Clean the final 'Ext_ Bladder_dataset.csv' into the analysis-ready table.

This is the definitive dataset: coded part numbers whose prefix encodes the
bladder type (B-TU=Turnup, B-MT=MTG, B-PU=Push), plus a Diagnose column.

Two things handled explicitly here:

1. `Diagnose` (Pass/Abnormal) is exactly (Bladder Life >= Target). It is a
   restatement of the response, so it is kept for reference but must NOT be
   used as a predictor of Bladder Life (that would be circular).

2. The installation date/time is embedded in the `Bladder name` field as
   `<install-date>_<id>` (e.g. `12/4/2024_02540`). The dates use MIXED
   conventions in the same file -- some M/D/Y, some D/M/Y, some 'Month D, Y'.
   We resolve unambiguous cases exactly; ambiguous d<=12 / m<=12 cases default
   to month-first (the majority convention here) and are flagged in
   `install_date_ambiguous` so the assumption is auditable.
"""

import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

RAW = Path("data/raw")
OUT = Path("data/clean")
OUT.mkdir(parents=True, exist_ok=True)
SRC = RAW / "Ext_Bladder_dataset.csv"

CAUSE_MAP = {
    "Leak (รั่ว)": "Leak",
    "Deform (เบี้ยว, ผิดรูปร่าง)": "Deform",
    "Tear (ฉีกขาด)": "Tear",
    "B/O": "Burn out",
    "Flabby (ยืด,หย่อนยาน)": "Flabby",
    "Bad material (วัสดุไม่ดี)": "Bad material",
    "CQ เกิดปัญหาด้าน Quality": "Quality issue",
}
TYPE_MAP = {"B-TU": "Turnup", "B-MT": "MTG", "B-PU": "Push"}

MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}


def parse_install(name):
    """Return (Timestamp or NaT, ambiguous_flag) parsed from a Bladder name."""
    if not isinstance(name, str):
        return pd.NaT, False
    ds = name.split("_")[0].strip()
    # Named month, e.g. 'December 16, 2024'
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})$", ds)
    if m:
        mon = MONTHS.get(m.group(1).lower())
        if mon:
            try:
                return pd.Timestamp(int(m.group(3)), mon, int(m.group(2))), False
            except ValueError:
                return pd.NaT, False
    # Numeric a/b/Y
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", ds)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        ambiguous = False
        if a > 12:            # a must be day  -> D/M/Y
            day, mon = a, b
        elif b > 12:          # b must be day  -> M/D/Y
            mon, day = a, b
        else:                 # both <=12: default month-first, flag it
            mon, day = a, b
            ambiguous = True
        try:
            return pd.Timestamp(y, mon, day), ambiguous
        except ValueError:
            return pd.NaT, ambiguous
    return pd.NaT, False


df = pd.read_csv(SRC)
n_raw = len(df)
df = df[[c for c in df.columns if not c.startswith("Unnamed")]]

# drop the trailing blank/footer row(s)
df = df[df["LastDate"].notna()].copy()

df = df.rename(columns={
    "LastDate": "scrap_date",
    "runberpartnumber": "part_code",
    "Bladder name": "bladder_id",
    "Status": "status",
    "Cause": "cause_raw",
    "Target": "target_life",
    "Bladder Life": "bladder_life",
    "Diagnose": "diagnose",
})

df["scrap_date"] = pd.to_datetime(df["scrap_date"], format="mixed", errors="coerce")
df["bladder_life"] = pd.to_numeric(df["bladder_life"], errors="coerce")
df["target_life"] = pd.to_numeric(df["target_life"], errors="coerce")

df["cause"] = df["cause_raw"].map(CAUSE_MAP).fillna(df["cause_raw"])
df["type_code"] = df["part_code"].astype(str).str.extract(r"^(B-[A-Z]{2})")
df["bladder_type"] = df["type_code"].map(TYPE_MAP)

inst = df["bladder_id"].apply(parse_install)
df["install_date"] = [t for t, _ in inst]
df["install_date_ambiguous"] = [a for _, a in inst]


def _swap_dm(name):
    """Re-parse an ambiguous a/b/Y name as day-first instead of month-first."""
    ds = str(name).split("_")[0].strip()
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", ds)
    if not m:
        return pd.NaT
    a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return pd.Timestamp(y, b, a)  # treat 'a' as day, 'b' as month
    except ValueError:
        return pd.NaT


# Correction: an install date cannot fall after the scrap date or in the
# future. For ambiguous rows where the default (month-first) violates that,
# flip to day-first when that yields a valid, consistent date.
_today = pd.Timestamp.today().normalize()
_bad = (
    df["install_date_ambiguous"]
    & df["install_date"].notna()
    & ((df["install_date"] > df["scrap_date"]) | (df["install_date"] > _today))
)
for idx in df.index[_bad]:
    alt = _swap_dm(df.at[idx, "bladder_id"])
    if pd.notna(alt) and alt <= df.at[idx, "scrap_date"] and alt <= _today:
        df.at[idx, "install_date"] = alt
n_corrected = int(_bad.sum())
df["install_ym"] = df["install_date"].dt.to_period("M").astype(str)
df["install_quarter"] = df["install_date"].dt.to_period("Q").astype(str)
df["install_year"] = df["install_date"].dt.year

# days the unit lived on the line (sanity check vs bladder_life cycle count)
df["days_in_service"] = (df["scrap_date"] - df["install_date"]).dt.days

# response must exist
n_before = len(df)
clean = df[df["bladder_life"].notna()].copy()
n_drop_life = n_before - len(clean)

cols = [
    "scrap_date", "install_date", "install_ym", "install_quarter", "install_year",
    "install_date_ambiguous", "days_in_service",
    "part_code", "bladder_type", "cause",
    "target_life", "bladder_life", "diagnose", "bladder_id", "status",
]
clean = clean[cols].sort_values("install_date").reset_index(drop=True)
clean.to_csv(OUT / "bladder_ext_clean.csv", index=False)

print("=" * 68)
print("CLEAN: Ext_Bladder_dataset")
print("=" * 68)
print(f"raw rows                       : {n_raw}")
print(f"footer/blank removed           : {n_raw - n_before}")
print(f"dropped (no bladder_life)      : {n_drop_life}")
print(f"=> clean rows                  : {len(clean)}")
print(f"install_date parsed            : {clean['install_date'].notna().sum()}")
print(f"  of which ambiguous d/m order : {clean['install_date_ambiguous'].sum()}")
print(f"  ambiguous flipped to dayfirst: {n_corrected} (violated install<=scrap)")
neg = (clean['days_in_service'] < 0).sum()
print(f"  rows with install>scrap left : {neg}")
print(f"install period range           : {clean['install_ym'].min()} -> {clean['install_ym'].max()}")
print()
print("bladder_type counts:\n" + clean["bladder_type"].value_counts().to_string())
print("\nWrote data/clean/bladder_ext_clean.csv")

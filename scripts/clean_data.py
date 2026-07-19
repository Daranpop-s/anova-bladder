"""
Clean the raw bladder datasets into tidy, analysis-ready tables.

Primary output:  data/clean/bladder_records_clean.csv
    One row per scrapped bladder, with engineered factors ready for an
    ANOVA / factor analysis on Bladder Life (the response variable).

The raw exports are messy:
  - data_5  -> the real per-bladder scrap records (USED as the main table)
  - data_4  -> a pivot summary per part number (cleaned for reference)
  - data_2  -> a machine breakdown log (different system, cleaned separately)
  - data_3  -> just a list of month labels (a filter lookup, dropped)
  - data_6  -> just a list of day numbers  (a filter lookup, dropped)

Every export also carries trailing "Applied filters: ..." footer rows and
blank spacer rows, which are stripped here.
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

# Map the raw Thai/English cause strings to clean English failure modes.
CAUSE_MAP = {
    "Leak (รั่ว)": "Leak",
    "Deform (เบี้ยว, ผิดรูปร่าง)": "Deform",
    "Tear (ฉีกขาด)": "Tear",
    "B/O": "Burn out",
    "Flabby (ยืด,หย่อนยาน)": "Flabby",
    "Bad material (วัสดุไม่ดี)": "Bad material",
    "CQ เกิดปัญหาด้าน Quality": "Quality issue",
}


def classify_type(name: str) -> str:
    """Bladder construction type, tolerant of the many typos in the source."""
    if not isinstance(name, str):
        return "Unknown"
    s = name.lower().replace(" ", "")
    # turnup is spelled: turnup, turn up, trunup, turmup, trumup, ...
    if "mtg" in s:
        return "MTG"
    if "push" in s:
        return "Push"
    if "msb" in s:
        return "MSB"
    if "extension" in s:
        return "Extension"
    if re.search(r"t[ru][rmu]*n?up", s) or "turn" in s or "trun" in s or "trum" in s:
        return "Turnup"
    return "Other"


def extract_size(name: str):
    """Nominal bladder diameter in inches, taken as the first quoted number.

    Names use the inch mark (") and sometimes give a range like 22"23" or
    10"12"; we keep the first value as the nominal size.
    """
    if not isinstance(name, str):
        return np.nan
    m = re.search(r'(\d{1,2})\s*"', name)
    return float(m.group(1)) if m else np.nan


def extract_partno(text: str):
    """Canonical part number of the form 0216-1-1074."""
    if not isinstance(text, str):
        return np.nan
    m = re.search(r"\d{3,4}-\d-\d{3,4}", text)
    return m.group(0) if m else np.nan


def strip_footer(df: pd.DataFrame, key_col: str) -> pd.DataFrame:
    """Drop blank spacer rows and the 'Applied filters:' footer block."""
    df = df[df[key_col].notna()].copy()
    df = df[~df[key_col].astype(str).str.startswith("Applied filters")]
    df = df[~df[key_col].astype(str).str.startswith("No filters")]
    return df


# ---------------------------------------------------------------------------
# 1) data_5 : the main per-bladder scrap records
# ---------------------------------------------------------------------------
df = pd.read_excel(RAW / "data_5_bladder_records.xlsx")
n_raw = len(df)

# Footer row has LastDate blank / 'Applied filters' -> drop via LastDate.
df = df[df["LastDate"].notna()].copy()

df = df.rename(
    columns={
        "LastDate": "last_date",
        "runberpartnumber": "part_desc",
        "Bladder name": "bladder_id",
        "Status": "status",
        "Cause": "cause_raw",
        "Target": "target_life",
        "Bladder Life": "bladder_life",
    }
)

df["last_date"] = pd.to_datetime(df["last_date"], errors="coerce")
df["bladder_life"] = pd.to_numeric(df["bladder_life"], errors="coerce")
df["target_life"] = pd.to_numeric(df["target_life"], errors="coerce")

# Engineered factors
df["part_number"] = df["part_desc"].apply(extract_partno)
df["bladder_type"] = df["part_desc"].apply(classify_type)
df["size_in"] = df["part_desc"].apply(extract_size)
df["cause"] = df["cause_raw"].map(CAUSE_MAP).fillna(df["cause_raw"])
df["year_month"] = df["last_date"].dt.to_period("M").astype(str)

# reached_target only meaningful when both numbers exist
df["reached_target"] = np.where(
    df["bladder_life"].notna() & df["target_life"].notna(),
    df["bladder_life"] >= df["target_life"],
    np.nan,
)

# The response variable must exist for the analysis -> require bladder_life.
n_before = len(df)
clean = df[df["bladder_life"].notna()].copy()
n_dropped_life = n_before - len(clean)

cols = [
    "last_date",
    "year_month",
    "part_number",
    "part_desc",
    "bladder_type",
    "size_in",
    "cause",
    "target_life",
    "bladder_life",
    "reached_target",
    "bladder_id",
    "status",
]
clean = clean[cols].sort_values("last_date").reset_index(drop=True)
clean.to_csv(OUT / "bladder_records_clean.csv", index=False)

# ---------------------------------------------------------------------------
# 2) data_4 : per-part pivot summary (cleaned for reference)
# ---------------------------------------------------------------------------
s4 = pd.read_excel(RAW / "data_4_summary.xlsx")
s4 = strip_footer(s4, "Runberpartnumber")
s4 = s4.rename(
    columns={
        "Runberpartnumber": "part_desc",
        "Target": "target_life",
        "AVG B/D life": "avg_life",
        "Total Scrap bladder": "total_scrap",
        "No. B/D life not reach target": "n_below_target",
        "Max of Bladder Life": "max_life",
        "Min of Bladder Life": "min_life",
    }
)
s4["part_number"] = s4["part_desc"].apply(extract_partno)
s4["bladder_type"] = s4["part_desc"].apply(classify_type)
s4["size_in"] = s4["part_desc"].apply(extract_size)
s4.to_csv(OUT / "part_summary_clean.csv", index=False)

# ---------------------------------------------------------------------------
# 3) data_2 : machine breakdown log (separate system, light clean)
# ---------------------------------------------------------------------------
m = pd.read_excel(RAW / "data_2_machine_log.xlsx")
m = strip_footer(m, "Machine")
m = m.rename(
    columns={
        "Day": "day",
        "Title": "event_id",
        "Partnumber": "machine_partno",
        "Machine": "machine",
        "Problem": "problem",
        "ผู้ที่แก้ไข": "fixed_by",
        "Fix datail": "fix_detail",
        "DateTimeissue": "issue_dt",
        "datetimefinish": "finish_dt",
    }
)
m["issue_dt"] = pd.to_datetime(m["issue_dt"], errors="coerce")
m["finish_dt"] = pd.to_datetime(m["finish_dt"], errors="coerce")
m.to_csv(OUT / "machine_log_clean.csv", index=False)

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
print("=" * 68)
print("CLEANING SUMMARY")
print("=" * 68)
print(f"data_5 raw rows                : {n_raw}")
print(f"  - footer/blank rows removed  : {n_raw - n_before}")
print(f"  - rows w/o Bladder Life drop : {n_dropped_life}")
print(f"  => clean bladder records     : {len(clean)}")
print()
print("Factors available on the clean bladder table:")
print(f"  bladder_type : {sorted(clean['bladder_type'].unique())}")
print(f"  size_in      : {sorted(clean['size_in'].dropna().unique())}")
print(f"  cause        : {sorted(clean['cause'].dropna().unique())}")
print(f"  part_number  : {clean['part_number'].nunique()} distinct")
print(f"  date range   : {clean['last_date'].min().date()} -> {clean['last_date'].max().date()}")
print()
print("bladder_life (response) describe:")
print(clean["bladder_life"].describe().round(1).to_string())
print()
print("Records per bladder_type:")
print(clean["bladder_type"].value_counts().to_string())
print()
print("Records per cause:")
print(clean["cause"].value_counts().to_string())
print()
print("Wrote:")
for p in ["bladder_records_clean.csv", "part_summary_clean.csv", "machine_log_clean.csv"]:
    print(f"  data/clean/{p}")

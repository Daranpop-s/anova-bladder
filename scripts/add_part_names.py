"""
Attach the real part name (code stripped) to each bladder.

The Ext table uses internal codes (B-TU-007). The raw event log carries the
descriptive `runberpartnumber` (e.g. 'Bladder turnup 8" 0239-1-1137'). Join on
Title==bladder_id, strip the numeric part-number code, normalize typos, and
resolve each internal code to a canonical name by majority vote.

Writes:
  - adds `part_name` to data/clean/bladder_ext_clean.csv
  - reports/part_name_map.csv  (code -> real name, with vote confidence)
"""

import re
import warnings
import pandas as pd
from pathlib import Path

warnings.filterwarnings("ignore")

raw = pd.read_csv("data/raw/Raw_Bladder_records.csv")
ext = pd.read_csv("data/clean/bladder_ext_clean.csv")

t2name = (raw.dropna(subset=["runberpartnumber"])
             .groupby("Title")["runberpartnumber"]
             .agg(lambda s: s.mode().iloc[0]))
ext["_desc"] = t2name.reindex(ext["bladder_id"]).values


def clean_name(s):
    if not isinstance(s, str):
        return s
    s = re.sub(r"\d{3,4}-\d-\d{3,4}", "", s)          # drop part-number code
    s = re.sub(r"\bpart ?store\b", "", s, flags=re.I)  # drop 'part store' note
    # normalize the many spellings of 'turnup'
    s = re.sub(r"\bt[ru][rmu]+n?up\b", "turnup", s, flags=re.I)
    s = re.sub(r"tr[ui]n?up|tru[mn]up|turmup|trumup", "turnup", s, flags=re.I)
    s = re.sub(r"\bturn ?up\b", "turnup", s, flags=re.I)
    s = re.sub(r"\bBla[bd]+er\b", "Bladder", s, flags=re.I)
    s = re.sub(r"(MTG)\s*[Bb]ladder", "MTG Bladder", s)
    s = re.sub(r'([0-9])\s*"', r'\1" ', s)             # ensure a space after size
    s = re.sub(r"(turnup|push|MTG Bladder)(\d)", r"\1 \2", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip(' -')
    return s


ext["part_name_raw"] = ext["_desc"].apply(clean_name)

# canonical name per internal code = majority vote
canon = {}
conf_rows = []
for c in sorted(ext["part_code"].dropna().unique()):
    vc = ext.loc[ext["part_code"] == c, "part_name_raw"].value_counts()
    name = vc.index[0]
    canon[c] = name
    conf_rows.append({"part_code": c, "part_name": name,
                      "vote_share": round(vc.iloc[0] / vc.sum(), 2), "n": int(vc.sum())})

ext["part_name"] = ext["part_code"].map(canon)
ext = ext.drop(columns=["_desc", "part_name_raw"])
ext.to_csv("data/clean/bladder_ext_clean.csv", index=False)

Path("reports").mkdir(exist_ok=True)
pd.DataFrame(conf_rows).to_csv("reports/part_name_map.csv", index=False)

print("Added part_name to data/clean/bladder_ext_clean.csv")
print("Wrote reports/part_name_map.csv\n")
print(pd.DataFrame(conf_rows).to_string(index=False))

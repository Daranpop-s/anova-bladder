"""
Build the 'experience -> evidence' data-visualization journey.

reports/evidence_journey.html — regenerates from the clean data + event log.
Arc: experience (opinion) -> the table -> a fair fight (>=50% of life only) ->
pinpoint us vs manufacturer by cause -> PROVE it's us (same part, only the
machine changed) -> PROVE it's them (dies short on every machine) -> a final
action board (which variants to push up, by how much, with which fix, expected
gain). Attribution color = cause: leak=blue=manufacturer, deform=amber=us.
"""
import json, numpy as np, pandas as pd, warnings
from pathlib import Path
warnings.filterwarnings("ignore")

FAIR = 0.5           # only judge bladders that ran >=50% of their promised life
MIN_N = 8

raw = pd.read_csv("data/raw/Raw_Bladder_records.csv")
ext = pd.read_csv("data/clean/bladder_ext_clean.csv", parse_dates=["scrap_date"])
raw["co"] = pd.to_datetime(raw["checkoutdate"], dayfirst=True, errors="coerce")
scr = raw[raw["statusbladder"] == "ทิ้ง"].sort_values("co").groupby("Title").tail(1)
ext["machine"] = scr.set_index("Title")["Machine"].reindex(ext["bladder_id"]).values
ext = ext[(ext.bladder_life > 0) & ext.target_life.notna()].copy()
ext["ratio"] = ext.bladder_life / ext.target_life
n_total = len(ext)
fair = ext[ext.ratio >= FAIR].copy()

def size_of(name):
    import re
    m = re.search(r'(\d+)"', name); return (m.group(1)+'"') if m else "—"
fair["size"] = fair.part_name.apply(size_of)
fair["attr"] = np.where(fair.cause == "Leak", "them", np.where(fair.cause == "Deform", "us", "other"))

# ---- points for the promise-line scatter (fair-run set) ----
pts = [dict(t=float(r.target_life), l=float(r.bladder_life), r=round(float(r.ratio),3),
            p=r.part_name, sz=r.size, c=(r.cause if r.cause in ("Leak","Deform") else "other"),
            m=(r.machine if isinstance(r.machine,str) else None), a=r.attr)
       for _, r in fair.iterrows()]

# ---- machine proof: median life per machine for a part (>=4 units) ----
def machine_strip(part):
    s = fair[fair.part_name == part]; tgt = float(s.target_life.median())
    out = []
    for m, gm in s.groupby("machine"):
        if len(gm) < 3: continue
        out.append(dict(machine=m, n=int(len(gm)), med=float(gm.bladder_life.median()),
                        pct=round(gm.bladder_life.median()/tgt*100),
                        lives=[float(x) for x in gm.bladder_life]))
    out.sort(key=lambda d: d["med"])
    return dict(part=part, target=tgt, cause=s.cause.mode().iloc[0], machines=out)

proof_us = machine_strip('Bladder turnup 15"')   # deform, one machine drags it
proof_them = machine_strip('Bladder turnup 8"')  # leak, low on every machine

# ---- action board ----
def row_machine(part):
    s = fair[fair.part_name == part]; tgt = float(s.target_life.median())
    mm = s.groupby("machine").bladder_life.agg(n="size", med="median"); mm = mm[mm.n >= 4]
    worst, best = mm.med.idxmin(), mm.med.idxmax()
    cur, ceil = mm.loc[worst,"med"], mm.loc[best,"med"]
    below = int((s.bladder_life < tgt).sum())
    return dict(part=part, size=size_of(part), focus=f"press {worst}", cause=s.cause.mode().iloc[0],
        cur_pct=round(cur/tgt*100), ceil_pct=round(ceil/tgt*100), ceil_machine=best,
        uplift_pts=round((tgt-cur)/tgt*100) if cur<tgt else 0, n=int(mm.loc[worst,"n"]),
        below=below, side="us", solution="Standardise + fix the press")
def row_design(part, side, solution):
    s = fair[fair.part_name == part]; tgt = float(s.target_life.median())
    cur = float(s.bladder_life.median()); below = int((s.bladder_life < tgt).sum())
    return dict(part=part, size=size_of(part), focus=f'{size_of(part)} — every press', cause=s.cause.mode().iloc[0],
        cur_pct=round(cur/tgt*100), ceil_pct=100, ceil_machine=None,
        uplift_pts=round((tgt-cur)/tgt*100), n=len(s), below=below, side=side, solution=solution)

board = [
    row_machine('Bladder turnup 15"'),
    row_machine('Bladder turnup 23"'),
    row_design('Bladder turnup 21"', "us", "Standardise the human · PLC deflate-lock"),
    row_design('Bladder turnup 8"',  "them", "Redesign · France design loop"),
]

sample = (fair[["scrap_date","part_name","target_life","bladder_life","cause","machine"]]
          .dropna().sort_values("scrap_date").tail(7))
sample_rows = [[r.scrap_date.strftime("%Y-%m-%d"), r.part_name, int(r.target_life),
                int(r.bladder_life), r.cause, r.machine] for _, r in sample.iterrows()]

DATA = dict(
    meta=dict(n_total=n_total, n_fair=len(fair), excluded=n_total-len(fair),
              fair_pct=round(len(fair)/n_total*100), below=int((fair.ratio<1).sum()),
              leak_them=round(fair[fair.cause=="Leak"].shape[0]), unit_note="≥50% of promised life"),
    points=pts, sample=sample_rows, proof_us=proof_us, proof_them=proof_them, board=board)

Path("reports").mkdir(exist_ok=True)
Path("reports/journey_data.json").write_text(json.dumps(DATA, indent=1), encoding="utf-8")
TEMPLATE = Path("scripts/journey_template.html").read_text(encoding="utf-8")
Path("reports/evidence_journey.html").write_text(TEMPLATE.replace("/*__DATA__*/", json.dumps(DATA)), encoding="utf-8")
print(f"fair set {len(fair)}/{n_total}  board:")
for r in board: print(f"  {r['part']:<20} {r['cur_pct']}%->{r['ceil_pct']}%  [{r['side']}] {r['focus']}")
print("wrote reports/evidence_journey.html")

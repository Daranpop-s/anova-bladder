"""
Build the staged 'failure story' HTML — one dataset, escalating perspective.

Regenerates reports/failure_story.html from data/clean/bladder_ext_clean.csv.
Design contract (from the brief):
  - reuse the target-vs-life scatter across stages; change one variable per stage
  - constant color semantics: red=broke promise, green=kept, blue=leak, orange=deform
  - chart carries the shape; text beside it carries names + reasoning
  - median wherever money is claimed; print the caveats ourselves
"""
import json, numpy as np, pandas as pd, warnings
from pathlib import Path
warnings.filterwarnings("ignore")

UNIT_COST = 30000            # assumed THB / bladder — labelled as an assumption
MIN_N = 5

d = pd.read_csv("data/clean/bladder_ext_clean.csv", parse_dates=["install_date","scrap_date"])
raw_rows = 429
d = d[(d.bladder_life > 0) & d.target_life.notna()].copy()
d["ratio"] = d.bladder_life / d.target_life
d["waste"] = np.where(d.ratio < 1, 1 - d.ratio, 0.0)

# ---- per-part stats + group assignment ----
def stats(x):
    r = x.bladder_life / x.target_life
    return pd.Series(dict(
        n=len(x), target=float(x.target_life.median()), med=float(x.bladder_life.median()),
        medratio=float(r.median()), iqr=float(r.quantile(.75) - r.quantile(.25)),
        maxr=float(r.max()), leak=float((x.cause == "Leak").mean()),
        deform=float((x.cause == "Deform").mean()),
        broke=float((x.bladder_life < x.target_life).mean()),
        waste_thb=float(x.waste.sum() * UNIT_COST)))
g = d.groupby("part_name").apply(stats)
g = g[g.n >= MIN_N].reset_index()

def group_of(row):
    if row.medratio >= 1: return "G3"          # kept its promise
    return "G1" if row.iqr <= 0.6 else "G2"    # tight=characteristic / wide=out of control
g["group"] = g.apply(group_of, axis=1)
part_group = dict(zip(g.part_name, g.group))
d["group"] = d.part_name.map(part_group).fillna("other")

# dominant cause label per part
def dom(row):
    if row.leak >= row.deform and row.leak >= .5: return "leak"
    if row.deform > row.leak and row.deform >= .5: return "deform"
    return "mixed"
g["dom"] = g.apply(dom, axis=1)

# ---- money ----
fleet_waste_units = float(d.waste.sum())
fleet_headroom = fleet_waste_units * UNIT_COST
red_parts = g[g.medratio < 1].sort_values("medratio")
red_headroom = float(d[d.part_name.isin(red_parts.part_name)].waste.sum() * UNIT_COST)

# ---- point-level payload ----
pts = [dict(t=float(r.target_life), l=float(r.bladder_life), r=round(float(r.ratio), 3),
            p=r.part_name, c=(r.cause if r.cause in ("Leak", "Deform") else "other"),
            g=r.group, inst=(r.install_date.strftime("%Y-%m-%d") if pd.notna(r.install_date) else None))
       for _, r in d.iterrows()]

# a small, real sample table for Stage 1 (looks boring on purpose)
sample = (d[["scrap_date", "part_name", "target_life", "bladder_life", "cause"]]
          .dropna().sort_values("scrap_date").tail(8))
sample_rows = [[r.scrap_date.strftime("%Y-%m-%d"), r.part_name, int(r.target_life),
                int(r.bladder_life), r.cause] for _, r in sample.iterrows()]

parts_payload = []
for _, r in g.sort_values(["group", "medratio"]).iterrows():
    parts_payload.append(dict(name=r.part_name, n=int(r.n), target=int(r.target),
        med=int(r.med), medratio=round(r.medratio, 2), iqr=round(r.iqr, 2),
        maxr=round(r.maxr, 1), leak=round(r.leak, 2), deform=round(r.deform, 2),
        broke=round(r.broke, 2), group=r.group, dom=r.dom, waste_thb=int(r.waste_thb)))

DATA = dict(
    meta=dict(n=len(d), raw=raw_rows, kept=int((d.ratio >= 1).sum()),
              broke=int((d.ratio < 1).sum()), broke_pct=round((d.ratio < 1).mean()*100),
              tmin=int(d.target_life.min()), tmax=int(d.target_life.max()),
              maxratio=round(float(d.ratio.max()), 1), unit_cost=UNIT_COST,
              inst_min=d.install_date.min().strftime("%Y-%m-%d"),
              inst_max=d.install_date.max().strftime("%Y-%m-%d")),
    points=pts, parts=parts_payload, sample=sample_rows,
    money=dict(fleet=round(fleet_headroom), red=round(red_headroom),
               red_parts=[dict(name=r.part_name, thb=int(r.waste_thb), n=int(r.n))
                          for _, r in red_parts.iterrows()]),
)

Path("reports").mkdir(exist_ok=True)
Path("reports/story_data.json").write_text(json.dumps(DATA, indent=1), encoding="utf-8")

TEMPLATE = Path("scripts/story_template.html").read_text(encoding="utf-8")
HTML = TEMPLATE.replace("/*__DATA__*/", json.dumps(DATA))
Path("reports/failure_story.html").write_text(HTML, encoding="utf-8")
print(f"N={DATA['meta']['n']}  groups: G1/G2/G3  fleet headroom THB {fleet_headroom:,.0f}")
print("red parts:", list(red_parts.part_name))
print("wrote reports/failure_story.html")

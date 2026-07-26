"""
Position (C / AR / R) and Machine analysis — and conflict check vs prior findings.

The raw event log (Raw_Bladder_records.csv) adds two factors the Ext dataset
lacked: bladder POSITION (C=Center, AR=Anti-reference, R=Reference/on the bati
machine) and MACHINE id. Title in the raw log == bladder_id in the Ext clean
table (100% match), so we attach the real bladder_life (cycle count) to each
bladder's position/machine and run the same log-life ANOVA machinery.

Key question: does WHERE the bladder sits (position) or WHICH machine it runs on
affect life? If yes, that is a direct in-plant / operation signal (previously we
could only infer "operation" as a residual). We also check whether this conflicts
with the earlier conclusions (cause has no effect; type/part dominate; deform is
operation-driven).
"""

import warnings
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from pathlib import Path

warnings.filterwarnings("ignore")
REP = Path("reports"); REP.mkdir(exist_ok=True)
RAW = "data/raw/Raw_Bladder_records.csv"

raw = pd.read_csv(RAW)
ext = pd.read_csv("data/clean/bladder_ext_clean.csv")

# ---- per-bladder position/machine, taken at the SCRAP event when available ----
raw["checkout_dt"] = pd.to_datetime(raw["checkoutdate"], dayfirst=True, errors="coerce")
scrap = raw[raw["statusbladder"] == "ทิ้ง"].copy()      # ทิ้ง = scrapped
# last scrap event per Title
scrap = scrap.sort_values("checkout_dt").groupby("Title").tail(1)
scrap_attr = scrap.set_index("Title")[["position", "Machine", "Oldornew"]]

# modal (most common) position/machine across all events, as fallback
def modal(s):
    m = s.mode()
    return m.iloc[0] if len(m) else np.nan
modal_attr = raw.groupby("Title").agg(position=("position", modal),
                                       Machine=("Machine", modal),
                                       Oldornew=("Oldornew", modal))

pos = scrap_attr["position"].reindex(ext["bladder_id"]).values
mac = scrap_attr["Machine"].reindex(ext["bladder_id"]).values
oldnew = scrap_attr["Oldornew"].reindex(ext["bladder_id"]).values
# fallback to modal where scrap event missing
mpos = modal_attr["position"].reindex(ext["bladder_id"]).values
mmac = modal_attr["Machine"].reindex(ext["bladder_id"]).values
mon = modal_attr["Oldornew"].reindex(ext["bladder_id"]).values

d = ext.copy()
d["position"] = np.where(pd.isna(pos), mpos, pos)
d["machine"] = np.where(pd.isna(mac), mmac, mac)
d["oldnew"] = np.where(pd.isna(oldnew), mon, oldnew)
d["logL"] = np.log10(d["bladder_life"])

lines = []
def out(s=""):
    print(s); lines.append(s)

def eta_sq(groups):
    grand = np.concatenate(groups); gm = grand.mean()
    ssb = sum(len(g)*(g.mean()-gm)**2 for g in groups)
    sst = ((grand-gm)**2).sum()
    return ssb/sst

def screen(col, minn=8, resp="logL"):
    dd = d[[col, resp]].dropna()
    vc = dd[col].value_counts(); keep = vc[vc >= minn].index
    dd = dd[dd[col].isin(keep)]
    groups = [g[resp].values for _, g in dd.groupby(col)]
    if len(groups) < 2:
        out(f"  {col}: too few groups"); return None
    F, p = stats.f_oneway(*groups)
    H, ph = stats.kruskal(*groups)
    W, pl = stats.levene(*groups)
    e = eta_sq(groups)
    out(f"  {col:<10} k={len(groups):<3} N={len(dd):<4} eta2={e:5.3f}  "
        f"ANOVA p={p:.2e}  Kruskal p={ph:.2e}  Levene p={pl:.2e}")
    return e, p, ph

out("="*76)
out("POSITION (C/AR/R) & MACHINE  vs  BLADDER LIFE   +  conflict check")
out(f"N joined = {d['bladder_life'].notna().sum()} bladders "
    f"(position found {d['position'].notna().sum()}, machine {d['machine'].notna().sum()})")
out("="*76)

out("\nLife by POSITION (cycles):")
out(d.groupby("position")["bladder_life"].agg(n="size", mean="mean", median="median").round(0).to_string())

out("\n1) Single-factor screens on log-life:")
screen("position")
screen("machine", minn=10)
screen("oldnew")
# re-baseline the prior factors on this joined frame for apples-to-apples
screen("bladder_type")
screen("cause")

# ---- confound: is position tied to type/part? (Simpson risk) ----
out("\n2) Confound check — position vs bladder_type (counts):")
out(pd.crosstab(d["position"], d["bladder_type"]).to_string())
out("\n   position vs cause (counts):")
out(pd.crosstab(d["position"], d["cause"]).to_string())

# ---- position effect AFTER controlling for part (within-part) ----
out("\n3) Position effect WITHIN part (Type-II ANOVA  logL ~ C(part_code) + C(position)):")
m = d.dropna(subset=["position", "logL", "part_code"]).copy()
vc = m["part_code"].value_counts(); m = m[m["part_code"].isin(vc[vc >= 8].index)]
model = smf.ols("logL ~ C(part_code) + C(position)", data=m).fit()
aov = sm.stats.anova_lm(model, typ=2)
aov["eta_sq"] = aov["sum_sq"]/aov["sum_sq"].sum()
out(f"   N={len(m)}, adj-R2={model.rsquared_adj:.3f}")
out(aov.round(4).to_string())

# ---- machine effect within part ----
out("\n4) Machine effect WITHIN part (Type-II ANOVA  logL ~ C(part_code) + C(machine)):")
mm = d.dropna(subset=["machine", "logL", "part_code"]).copy()
vc = mm["machine"].value_counts(); mm = mm[mm["machine"].isin(vc[vc >= 10].index)]
vp = mm["part_code"].value_counts(); mm = mm[mm["part_code"].isin(vp[vp >= 8].index)]
model2 = smf.ols("logL ~ C(part_code) + C(machine)", data=mm).fit()
aov2 = sm.stats.anova_lm(model2, typ=2)
aov2["eta_sq"] = aov2["sum_sq"]/aov2["sum_sq"].sum()
out(f"   N={len(mm)}, adj-R2={model2.rsquared_adj:.3f}")
out(aov2.round(4).to_string())

(REP/"position_report.txt").write_text("\n".join(lines), encoding="utf-8")
out("\nReport written: reports/position_report.txt")

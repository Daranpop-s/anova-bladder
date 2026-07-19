"""
ANOVA / factor analysis of bladder life on the clean Ext dataset.

Response variable : bladder_life  (cycle count a bladder achieved before scrap)
Because life is strongly right-skewed, tests are run on log10(life) and
cross-checked with the non-parametric Kruskal-Wallis and Welch (unequal
variance) ANOVA.

Sections
  1. Main design factors : bladder_type, cause, part_code
  2. Installation-time / batch-defect analysis (install_quarter), including a
     within-part cohort test and a caveat about survivorship truncation.
  3. Multi-factor model  : does install period add signal beyond type + cause?
Figures written to reports/.
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
REP = Path("reports")
REP.mkdir(exist_ok=True)

df = pd.read_csv("data/clean/bladder_ext_clean.csv", parse_dates=["scrap_date", "install_date"])
df["log_life"] = np.log10(df["bladder_life"])

lines = []
def out(s=""):
    print(s)
    lines.append(s)


def eta_sq(groups):
    grand = np.concatenate(groups); gm = grand.mean()
    ssb = sum(len(g) * (g.mean() - gm) ** 2 for g in groups)
    sst = ((grand - gm) ** 2).sum()
    return ssb / sst


def welch_anova(groups):
    k = len(groups)
    n = np.array([len(g) for g in groups]); m = np.array([g.mean() for g in groups])
    v = np.array([g.var(ddof=1) for g in groups]); w = n / v
    xbar = (w * m).sum() / w.sum()
    num = (w * (m - xbar) ** 2).sum() / (k - 1)
    den = 1 + (2 * (k - 2) / (k ** 2 - 1)) * (((1 - w / w.sum()) ** 2 / (n - 1)).sum())
    F = num / den
    dfd = (k ** 2 - 1) / (3 * (((1 - w / w.sum()) ** 2 / (n - 1)).sum()))
    p = stats.f.sf(F, k - 1, dfd)
    return F, p


def screen(factor, resp="log_life", min_n=5, label=None):
    d = df[[factor, resp]].dropna()
    vc = d[factor].value_counts()
    keep = vc[vc >= min_n].index
    d = d[d[factor].isin(keep)]
    groups = [g[resp].values for _, g in d.groupby(factor)]
    if len(groups) < 2:
        out(f"  {factor}: too few groups"); return
    F, p = stats.f_oneway(*groups)
    Fw, pw = welch_anova(groups)
    H, ph = stats.kruskal(*groups)
    W, pl = stats.levene(*groups)  # homogeneity of variance
    eta = eta_sq(groups)
    out(f"  {label or factor:<16} k={len(groups):<3} N={len(d):<4} "
        f"eta2={eta:5.3f}  ANOVA p={p:.2e}  Welch p={pw:.2e}  Kruskal p={ph:.2e}"
        f"  Levene p={pl:.2e}")


out("=" * 78)
out("BLADDER LIFE — ANOVA / FACTOR ANALYSIS")
out(f"N = {len(df)} scrapped bladders | response = bladder_life (tested on log10)")
out("=" * 78)
out("\nResponse distribution (bladder_life):")
out(df["bladder_life"].describe().round(0).to_string())
out(f"  skewness (raw)   = {stats.skew(df['bladder_life']):.2f}")
out(f"  skewness (log10) = {stats.skew(df['log_life']):.2f}  <- log makes it ~symmetric")

# ----------------------------------------------------------------- 1) factors
out("\n" + "-" * 78)
out("1) MAIN DESIGN FACTORS  (single-factor screens on log10 life)")
out("-" * 78)
screen("bladder_type")
screen("cause")
screen("part_code")

out("\nMean bladder_life by type:")
out(df.groupby("bladder_type")["bladder_life"]
      .agg(n="size", mean="mean", median="median").round(0)
      .sort_values("median").to_string())

out("\nTukey HSD (log10 life) between bladder types:")
tk = pairwise_tukeyhsd(df["log_life"], df["bladder_type"])
out(str(tk))

# ----------------------------------------------------- 2) installation timing
out("\n" + "-" * 78)
out("2) INSTALLATION-TIME / BATCH-DEFECT ANALYSIS")
out("-" * 78)
out("Hypothesis: bladders from a bad production/install lot fail early together,")
out("so life should vary by install period.")
out("")
out("*** CAVEAT — survivorship truncation: the dataset only contains bladders")
out("already SCRAPPED. Units installed recently that are still running are")
out("absent, so recent install cohorts are biased toward short life. Read the")
out("recent quarters with that in mind. ***")
out("")

qtab = (df.dropna(subset=["install_quarter"])
          .groupby("install_quarter")["bladder_life"]
          .agg(n="size", mean="mean", median="median").round(0))
out("Life by install quarter:")
out(qtab.to_string())

screen("install_quarter", label="install_quarter")

# Overall trend: correlation of install time vs life (Spearman, rank-based)
d = df.dropna(subset=["install_date"])
rho, prho = stats.spearmanr(d["install_date"].astype("int64"), d["bladder_life"])
out(f"\nSpearman(install_date, life) = {rho:+.3f}  p={prho:.2e} "
    "(negative is expected purely from truncation)")

# Within-part cohort test: for each part with enough spread of install
# quarters, does install_quarter explain life? This isolates a batch effect
# from the part/type mix.
out("\nWithin-part batch test  (ANOVA of log-life across install quarters,")
out("per part, using quarters with >=3 units and parts with >=2 such quarters):")
out(f"  {'part_code':<10}{'type':<8}{'#qtr':>5}{'N':>5}{'ANOVA p':>12}{'eta2':>8}")
any_sig = False
for pc, g in df.dropna(subset=["install_quarter"]).groupby("part_code"):
    qc = g["install_quarter"].value_counts()
    qk = qc[qc >= 3].index
    gg = g[g["install_quarter"].isin(qk)]
    if gg["install_quarter"].nunique() < 2:
        continue
    grp = [x["log_life"].values for _, x in gg.groupby("install_quarter")]
    F, p = stats.f_oneway(*grp)
    eta = eta_sq(grp)
    flag = " *" if p < 0.05 else ""
    any_sig = any_sig or p < 0.05
    out(f"  {pc:<10}{g['bladder_type'].iloc[0]:<8}"
        f"{gg['install_quarter'].nunique():>5}{len(gg):>5}{p:>12.2e}{eta:>8.3f}{flag}")
out("  (* = install quarter significantly affects life within that part, p<0.05)")
if not any_sig:
    out("  -> No part shows a significant install-quarter effect: no evidence of")
    out("     a bad-lot batch effect once part identity is held fixed.")

# ------------------------------------------------ 3) multi-factor ANOVA model
out("\n" + "-" * 78)
out("3) MULTI-FACTOR ANOVA  (Type-II)  log_life ~ type + cause + install_quarter")
out("-" * 78)
m = df.dropna(subset=["bladder_type", "cause", "install_quarter", "log_life"]).copy()
# keep only well-populated levels so the model is estimable
for col in ["cause", "install_quarter"]:
    vc = m[col].value_counts()
    m = m[m[col].isin(vc[vc >= 5].index)]
model = smf.ols("log_life ~ C(bladder_type) + C(cause) + C(install_quarter)", data=m).fit()
aov = sm.stats.anova_lm(model, typ=2)
aov["eta_sq"] = aov["sum_sq"] / aov["sum_sq"].sum()
out(f"N used = {len(m)},  model adj-R^2 = {model.rsquared_adj:.3f}")
out(aov.round(4).to_string())
out("\nInterpretation: compare each factor's PR(>F). A large, significant")
out("bladder_type with a non-significant install_quarter means WHAT the bladder")
out("is drives life, not WHEN it was installed.")

# --------------------------------------------------------------- figures
fig, ax = plt.subplots(1, 2, figsize=(13, 5))
order = df.groupby("bladder_type")["bladder_life"].median().sort_values().index
data = [df[df["bladder_type"] == t]["bladder_life"] for t in order]
ax[0].boxplot(data, tick_labels=list(order), showfliers=False)
ax[0].set_yscale("log"); ax[0].set_ylabel("Bladder life (cycles, log)")
ax[0].set_title("Life by bladder type")
for t in order:
    s = df[df["bladder_type"] == t].dropna(subset=["install_date"])
    ax[1].scatter(s["install_date"], s["bladder_life"], s=14, alpha=0.5, label=t)
ax[1].set_yscale("log"); ax[1].set_xlabel("Install date"); ax[1].set_title("Life vs install date")
ax[1].legend(); fig.autofmt_xdate()
fig.tight_layout(); fig.savefig(REP / "life_factors.png", dpi=110)
out(f"\nFigure written: reports/life_factors.png")

(REP / "anova_report.txt").write_text("\n".join(lines), encoding="utf-8")
print("\nReport written: reports/anova_report.txt")

"""
Manufacturer-vs-operation variance decomposition of bladder life.

Reproduces (and checks) the nested analysis:
  - variance of log-life split into  part (design) / lot-within-part (batch) /
    within-lot residual (operation)  -- overall and split BY CAUSE
  - within-part install-lot effect (Kruskal-Wallis, epsilon^2)
  - two clocks: premature clustering by INSTALL quarter vs REMOVAL quarter
  - effect sizes for Life ~ part / install_q / removal_q

"Lot" is proxied by install quarter (no true lot id exists). "Operation" is
the within-lot residual, so it also absorbs random noise -> upper bound.
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
REP = Path("reports"); REP.mkdir(exist_ok=True)

d = pd.read_csv("data/clean/bladder_ext_clean.csv",
                parse_dates=["scrap_date", "install_date"])
d = d[d["bladder_life"] > 0].copy()
d["logL"] = np.log(d["bladder_life"])
d["install_q"] = d["install_date"].dt.to_period("Q").astype(str)
d["removal_q"] = d["scrap_date"].dt.to_period("Q").astype(str)
d = d.rename(columns={"part_code": "part"})

lines = []
def out(s=""):
    print(s); lines.append(s)


def kw_eps2(groups):
    """Kruskal-Wallis H, p and epsilon^2 effect size."""
    groups = [g for g in groups if len(g) >= 1]
    N = sum(len(g) for g in groups); k = len(groups)
    if k < 2:
        return np.nan, np.nan, np.nan
    H, p = stats.kruskal(*groups)
    eps2 = (H - k + 1) / (N - k) if N > k else np.nan
    return H, p, eps2


def nested_varcomp(sub, label):
    """Unbalanced two-level nested-random-model variance components of logL
    (Searle ANOVA estimator):  A = part (design), B(A) = lot within part
    (batch), E = within-lot residual (operation).  Negative estimates -> 0."""
    sub = sub.dropna(subset=["install_q"]).copy()
    y = sub["logL"].values
    grand = y.mean()
    a = sub["part"].nunique()

    SSA = SSB = SSE = 0.0
    sum_b = 0                      # total #lots across parts
    T1 = 0.0                       # Σ_i Σ_j n_ij^2 / n_i.
    Tn2 = 0.0                      # Σ_i Σ_j n_ij^2
    Ti2 = 0.0                      # Σ_i n_i.^2
    N = len(sub)
    for _, gi in sub.groupby("part"):
        ni = len(gi); mi = gi["logL"].mean()
        SSA += ni * (mi - grand) ** 2
        Ti2 += ni ** 2
        lots = gi.groupby("install_q")
        sum_b += lots.ngroups
        s_nij2 = 0.0
        for _, gij in lots:
            nij = len(gij); mij = gij["logL"].mean()
            SSB += nij * (mij - mi) ** 2
            SSE += ((gij["logL"].values - mij) ** 2).sum()
            s_nij2 += nij ** 2
            Tn2 += nij ** 2
        T1 += s_nij2 / ni

    df_A, df_B, df_E = a - 1, sum_b - a, N - sum_b
    MSA = SSA / df_A if df_A > 0 else np.nan
    MSB = SSB / df_B if df_B > 0 else np.nan
    MSE = SSE / df_E if df_E > 0 else np.nan

    k1 = (N - T1) / df_B if df_B > 0 else np.nan
    k2 = (T1 - Tn2 / N) / df_A if df_A > 0 else np.nan
    k3 = (N - Ti2 / N) / df_A if df_A > 0 else np.nan

    s2_e = MSE
    s2_b = max((MSB - MSE) / k1, 0.0)
    s2_a = max((MSA - MSE - k2 * s2_b) / k3, 0.0)
    tot = s2_a + s2_b + s2_e
    out(f"\n[{label}]  N={N}  parts={a}  lots={sum_b}")
    out(f"  part (design)          : {s2_a/tot*100:5.1f}%  -> manufacturer (design)")
    out(f"  lot within part (batch): {s2_b/tot*100:5.1f}%  -> manufacturer (production)")
    out(f"  within-lot residual    : {s2_e/tot*100:5.1f}%  -> operation + noise")
    out(f"  => manufacturer-linked : {(s2_a+s2_b)/tot*100:5.1f}%   "
        f"operation-linked : {s2_e/tot*100:5.1f}%")
    return dict(part=s2_a/tot, lot=s2_b/tot, resid=s2_e/tot)


out("=" * 78)
out("MANUFACTURER vs OPERATION — nested variance decomposition of log(life)")
out(f"N = {len(d)} bladders with valid life")
out("=" * 78)

out("\n" + "-" * 78)
out("1) OVERALL and BY CAUSE")
out("-" * 78)
nested_varcomp(d, "ALL causes")
for cause in ["Leak", "Deform"]:
    sub = d[d["cause"] == cause]
    if sub["part"].nunique() >= 2:
        nested_varcomp(sub, cause)

out("\n" + "-" * 78)
out("2) INSTALL-LOT EFFECT WITHIN EACH PART  (Kruskal-Wallis, eps^2)")
out("-" * 78)
out(f"  {'part':<10}{'type':<8}{'#lot':>5}{'N':>5}{'eps^2':>8}{'p':>12}   read")
for p, g in d.groupby("part"):
    qc = g["install_q"].value_counts()
    qk = qc[qc >= 4].index
    gg = g[g["install_q"].isin(qk)]
    if gg["install_q"].nunique() < 2:
        continue
    grp = [x["bladder_life"].values for _, x in gg.groupby("install_q")]
    H, pv, e2 = kw_eps2(grp)
    read = "BATCH signal" if pv < 0.05 else "no batch signal"
    out(f"  {p:<10}{g['bladder_type'].iloc[0]:<8}{gg['install_q'].nunique():>5}"
        f"{len(gg):>5}{e2:>8.3f}{pv:>12.3g}   {read}")

out("\n" + "-" * 78)
out("3) TWO CLOCKS — premature clustering by INSTALL vs REMOVAL quarter")
out("-" * 78)
# premature = life below half the part's own median (target is unreliable)
med = d.groupby("part")["bladder_life"].transform("median")
d["prem"] = d["bladder_life"] < 0.5 * med
out(f"premature units (life < 0.5 x part median): {d['prem'].sum()} / {len(d)} "
    f"({d['prem'].mean()*100:.0f}%)")
for clock in ["install_q", "removal_q"]:
    ct = pd.crosstab(d[clock], d["prem"])
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    out(f"  {clock:<10}: chi2={chi2:5.1f}  dof={dof}  p={p:.3g}")

out("\nPremature rate by REMOVAL quarter:")
rr = d.groupby("removal_q")["prem"].agg(n="size", prem_rate="mean")
rr["prem_rate"] = (rr["prem_rate"] * 100).round(0)
out(rr.to_string())

out("\n" + "-" * 78)
out("4) EFFECT SIZES  Life ~ single factor  (Kruskal-Wallis eps^2)")
out("-" * 78)
for f in ["part", "install_q", "removal_q", "cause", "bladder_type"]:
    g = d.dropna(subset=[f])
    grp = [x["bladder_life"].values for _, x in g.groupby(f) if len(x) >= 4]
    H, pv, e2 = kw_eps2(grp)
    out(f"  Life ~ {f:<12} eps^2={e2:6.3f}  p={pv:.3g}  (k={len(grp)})")

(REP / "variance_components_report.txt").write_text("\n".join(lines), encoding="utf-8")
out("\nReport written: reports/variance_components_report.txt")

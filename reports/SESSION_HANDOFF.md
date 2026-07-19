# Bladder Life — Root-Cause Analysis: Session Handoff

Self-contained summary of data, method, findings, and caveats so another chat
can continue without re-deriving anything.

---

## 1. Objective

Answer: **why do curing bladders fail before their target life — is it the
manufacturer (design + delivered batch) or us (in-plant operation)?** And test
whether **installation time** points to bad production lots.

---

## 2. Data inventory (what we were given)

Six raw files. Only two carry real analytical signal; three are report
filter-lists; one is a different system.

| Raw file | Rows | What it actually is | Used? |
|----------|------|---------------------|-------|
| `data_5_bladder_records.xlsx` | 433 | Per-bladder scrap records (date, part, cause, target, life) | Superseded by Ext |
| **`Ext_Bladder_dataset.csv`** | 429 | **Definitive** clean-ish per-bladder records: coded parts + `Diagnose` | **YES — primary** |
| `data_4_summary.xlsx` | 28 | Pivot summary per part (avg/min/max life, scrap counts) | Reference only |
| `data_2_machine_log.xlsx` | 5087 | Machine breakdown/repair log — different system (tire machines) | Tangential |
| `data_3_month_list.xlsx` | 63 | Just a list of month labels (Jan-22…Dec-26) | No — filter list |
| `data_6_day_list.xlsx` | 34 | Just a list of day numbers 1–31 | No — filter list |

**Primary dataset = `Ext_Bladder_dataset.csv` → cleaned to 417 usable rows.**

---

## 3. Cleaning steps (script: `scripts/clean_ext.py` → `data/clean/bladder_ext_clean.csv`)

1. Dropped 3 junk `Unnamed:` columns and the trailing blank/`Applied filters:` footer row.
2. Dropped 11 rows with no `Bladder Life` (the response variable). **429 → 417.**
3. Renamed columns to snake_case; parsed `scrap_date` (mixed text date formats).
4. **Bladder type** decoded from the part-code prefix: `B-TU`=Turnup, `B-MT`=MTG, `B-PU`=Push.
5. **Cause** normalized Thai→English: Leak, Deform, Tear, Burn out, Flabby, Bad material, Quality issue.
6. **Installation date** extracted from the `Bladder name` field (format `<install-date>_<id>`,
   e.g. `12/4/2024_02540`). `LastDate` = scrap date; the name holds the install date.
   - Date formats are **mixed in the same file**: 173 clearly month-first (M/D/Y),
     81 clearly day-first (D/M/Y), 153 ambiguous, 15 named-month.
   - Ambiguous cases default to **month-first**, flagged in `install_date_ambiguous`.
   - **Correction pass**: if month-first put install *after* scrap (impossible) or in
     the future, flip to day-first. 11 rows corrected; 0 rows left with install > scrap.
7. `reached_target = bladder_life >= target_life`.

### Critical data note — `Diagnose` is NOT an independent factor
`Diagnose` (Pass/Abnormal) is **exactly** `bladder_life >= target_life` (verified:
Pass↔reached 219/219, Abnormal↔missed 198/198). It is a restatement of the
response, so **it must never be used as a predictor** (circular). Kept for
reference only.

---

## 4. Response variable & why we log-transform

`bladder_life` = cycle count before scrap. Strongly right-skewed
(skew ≈ 2.68). `log10(life)` skew ≈ 0.02 (≈ symmetric). Distribution is
Weibull-like with shape **β ≈ 1**. Therefore:
- All ANOVA runs on **log-life**, cross-checked with **Welch** (unequal variance)
  and non-parametric **Kruskal–Wallis**.
- Always report **effect size** (η² for ANOVA, ε² for KW), not just p — with
  N ≈ 417 almost everything is "significant."

Response summary: median 584, mean 1187, min 15, max 11,220 cycles.
**47% of scrapped units never reached target** (53% reached).

---

## 5. Methods used

1. **One-way screens** on log-life for each factor (ANOVA + Welch + Kruskal + Levene).
2. **Tukey HSD** post-hoc between bladder types.
3. **Nested variance decomposition (manufacturer vs operation)** — the core method:
   - Model: `logL = part (design) + lot-within-part (batch) + within-lot residual (operation)`.
   - Estimated with the **Searle unbalanced two-level nested-ANOVA variance-component
     estimator** (proper variance components, not SS shares — see pitfall below).
   - Run **overall and separately by cause** (Leak, Deform).
4. **Within-part batch test**: Kruskal–Wallis of life across install lots (quarters),
   per part — isolates a delivered-batch effect from the part/type mix.
5. **Two-clock test**: premature-rate clustering by **install quarter** vs
   **removal quarter** (χ² on `premature = life < 0.5 × part-median`).
6. **Multi-factor Type-II ANOVA**: `logL ~ type + cause + install_quarter`.

### Method pitfall we corrected
A sum-of-squares *share* gives the lot term one dummy per lot (~128 lots), so it
absorbs SS that is really sampling noise → **overstates the batch component**
(gave lot ≈ 20–33%). The proper **variance-component estimator** shrinks it to
≈ 6%. Use variance components, not SS shares, for the manufacturer/operation split.

---

## 6. FINDINGS

### 6.1 What drives life (single-factor, log-life, KW ε²)
| Factor | ε² / η² | p | Verdict |
|--------|---------|---|---------|
| Part number | 0.41 | 6e-29 | **Strongest** (finest grouping) |
| Bladder type | 0.11–0.12 | 1e-10 | **Strong** |
| Reached-target flag | 0.26 (η²) | 2e-29 | (degenerate — it's the response) |
| Install quarter | 0.011 | 0.14 | **Not significant** |
| **Removal quarter** | **0.072** | **1e-5** | **Significant** |
| Failure cause | ≈ 0 | 0.50 | **No effect on life** |

- **Push** bladders far outlive others: median ≈ 3,437 cycles vs **MTG ≈ 492**,
  **Turnup ≈ 535**. Tukey: Push ≠ (MTG, Turnup); MTG ≈ Turnup.
- **Failure cause does not explain lifetime** (bladders don't live longer/shorter by *how* they die).

### 6.2 Manufacturer vs Operation (nested variance components, log-life)
| Split | Part (design) | Batch (lot) | Within-lot (operation) | → Manufacturer / Us |
|-------|--------------|-------------|------------------------|---------------------|
| **Overall** | 40% | **6%** | 54% | **~46% / ~54%** |
| **Leak** (62% of failures) | 59% | 13% | 28% | **~72% manufacturer** |
| **Deform** (31% of failures) | 11% | 9% | 80% | **~80% operation** |

**Headline: it's both, and it separates by failure mode.**
- **Leaks → manufacturer** (design + quality). Largest failure mode.
- **Deform → us** (operation): same delivery, very different outcomes = handling/process.
- Pooled, the two cancel — so **never report a single "cause"; split by mode**.

> Note: the doc handed in earlier claimed **42/20/38 → 60% manufacturer**. Reproduced
> here as **40/6/54 → ~46% manufacturer** using proper variance components. The 20%
> batch figure was an SS-share artifact. Direction identical; batch share corrected down.

### 6.3 Batch (bad-lot) signal — only 2 parts (install-lot KW, ε²)
| Part | ε² | p | Read |
|------|----|----|------|
| **B-TU-004** | 0.34 | 0.009 | **Real batch effect** |
| **B-TU-007** | 0.20 | 0.02 | **Real batch effect** |
| B-MT-006, B-TU-001/005/009/012 | ≈ 0 | n.s. | No batch signal |

**Only B-TU-004 and B-TU-007 are legitimate supplier bad-batch / warranty cases.**
For all other parts, variation is *within* every delivery → not a batch problem.

### 6.4 Two clocks — the decisive result
- **Install quarter**: premature failures **not** clustered (χ²=11.2, p=0.35). →
  *Not* a bad manufacturing/delivery window.
- **Removal quarter**: premature failures **strongly clustered** (χ²=22.7, p=0.004),
  peaking **2024 Q3 at 50% premature** (baseline ~12–15%). → A **plant-side event**
  (machine / process / consumable) at that time, regardless of when units were installed.

**Interpretation:** failures line up with *when they died in our plant*, not *when
they were made* → operation signature. **Best single lead: pull maintenance /
machine / process logs for 2024 Q3.**

---

## 7. Caveats (state these in any meeting)
1. **"Operation" = residual** after part + batch, so it also carries random noise →
   treat the ~54% as an **upper bound**.
2. **No true lot number or machine ID** in the data. "Lot" is proxied by install
   quarter. Cannot yet firmly separate "a bad machine" from "a bad batch."
3. **Survivorship / right-truncation**: dataset holds only *already-scrapped* units.
   Recently-installed units still running are absent → recent install cohorts look
   short-lived. The 2024 Q3 removal spike needs a **maturation-bias check** before it's
   claimed as a hard event (verify it's not a window edge).
4. **Target is an internal guess**; "premature" here uses each part's own median, not target.
5. Exact percentages are **soft**; the **direction** of every finding is solid.

---

## 8. Recommendations
**Manufacturer half:** supplier-quality review on leak-dominant parts; file lot
claims on **B-TU-004 & B-TU-007 only**; tighten with serial adjacency.
**Our half:** PLC air-purge interlock + handling SOP (kills deform); **trace the
2024 Q3 spike**; start logging **true lot numbers + machine/press ID** (turns the
next analysis from inference into proof, enables a proper survival model).

---

## 9. Method references (for credibility)
- ANOVA Method for Variance-Component Decomposition & Diagnosis in Batch Manufacturing
  Processes — *Flexible Services & Manufacturing Journal* (Springer).
  https://link.springer.com/article/10.1023/A:1024457408540
- Variance Component Calculations: Common Methods & Misapplications — *Quality
  Engineering* (Taylor & Francis). https://www.tandfonline.com/doi/full/10.1081/QEN-120003564
- Weibull Reliability Analysis (censored life data) — F. Scholz, Univ. of Washington.
  https://faculty.washington.edu/fscholz/Reports/weibullanalysis.pdf
- How to Perform Nested ANOVA (supplier/batch) — Lean Six Sigma Hub.
  https://lean6sigmahub.com/how-to-perform-nested-anova-a-complete-guide-with-real-world-examples/

---

## 10. Repository map & reproduce
```
data/raw/                       # the 6 source files
data/clean/bladder_ext_clean.csv   # PRIMARY analysis table (417 rows)
data/clean/bladder_records_clean.csv, part_summary_clean.csv, machine_log_clean.csv
scripts/clean_ext.py            # clean Ext dataset (+ install-date parsing)
scripts/clean_data.py           # clean the earlier data_2/4/5 files
scripts/analyze_lifetime.py     # one-way ANOVA, Tukey, install-time, multi-factor
scripts/variance_components.py  # nested manufacturer-vs-operation decomposition
reports/anova_report.txt, variance_components_report.txt, life_factors.png
reports/manager_briefing.html   # one-page boardroom visual
```
Reproduce:
```bash
pip install pandas openpyxl scipy statsmodels matplotlib
python3 scripts/clean_ext.py
python3 scripts/analyze_lifetime.py
python3 scripts/variance_components.py
```

## 11. Git / environment state
- Branch: `claude/anova-test-3ikcqe`. All work **committed locally**.
- **Push blocked**: 403 egress-policy denial on git write (reads work). Not retryable
  per proxy rules — needs write access granted to the session.
- Commits show "Unverified" (no GPG signing key in env); author is correct
  (`Claude <noreply@anthropic.com>`). Cosmetic only.

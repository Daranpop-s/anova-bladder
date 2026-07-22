# Bladder-Life ANOVA — Detailed Methods & Derivation Report

Reproducibility-level documentation: every transform, test, formula, threshold,
and the exact reasoning chain from the data to each conclusion. Someone with the
raw file and this report can reproduce every number — or improve on the method
using §12.

Dataset: `Ext_Bladder_dataset.csv` → cleaned to **N = 417** scrapped bladders.
Scripts: `scripts/clean_ext.py`, `scripts/analyze_lifetime.py`,
`scripts/variance_components.py`. Stack: pandas, scipy, statsmodels.

---

## 0. Conclusions up front (each links to the section that proves it)

| # | Conclusion | Proof |
|---|-----------|-------|
| C1 | **What a bladder *is* (part/type) drives life; how it *fails* (cause) does not.** | §4, §6, §9 |
| C2 | **Push ≫ MTG ≈ Turnup** (median 3,437 vs 492/535 cycles). | §4, §5 |
| C3 | **Blame splits by failure mode:** Leak ≈ 72% manufacturer, Deform ≈ 80% operation. | §6 |
| C4 | **Overall ≈ 46% manufacturer / 54% operation** (not the 60/40 claimed earlier — see §6.3 pitfall). | §6 |
| C5 | **Only B-TU-004 and B-TU-007 carry a real bad-batch signal.** | §7 |
| C6 | **Failures cluster by *removal* time (2024Q3, 50% premature), not *install* time** → plant event, not bad delivery. | §8 |

---

## 1. Data preparation (exact, from `clean_ext.py`)

Starting rows: 429. Steps and row accounting:

1. Drop 3 empty `Unnamed:` columns.
2. Drop trailing footer row where `LastDate` is blank (the `Applied filters:` line). → 428.
3. Drop 11 rows with missing `Bladder Life` (the response cannot be null). → **417**.

Column derivations:
- `scrap_date` ← `LastDate`, parsed with `format="mixed"`.
- `bladder_life` ← `Bladder Life` (numeric, cycle count). **Response variable.**
- `target_life` ← `Target`.
- `bladder_type` ← first 4 chars of `part_code`: `B-TU`→Turnup, `B-MT`→MTG, `B-PU`→Push.
- `cause` ← Thai→English map (Leak, Deform, Tear, Burn out, Flabby, Bad material, Quality issue).
- `install_date` ← parsed from the `Bladder name` field, which is `"<install-date>_<id>"`.
- `install_quarter`, `install_ym`, `removal_q` (= scrap-date quarter) ← period floors.

### 1.1 Installation-date parsing (the one genuinely messy field)
`Bladder name` example: `12/4/2024_02540`. Split on `_`, take token 0.
Formats present (counts): month-first M/D/Y = 173, day-first D/M/Y = 81,
ambiguous (both ≤12) = 153, named-month ("December 16, 2024") = 15.
- Unambiguous numeric: if first field >12 → day-first; if second >12 → month-first.
- Ambiguous (both ≤12): **default month-first**, and set `install_date_ambiguous=True`.
- **Validation/repair pass:** an install date cannot be after the scrap date or in
  the future. For flagged-ambiguous rows violating that, re-parse day-first; keep the
  swap only if it yields install ≤ scrap and ≤ today. **11 rows repaired; 0 rows left
  with install > scrap.** This is why the parsing is trustworthy enough for
  quarter-level cohorts (day-within-quarter error doesn't move the quarter bin except
  at boundaries, and the repair catches the boundary cases).

### 1.2 A trap we defused — `Diagnose` is not a factor
`Diagnose` ∈ {Pass, Abnormal} equals **exactly** `bladder_life ≥ target_life`
(cross-tab: Pass↔reached 219/219; Abnormal↔missed 198/198; zero off-diagonal). It is
a coarsened copy of the response. **Using it as a predictor would be circular**, so it
is excluded from every model. (This is the single most important "don't" here.)

---

## 2. Response variable and why we model log-life

`bladder_life` summary: mean 1187, median 584, min 15, max 11,220, SD 1501.
- **Raw skewness = 2.68** (heavy right tail) → violates ANOVA's normality/equal-variance
  assumptions; a few long-lived Push units would dominate sums of squares.
- **log10(life) skewness = 0.02** (≈ symmetric).
- The life distribution is Weibull-like with shape **β ≈ 1** (near-exponential).

**Rule adopted:** run parametric tests (ANOVA, Welch, Tukey, variance components) on
**log-life**, and confirm each with the **non-parametric Kruskal–Wallis** on raw life.
If parametric and non-parametric agree, the conclusion is not an artifact of the
transform. They agree everywhere here.

---

## 3. The statistical toolbox (what each test is, and why it's used)

| Test | Question it answers | Why here |
|------|--------------------|----------|
| **One-way ANOVA** (F) on log-life | Do group means differ? | Primary screen per factor |
| **Welch ANOVA** | Same, without assuming equal variances | Levene often significant (unequal spread) |
| **Kruskal–Wallis** (H) on raw life | Do group distributions differ? (rank-based) | Transform-free confirmation |
| **Levene** | Are group variances equal? | Tells us whether to trust classic F vs Welch |
| **Tukey HSD** | *Which* groups differ, family-wise controlled | Post-hoc after a significant type effect |
| **Nested variance components** (Searle) | *How is the variance split* across design/batch/operation? | The manufacturer-vs-us question |
| **χ² contingency** | Is a binary outcome (premature) associated with a time bucket? | Two-clock test |
| **Effect size** η² (ANOVA) / ε² (KW) | Does the factor *matter*, beyond being significant? | With N≈417 p-values are almost always tiny |

**Effect-size formulas used**
- η² = SS_between / SS_total.
- ε² (Kruskal–Wallis) = (H − k + 1) / (N − k), where k = #groups, N = total.
- Interpretation guide: ε²/η² ≈ 0.01 small, 0.06 medium, 0.14 large.

Significance threshold α = 0.05 throughout. Effect size is weighted **more heavily
than p** in every conclusion.

---

## 4. Analysis 1 — single-factor screens (log-life)

`screen()` keeps only levels with n ≥ 5, then runs all four tests.

| Factor | k | N | η²/ε² | ANOVA p | Welch p | Kruskal p | Levene p |
|--------|---|---|-------|---------|---------|-----------|----------|
| bladder_type | 3 | 417 | 0.120 | 3.1e-12 | 1.1e-10 | 1.3e-10 | 0.013 |
| **cause** | 4 | 408 | **0.010** | **0.252** | **0.270** | **0.501** | 0.469 |
| part_code | 15 | 394 | 0.392 | 3.5e-33 | 3.7e-29 | 8.0e-29 | 4.3e-08 |

Mean/median life by type (cycles): MTG 890/492 · Turnup 1039/535 · **Push 3313/3437**.

**How this yields C1 and C2:**
- `cause` is non-significant on *all four* tests and its effect size is ~0.01 (negligible).
  → **failure mode does not explain how long a bladder lived** (C1, negative half).
- `part_code` (ε²=0.39) and `bladder_type` (ε²=0.12) are the large, robust effects.
  → **identity of the bladder is the driver** (C1, positive half). Push is the outlier
  (C2), confirmed formally in §5.
- Levene significant for type/part → we do **not** rely on classic F alone; Welch and
  Kruskal agree, so the conclusion stands under unequal variance.

---

## 5. Analysis 2 — Tukey HSD (which types differ)

On log10-life, FWER = 0.05:

| Pair | mean diff (log10) | p-adj | Reject H₀? |
|------|-------------------|-------|-----------|
| MTG vs Push | +0.662 | 0.000 | **Yes** |
| MTG vs Turnup | +0.046 | 0.718 | No |
| Push vs Turnup | −0.617 | 0.000 | **Yes** |

meandiff 0.66 in log10 ≈ **10^0.66 ≈ 4.6× longer life for Push**. MTG and Turnup are
statistically indistinguishable. → **C2 proven**: the type effect is entirely "Push vs
the rest," not a smooth gradient.

---

## 6. Analysis 3 — nested variance decomposition (manufacturer vs operation)

**The central method.** Model log-life as a two-level *nested random* structure:

```
logL_ijk = μ + A_i + B_ij + e_ijk
   A_i   = part i              (design)      → manufacturer
   B_ij  = install-lot j in part i (batch)   → manufacturer (production)
   e_ijk = within-lot residual               → operation + random noise
```

Variance components σ²_A, σ²_B, σ²_e are estimated with the **Searle unbalanced
two-fold nested ANOVA estimator** (method of moments), because the design is highly
unbalanced (parts have very different lot counts and sizes).

### 6.1 The estimator (exact formulas in `variance_components.py`)
Sums of squares (a = #parts; for part i: n_i obs, b_i lots; lot ij has n_ij obs; N total):
```
SSA = Σ_i n_i (ȳ_i.. − ȳ...)²                         df_A = a − 1
SSB = Σ_i Σ_j n_ij (ȳ_ij. − ȳ_i..)²                    df_B = Σ_i b_i − a
SSE = Σ Σ Σ (y − ȳ_ij.)²                               df_E = N − Σ_i b_i
MSA=SSA/df_A,  MSB=SSB/df_B,  MSE=SSE/df_E
```
Coefficients (unbalanced) with T1 = Σ_i (Σ_j n_ij²)/n_i, Tn2 = Σ_ij n_ij², Ti2 = Σ_i n_i²:
```
k1 = (N − T1) / df_B
k2 = (T1 − Tn2/N) / df_A
k3 = (N − Ti2/N) / df_A
```
Solve the expected-mean-square equations, floor negatives at 0:
```
σ²_e = MSE
σ²_B = max( (MSB − MSE)/k1 , 0 )        # batch
σ²_A = max( (MSA − MSE − k2·σ²_B)/k3 , 0 )   # design
```
Shares = each σ² / (σ²_A + σ²_B + σ²_e). Run **overall** and **within each cause**.

### 6.2 Results
| Subset | N | Part = design | Lot = batch | Within-lot = operation | Manufacturer / Us |
|--------|---|--------------|-------------|------------------------|-------------------|
| **All causes** | 416* | 39.8% | 5.9% | 54.3% | **45.7% / 54.3%** |
| **Leak** (62%) | 255 | 58.8% | 13.1% | 28.0% | **72.0% / 28.0%** |
| **Deform** (31%) | 131 | 10.6% | 9.4% | 80.0% | **20.0% / 80.0%** |

*one row dropped for a missing install-quarter.

**How this yields C3 and C4:**
- Leak variance is dominated by **which part it is** (design 59%) → **manufacturer**
  problem; leaks are the biggest failure mode (62%), so this is the biggest lever.
- Deform variance is dominated by **within-lot residual** (80%): units from the *same*
  delivery scatter widely → not a design or batch signature → **operation** (handling/
  process). → **C3**.
- Overall ≈ **46/54** manufacturer/operation → **C4**. Pooling Leak and Deform (which
  point opposite ways) is *why you must never quote a single blended cause* — the modes
  partly cancel.

### 6.3 The method pitfall we caught (why 60/40 was wrong)
An earlier hand analysis reported part 42% / **lot 20%** / within 38% → "60% manufacturer."
Reproduced here: using a **sum-of-squares share** (η²-style) for the lot term inflates it,
because "lot" expands to ~128 dummy columns that soak up SS which is really sampling
noise. Our first SS-based pass indeed gave lot ≈ 20–33%. The **variance-component
estimator** removes that inflation → lot ≈ **6%**. Lesson baked into the method:
**decompose with variance components, not SS shares.** Direction of the story is
unchanged; the *batch* magnitude was overstated.

---

## 7. Analysis 4 — within-part batch test (isolating a bad lot)

To test "was a specific delivery defective," hold the **part fixed** and ask whether
**install lot (quarter)** explains life within it — Kruskal–Wallis per part, using
quarters with ≥ 3–4 units and parts with ≥ 2 such quarters; report ε².

| Part | type | #lots | N | ε² | p | Read |
|------|------|-------|---|----|----|------|
| **B-TU-004** | Turnup | 6 | 36 | **0.343** | **0.009** | Real batch effect |
| **B-TU-007** | Turnup | 6 | 47 | **0.204** | **0.020** | Real batch effect |
| B-TU-005 | Turnup | 5 | 24 | 0.103 | 0.203 | none |
| B-MT-006 | MTG | 7 | 40 | −0.035 | 0.564 | none |
| B-TU-001 | Turnup | 4 | 29 | −0.054 | 0.647 | none |
| B-TU-009 | Turnup | 6 | 33 | 0.002 | 0.409 | none |
| B-TU-012 | Turnup | 6 | 43 | −0.003 | 0.431 | none |

(A separate ANOVA-on-log-life version of the same test agrees: B-TU-004 p=0.003,
B-TU-007 p=0.024, all others n.s.)

**How this yields C5:** only two parts show install-lot significantly moving life.
Multiple-comparison note: ~10 tests at α=0.05 expect ~0.5 false positives; observing 2,
with one at p=0.009, is above chance and both are the *same failure-prone Turnup
family* — enough to flag as genuine claim candidates, not enough to over-claim. For
every other part, life varies *within* every delivery → no batch story. **C5.**

---

## 8. Analysis 5 — the two clocks (install vs removal time)

Define **premature = life < 0.5 × that part's own median** (robust, target-free);
72/417 units (17%). Test association of `premature` with each time bucket via χ².

| Clock (bucket) | χ² | dof | p | Verdict |
|----------------|----|-----|---|---------|
| **Install quarter** (when made/delivered) | 11.2 | 10 | **0.345** | not clustered |
| **Removal quarter** (when it died in plant) | 22.7 | 8 | **0.0038** | **clustered** |

Premature rate by removal quarter: **2024Q3 = 50%** (11/22), 2024Q4 25%, then
18/18/13/14/11/12% — i.e. one spike over a ~12–15% baseline.

Corroboration: `Life ~ install_q` ε²=0.011 (p=0.14, n.s.); `Life ~ removal_q`
ε²=0.072 (p=1.1e-5, significant). Spearman(install_date, life) = −0.14 (p=0.004) —
weakly negative, exactly what survivorship truncation alone produces (see §11).

**How this yields C6 (the decisive logic):**
- If a **bad manufacturing/delivery lot** were the cause, prematures cluster by **install
  time**. They **don't** (p=0.35). → rules out "a bad delivery period" fleet-wide.
- Prematures instead cluster by **removal time**, peaking 2024Q3. A cause tied to *when
  units die in the plant, regardless of when they were installed*, is a **plant/process/
  machine event** — an operation signature. → **C6.** Actionable lead: pull maintenance,
  machine, and consumable-batch logs for 2024Q3.

---

## 9. Analysis 6 — multi-factor ANOVA (does timing add anything beyond identity?)

Type-II ANOVA, `log_life ~ C(bladder_type) + C(cause) + C(install_quarter)`, on the 404
rows whose levels are well populated (≥5 each):

| Term | sum_sq | df | F | PR(>F) | η² |
|------|--------|----|----|--------|-----|
| bladder_type | 10.29 | 2 | 25.38 | ~0.000 | 0.112 |
| cause | 0.099 | 3 | 0.162 | 0.922 | 0.001 |
| install_quarter | 2.45 | 8 | 1.512 | 0.151 | 0.027 |
| Residual | 79.07 | 390 | | | 0.860 |

Model adj-R² = 0.126.

**How this reinforces C1/C4/C6:** controlling for everything jointly, **bladder_type is
the only significant term**; cause is inert (p=0.92) and install_quarter is not
significant (p=0.15). So *what* the bladder is drives life, not *when* it went in — the
same message as the single-factor and two-clock analyses, now holding the other factors
constant. (Low R²=0.13 is expected: most life variation is *within* part — i.e.
operation + noise — which these three fixed factors don't capture; that residual is
precisely the "operation" share quantified in §6.)

---

## 10. The full derivation chain (data → each conclusion, and what would falsify it)

- **C1** (identity drives life, not cause): cause fails all 4 screens (§4) *and* is inert
  in the joint model (§9). *Falsifier:* a significant cause effect with ε²>0.06. Not seen.
- **C2** (Push ≫ rest): Tukey isolates Push in both contrasts, MTG≈Turnup (§5); ~4.6×.
  *Falsifier:* overlapping Tukey intervals. Not seen.
- **C3** (mode split): variance components computed *separately by cause* diverge sharply —
  Leak design-heavy, Deform residual-heavy (§6.2). *Falsifier:* similar decomposition
  across causes. Not seen (59% vs 11% design share).
- **C4** (≈46/54): overall variance components (§6.2), with the SS-share pitfall corrected
  (§6.3). *Soft number* — depends on the "operation = residual" definition (§11).
- **C5** (only 2 batch parts): within-part KW (§7). *Falsifier:* many parts significant, or
  neither surviving an ANOVA cross-check. Cross-check agrees.
- **C6** (removal not install): the two χ² tests point opposite ways (§8) and the joint
  model shows install_quarter inert (§9). *Falsifier:* install clustered / removal flat, or
  the removal spike explained purely by truncation (§11 — checkable, not yet ruled out).

---

## 11. Threats to validity (and how each conclusion survives)

1. **Survivorship / right-truncation (the big one).** Only *already-scrapped* units are
   present; long-lived recent installs are still running and absent. This *guarantees* a
   spurious negative install-date↔life correlation and makes recent install cohorts look
   short. → We therefore **do not** interpret the install-quarter trend as causal (and it's
   n.s. anyway), and we flag that the **2024Q3 removal spike needs a maturation-bias check**
   before it's claimed as a hard event. C1/C2/C3/C5 are cross-sectional comparisons *within*
   the scrapped population and are not affected.
2. **"Operation" = residual**, so it absorbs measurement error and randomness → treat the
   54% as an **upper bound** on truly controllable operation variance.
3. **No true lot or machine ID.** "Lot" is proxied by install quarter; a real lot could be
   finer or coarser. C5's two parts are candidates to *investigate*, not proven RMA cases.
4. **Target is an internal estimate**, so "premature" uses each part's own median instead.
5. **Date ambiguity** (§1.1): mitigated by the install≤scrap repair and by analyzing at
   quarter granularity; residual misassignment is small and non-systematic.
6. **Multiplicity**: many tests run; we lean on effect size and cross-method agreement
   rather than any single p-value, and note the false-positive budget in §7.

---

## 12. How to reproduce — and how to do it *better*

**Reproduce exactly:**
```bash
pip install pandas openpyxl scipy statsmodels matplotlib
python3 scripts/clean_ext.py            # -> data/clean/bladder_ext_clean.csv (417 rows)
python3 scripts/analyze_lifetime.py     # §4,5,8,9 + figure
python3 scripts/variance_components.py  # §6,7,8 numbers
```

**Improvements (in priority order):**
1. **Survival analysis instead of ANOVA on scrapped-only data.** Add the *censored*
   (still-running) units and fit a **Weibull AFT / Cox model** with type, part, install
   cohort as covariates. This removes the truncation threat behind C6 and gives a proper
   hazard by install lot — the correct tool for "bad batch over time."
2. **Proper mixed model for §6.** Replace the moment estimator with REML
   `MixedLM logL ~ 1, groups=part, vc={lot: install_q}` (guard the unbalanced vc build) or
   `lme4::lmer(logL ~ 1 + (1|part/lot))` in R, to get variance components **with confidence
   intervals** — turns C4's soft 46/54 into an interval.
3. **Get the missing keys.** True **lot numbers** and a **machine/press ID** in logging turn
   the removal-time *proxy* (C6) into a direct machine test, and let C5's batch claims be
   pinned by serial adjacency.
4. **Verify the 2024Q3 spike** against maintenance logs before acting — confirm it's an
   event, not a window edge.
5. **Model life with a Weibull GLM** (log-link, β≈1) rather than log-normal ANOVA if you
   want parameters in engineering (cycles) units with the correct tail.

---

## 13. Appendix — key raw numbers

- N = 417 (from 429); 47% missed target; premature (½ median) = 72 (17%).
- Life: mean 1187, median 584, SD 1501, max 11,220; skew raw 2.68 / log10 0.02.
- Type medians: MTG 492, Turnup 535, Push 3437. Tukey Push−others ≈ 0.62–0.66 log10.
- Single-factor ε²: part 0.415, type 0.105, removal_q 0.072, install_q 0.011, cause ≈ 0.
- Variance shares — All: 40/6/54 · Leak: 59/13/28 · Deform: 11/9/80 (design/batch/op).
- Batch parts: B-TU-004 ε²=0.34 p=0.009; B-TU-007 ε²=0.20 p=0.02.
- Two clocks: install χ²=11.2 p=0.345; removal χ²=22.7 p=0.0038; 2024Q3 = 50% premature.
- Multi-factor Type-II: type p≈0, cause p=0.92, install_q p=0.15, adj-R²=0.126.

# anova-bladder

Root-cause analysis of **premature curing-bladder failure** — is it the
**manufacturer** (part design + delivered batch) or **us** (in-plant operation)?
An ANOVA / nested variance-decomposition pipeline over bladder scrap records that
turns floor experience into evidence.

**Yes — you can verify and recreate every finding below from this repo.** The
pipeline is deterministic: same inputs → same numbers. Follow §2, then check your
output against the numbers in §4.

---

## 1. Setup

```bash
pip install pandas openpyxl scipy statsmodels matplotlib
```
Python 3.9+. All data is in `data/raw/` (committed) — nothing external to fetch.

## 2. Reproduce everything (run in order)

```bash
python3 scripts/clean_ext.py          # raw CSV -> data/clean/bladder_ext_clean.csv (417 rows)
python3 scripts/add_part_names.py      # attach real part names (strip internal codes)
python3 scripts/analyze_lifetime.py    # one-way ANOVA, Tukey, install-time, multi-factor
python3 scripts/variance_components.py # manufacturer-vs-operation nested decomposition
python3 scripts/analyze_position.py    # machine & position ANOVA (event-log join)
```
Optional — rebuild the visual stories (each regenerates from the clean data):
```bash
python3 scripts/build_story.py         # reports/failure_story.html
python3 scripts/build_journey.py       # reports/evidence_journey.html
```

Numbers print to the console **and** land as text in `reports/*.txt`. Full
methodology (formulas, assumptions, threats to validity) is in
[`reports/ANOVA_METHODS_REPORT.md`](reports/ANOVA_METHODS_REPORT.md).

## 3. Data

| File | What it is |
|------|-----------|
| `data/raw/Ext_Bladder_dataset.csv` | **Primary** — per-bladder scrap records (life, target, cause) |
| `data/raw/Raw_Bladder_records.csv` | Event log — adds **machine** and **position** (C/AR/R); `Title` == `bladder_id` (100% join) |
| `data/clean/bladder_ext_clean.csv` | **Analysis table, 417 rows** — produced by the pipeline |

Response variable = `bladder_life` (cycles). Modeled as `log10` (raw life is
Weibull-ish, skew ≈ 2.7); parametric results confirmed with non-parametric
Kruskal–Wallis; effect size (η²/ε²) reported, not just p (N≈417 makes almost
everything "significant").

## 4. Findings — check your run against these exact numbers

Cleaning: **429 raw → 417** with a usable life (1 footer row + 11 blank-life dropped).

**One-way ANOVA on log10(life)** (`analyze_lifetime.py`):

| Factor | k | η²/ε² | ANOVA p | reproduces? |
|--------|---|-------|---------|-------------|
| `part_code` | 15 | 0.392 | 3.4e-33 | ✓ strongest |
| `bladder_type` | 3 | 0.120 | 3.1e-12 | ✓ Push ≫ MTG≈Turnup (Tukey) |
| `cause` | 4 | 0.010 | 0.25 | ✓ **no effect** |

**Manufacturer vs operation — nested variance decomposition** (`variance_components.py`,
Searle unbalanced two-level estimator; use variance components, **not** SS-shares):

| Split | Part (design) | Lot (batch) | Within-lot (operation) | → mfr / us |
|-------|--------------|-------------|------------------------|-----------|
| **Overall** | 39.8% | 5.9% | 54.3% | **45.7 / 54.3** |
| **Leak** | 58.8% | 13.1% | 28.0% | **72 / 28** |
| **Deform** | 10.6% | 9.4% | 80.0% | **20 / 80** |

**Machine & position** (`analyze_position.py`, event-log join, N=417):
- **Machine** within part: η²≈0.075–0.078, **p≈0.0003** → real operation lever.
  The 15″ turnup dies **7× faster on PAP21B** (≈226 vs ≈1,605 cycles).
- **Position (C/AR/R)**: η²≈0.002, **p≈0.57** → no effect; it just proxies bladder type.

**Two clocks** (premature clustering): install quarter p≈0.35 (n.s.) vs
**removal** quarter **p≈0.004** (2024Q3 ≈ 50% premature) → a plant event, not a
bad delivery.

> If your run matches the table above, you've reproduced the analysis. Small
> differences (±0.001) can appear across BLAS/statsmodels versions; the p-value
> **orders of magnitude** and effect-size **ranks** are what matter.

## 5. Conventions (important)
- **Refer to parts by real name, not code** — `B-TU-007` → `Bladder turnup 15"`
  (see `reports/part_name_map.csv`). Two part numbers share the `15"` name.
- **`Diagnose` (Pass/Abnormal) is NOT a predictor** — it *equals*
  `bladder_life >= target_life`, a restatement of the response. Never model it.
- **Survivorship truncation**: the data holds only *already-scrapped* bladders,
  so recent install cohorts look short-lived — don't read install-time trends as causal.

## 6. Reports & deliverables (in `reports/`)
- `ANOVA_METHODS_REPORT.md` — full reproducible method + derivation of each conclusion
- `SESSION_HANDOFF.md` — portable summary · `position_conflict_check.md` — machine/position write-up
- `*.txt` — raw numeric output from each script
- `manager_briefing.html` — one-page executive visual
- `failure_story.html` / `evidence_journey.html` — staged data-visualization stories
- `visual-qa` skill (`.claude/skills/visual-qa/`) renders + verifies any HTML visual before hand-off

## 7. Layout
```
data/raw/            source CSVs        scripts/            the pipeline
data/clean/          analysis tables    reports/            numbers, method, visuals
CLAUDE.md            working conventions
```

Work branch: `claude/anova-test-3ikcqe`.

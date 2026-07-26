# CLAUDE.md — anova-bladder

Root-cause analysis of **premature curing-bladder failure**: is it the
manufacturer (design + delivered batch) or us (in-plant operation)? Built around
an ANOVA / nested-variance-decomposition pipeline over bladder scrap records.

## Conventions (read first)
- **Refer to parts by their real name, never the internal code.** Codes like
  `B-TU-007` are internal; always translate to the real name (e.g.
  `Bladder turnup 15"`) via `part_name` in `data/clean/bladder_ext_clean.csv` or
  `reports/part_name_map.csv`. Two different part numbers can share a name (there
  are two `15"` turnups) — add "high-volume" / size context when it matters.
- **`Diagnose` (Pass/Abnormal) is NOT a predictor** — it equals
  `bladder_life >= target_life`, a restatement of the response. Never model it.
- **Model `log10(bladder_life)`** (raw life is Weibull-ish, skew ≈ 2.7). Confirm
  every parametric result with non-parametric Kruskal–Wallis; report **effect
  size** (η²/ε²), not just p (N≈417 makes everything "significant").
- **Mind survivorship truncation**: the data holds only *already-scrapped*
  bladders. Recent install cohorts look short-lived; don't read install-time
  trends as causal.

## Data
- `data/raw/` — source files. The two that matter:
  - `Ext_Bladder_dataset.csv` — definitive per-bladder scrap records (life, cause, target).
  - `Raw_Bladder_records.csv` — full event log; adds **position** (C/AR/R) and
    **machine** id. Its `Title` == `bladder_id` in the Ext data (100% join).
  - Others (`data_2..6`) are a machine log + report filter-lists; mostly ignorable.
- `data/clean/bladder_ext_clean.csv` — **primary analysis table, 417 rows.**
  Key columns: `bladder_life` (response), `part_code`, `part_name`,
  `bladder_type` (Turnup/MTG/Push), `cause`, `target_life`, `install_date`,
  `scrap_date`, `machine`, `position`.

## Pipeline (run in this order)
```bash
pip install pandas openpyxl scipy statsmodels matplotlib
python3 scripts/clean_ext.py          # -> data/clean/bladder_ext_clean.csv (417 rows)
python3 scripts/add_part_names.py     # attach real part_name (strip codes)
python3 scripts/analyze_lifetime.py   # one-way ANOVA, Tukey, install-time, multi-factor
python3 scripts/variance_components.py# manufacturer-vs-operation nested decomposition
python3 scripts/analyze_position.py   # position & machine join + conflict check
```
Reports land in `reports/` (`.txt` numbers, `manager_briefing.html`,
`SESSION_HANDOFF.md`, `ANOVA_METHODS_REPORT.md`, `position_conflict_check.md`).
`scripts/clean_data.py` cleans the older `data_2/4/5` files (reference only).

## Method
Nested variance decomposition of log-life: **part (design) → lot-within-part
(batch) → within-lot residual (operation)** via the Searle unbalanced two-level
ANOVA estimator (`variance_components.py`). Use variance components, **not**
sum-of-squares shares (SS-shares overstate the batch term). Machine & position
tested within-part via Type-II ANOVA.

## Current findings (summary)
- **Identity drives life, not failure mode.** Part/type dominate (η² 0.2–0.4);
  cause has ~zero effect. **Push** lasts ~3,400 cycles vs ~500 for turnup/MTG.
- **Blame splits by mode:** Leak ≈ 72% manufacturer (design); Deform ≈ 80%
  operation (same delivery, different outcome). Overall ≈ 46% mfr / 54% us.
- **Machine matters** (η²=0.078, p=0.0004 within part) — the concrete operation
  lever. Worst: PAP13, PAP21B, BNS20. `Bladder turnup 15"` dies **7× faster on
  PAP21B** (226 vs 1,605 cycles) → its apparent "bad batch" is largely a machine
  effect. `Bladder turnup 10"` remains a clean supplier-batch case.
- **Position (C/AR/R) has no effect** — it just proxies bladder type (C = MTG).
- Premature failures cluster by **removal** time (2024Q3 spike, ~50%), not
  **install** time → a plant event, not a bad delivery.

## Installed skills (`.agents/skills/`, symlinked into `.claude/skills/`)
Stack chosen for the workflow **raw CSV → insights & relationships → simple
visuals for non-data-scientist audiences** (pinned in `skills-lock.json`):

| Stage | Skill | Source |
|-------|-------|--------|
| Profile a new CSV (shape, nulls, quality) | `explore-data` | knowledge-work-plugins |
| Stats: significance, correlation, outliers, trends | `statistical-analysis` | knowledge-work-plugins |
| ML / modeling / feature engineering | `data-scientist` | borghei/claude-skills |
| General SQL + analysis + reporting | `data-analyst` | borghei/claude-skills |
| Pick the right chart, publication quality | `create-viz`, `data-visualization` | knowledge-work / kw |
| Interactive HTML dashboard for stakeholders | `build-dashboard` | knowledge-work-plugins |

Also already available in-session: document skills (`docx`, `pdf`, `pptx`,
`xlsx`) for Excel/deck deliverables, and `dataviz`. The
`/plugin install document-skills@anthropic-agent-skills` line is an interactive
CLI command (not tool-runnable); those skills are already active here.

Suggested per-stage order for a fresh CSV: `explore-data` → `statistical-analysis`
→ `create-viz`/`data-visualization` → `build-dashboard` (audience-facing).

## Git
Work branch: `claude/anova-test-3ikcqe`. Commit + push there.

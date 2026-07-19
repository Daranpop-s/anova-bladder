# Cleaned datasets

Produced by `scripts/clean_data.py` from the raw exports in `data/raw/`.

## What each raw file was

| Raw file | Role |
|----------|------|
| `data_5_bladder_records.xlsx` | **Main data** — one row per scrapped bladder (date, part, cause, target, life) |
| `data_4_summary.xlsx` | Pivot summary per part number (derived from the same source) |
| `data_2_machine_log.xlsx` | Machine breakdown/repair log — a separate system |
| `data_3_month_list.xlsx` | Just a list of month labels (a report filter list) — not analytical data |
| `data_6_day_list.xlsx` | Just a list of day numbers (a report filter list) — not analytical data |

## `bladder_records_clean.csv` (primary — for the ANOVA)

421 rows (from 433 raw: 1 footer row + 11 rows with no Bladder Life removed).
Response variable = **`bladder_life`**.

| Column | Meaning |
|--------|---------|
| `last_date` | Date the bladder was scrapped |
| `year_month` | `YYYY-MM` of `last_date` (time factor) |
| `part_number` | Canonical part no. e.g. `0216-1-1074` (collapses name typos) |
| `part_desc` | Original free-text description |
| `bladder_type` | `MTG`, `Turnup`, or `Push` (parsed from description) |
| `size_in` | Nominal diameter in inches (first quoted value) |
| `cause` | Failure mode in English: Leak, Deform, Tear, Burn out, Flabby, Bad material, Quality issue |
| `target_life` | Design target life |
| `bladder_life` | **Actual life achieved (response variable)** |
| `reached_target` | `True` if `bladder_life >= target_life` |
| `bladder_id` | Original per-bladder id string |
| `status` | Source status (all `ทิ้ง` = scrapped) |

## Candidate factors and how they rank (one-way ANOVA preview)

| Factor | p-value | eta² (variance explained) |
|--------|---------|---------------------------|
| `part_number` | 3.6e-27 | 0.34 |
| `reached_target` | 1.7e-29 | 0.26 |
| `bladder_type` | 1.8e-16 | 0.16 |
| `size_in` | 1.2e-08 | 0.13 |
| `cause` | 0.059 (n.s.) | 0.02 |

Bladder **type** matters most among the design factors — `Push` bladders last
~3,400 cycles on average vs ~900–1,100 for MTG/Turnup. Failure **cause** does
*not* significantly explain the lifetime. These are single-factor screens; a
full (multi-factor) ANOVA will run once the final clean dataset is added.

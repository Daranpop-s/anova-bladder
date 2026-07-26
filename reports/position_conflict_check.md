# Position (C/AR/R) & Machine ANOVA — and conflict check vs prior findings

New dataset: `Raw_Bladder_records.csv` (1,998 events, 610 bladders). Adds two
factors the Ext analysis lacked — **position** (C=Center, AR=Anti-reference,
R=Reference/on the bati machine) and **machine** id. `Title` == Ext `bladder_id`
(**100% match**), so the real `bladder_life` (cycles) was attached to each
bladder's position/machine and run through the same log-life ANOVA.
N = 417 (position on 416, machine on 408). Script: `scripts/analyze_position.py`.

## Headline: the new insights do NOT conflict — they confirm and sharpen

| Prior finding | New data says | Verdict |
|---------------|---------------|---------|
| Cause doesn't affect life | cause η²=0.009, p=0.18 (again n.s.) | ✅ same |
| Part / type dominate life | part η²=0.22–0.33 in every model; type η²=0.12 | ✅ same |
| ~54% "operation" residual (inferred) | **machine is real: η²=0.078, p=0.0004 within part** | ✅ **now direct, not inferred** |
| (no position data before) | **position has NO effect (η²=0.006, p=0.30)** | ⚠️ new — and it's a confound (below) |

## 1. Position (C / AR / R) does NOT affect life
- Single-factor: η²=0.006, ANOVA p=0.30, Kruskal p=0.39 → nothing.
- Life by position: AR 590 · C 492 · R 637 (median cycles) — flat.
- **Why it looks like it might, but doesn't — collinear with type.** Position is
  almost perfectly a proxy for bladder type:

  | position | MTG | Push | Turnup |
  |----------|-----|------|--------|
  | C | 74 | 0 | 1 |
  | AR | 0 | 14 | 148 |
  | R | 0 | 18 | 161 |

  `C` is the MTG center position; AR/R are the Turnup/Push side positions. Once
  **part is controlled** (Type-II ANOVA `logL ~ part + position`), position
  η²=0.002, **p=0.57** — definitively nothing. C/AR/R is not a lever.
- Side note (consistent with prior): `C` (all MTG) has **0 deform** failures;
  deform lives entirely on AR/R (Turnup) — matches "deform is a Turnup problem."

## 2. Machine DOES affect life — the operation signal is now direct
- Single-factor: η²=0.221, p=1.8e-15 (but confounded with part).
- **Within part** (`logL ~ part + machine`): machine **η²=0.078, p=0.0004** —
  survives controlling for what the bladder is. ~8% of life variation is the
  machine, on top of part identity. adj-R² rises 0.31→0.36 when machine is added.
- This is the **first direct evidence** for the "operation / in-plant" component
  that was previously only a residual. It confirms conclusion C4/C6: part of the
  ~54% "us" share is concretely **the machine a bladder runs on**.
- Worst machines by premature rate (life < ½ part-median, n≥12): **PAP13 33%,
  PAP21B 29%, BNS20 28%, PAP18 24%** vs best PAP20 0%, PAP21A 9%, BNS18 10%.

## 3. Does machine explain the 2024 Q3 removal spike?
Partly. The Q3 prematures are spread across **BNS18/19/20 and PAP21B** (PAP21B: 5
scraps, 80% premature; the BNS trio all 100% but on 1–2 units each) rather than one
smoking-gun machine. Cell counts are tiny (≤5), so this is a lead, not proof —
**pull the maintenance logs for PAP21B and the BNS line around 2024 Q3.**

## 4. `Old vs New` bladder
η²=0.156, p=6e-17 (single factor). "Old" (reused) vs "New" units differ in recorded
life — but this is entangled with reuse/survivorship (an "Old" unit already survived
a prior cycle), so treat as descriptive, not causal, until defined precisely.

## Bottom line
No contradiction with the earlier ANOVA. Position (C/AR/R) turns out to be a
disguised type variable and carries no independent effect. Machine is the genuinely
new, actionable factor: it significantly affects life within a part, which
**directly confirms** the previously-inferred operation share and hands you a
concrete target list (PAP13, PAP21B, BNS20). The manufacturer-vs-operation split,
the leak/deform mode split, and the part/type dominance all stand unchanged.

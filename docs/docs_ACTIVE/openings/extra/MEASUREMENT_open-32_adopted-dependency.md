# MEASUREMENT M06 — OPEN-32: does any *adopted* result depend on `layout_assign`?

> **Date:** 2026-08-06. **Executed by:** the manager session, directly — read-only, no simulation,
> no cluster, no interpreter run. Every command was a `git`, `grep`, `awk`, `ls` or `find`.
> **Item:** OPEN-32's named first measurement, which the register calls *"cheap"* and requires be
> **confirmed rather than assumed** (register `INVESTIGATION_open-items-register.md:434-437`, echoing
> OPEN-01's own "What is NOT known" item 3 at `:172`).
> **Answer: NO. No adopted result depends on `layout_assign`.** Established three independent ways,
> two of which are exhaustive rather than sampled.

---

## 1. The question, stated precisely

OPEN-01 and OPEN-03 are both large and both unremediated. OPEN-32 records that they point in opposite
directions and that their net is unmeasured. Before any of that matters to the project's headline
claims, one prior question has to be settled:

> **Do the numbers this project has adopted — NYC −31.3% / LA −3.6% / Austin −30.5%, fleet-weighted
> ~~158.0~~ **157.1 kWh/m²** (pooled: total simulated energy ÷ total simulated floor area; the struck
> figure was a count-weighted mean of the 12 cell means, superseded 2026-08-12, OPEN-43) — pass
> through the `layout_assign` code path at all?**

If they do not, then OPEN-01 and OPEN-03 are bounded to a method that is already flagged
*not certified for fleet EUI*, and the adopted baseline is not in question. If they do, the adopted
baseline inherits a median ×2.0 denominator error and a ≥1.72× lighting-load error at once.

The register was explicit that this must not be assumed. It is now measured.

---

## 2. What "the adopted baseline" resolves to

| | |
|---|---|
| **Definition** | Phase-E full realism + the E-R3-3 archetype correction + elevators |
| **Adoption record** | `docs/docs_DONE/LOADS & SCHEDULES/elevators/PLAN_elevator_loads_implementation.md:257` — *"Decision: ADOPTED. E-R3-3+elevators is the new Phase-E adopted baseline; headline NYC −31.3% / LA −3.6% / Austin −30.5%, fleet-weighted 158.0 kWh/m²"* (verbatim archived quote, not altered here — see restatement below: ~~158.0~~ **157.1 kWh/m²**, pooled: total simulated energy ÷ total simulated floor area; the struck figure was a count-weighted mean of the 12 cell means, superseded 2026-08-12, OPEN-43) |
| **Restated at** | `docs/PROJECT_CHECKLIST.md:88-91` |
| **Artifacts** | `docs/docs_VALIDATION/validations/overAll/results/phaseE_elevrb/<12 cells>/05_results.csv` (post-elevator, adopted) and `docs/validations/overAll/results/phaseE_er33/<12 cells>/05_results.csv` (the E-R3-3-only predecessor) |
| **Rows** | **8,160 in each tree** — verified by count, and equal to the T08 ∪ T20 union established by M05 |

Both trees were checked, not only the adopted one, so that the finding also covers the pre-elevator
record that older reports quote.

---

## 3. Line of evidence 1 — temporal: the mode did not exist yet

`layout_assign` is not merely unused by the adopted baseline; it had not been written when the
adopted baseline was produced.

| Fact | Command | Result |
|---|---|---|
| First commit in the repo containing the string `layout_assign` | `git log -S"layout_assign"` | **`3a925f9`, 2026-07-25** |
| The string at that commit's parent | `git grep -c "layout_assign" 3a925f9^` | **no matches — absent from the tree** |
| Adopted (post-elevator) artifacts entered git | `git log --diff-filter=A -- …/phaseE_elevrb/nyc_urban/05_results.csv` | **`ef19141`, 2026-07-21** |
| Predecessor (E-R3-3-only) artifacts entered git | `git log --diff-filter=A -- …/phaseE_er33/nyc_centre/05_results.csv` | **`03e2121`, 2026-07-02** |

Both sets of adopted artifacts were committed **before** the mode's first line of code — the
post-elevator set by 4 days, the predecessor set by 23.

**Stated limitation, so this line is not over-read.** This repository's history is **40 commits**
(`git rev-list --count HEAD`) for roughly two months of work, i.e. it is curated, not a
commit-by-commit record. A squashed history can hide the true first authorship date of a symbol.
This line of evidence is therefore treated as **corroborating, not decisive** — it is consistent with
the other two but does not carry the finding alone. Lines 2 and 3 do, and neither depends on history.

---

## 4. Line of evidence 2 — structural: `auto` cannot reach `layout_assign`

This is the decisive line, and it is a property of the code at HEAD, independent of any history.

`decide_zoning_strategy()` (`openubem/geometry/zoning.py:13-42`) is the single point where a
resolution mode becomes a zoning strategy. Its structure:

- Lines 17–33 handle each **explicitly named** mode: `building` → `single_zone`, `floor` →
  `one_zone_per_floor`, `fast_zone` → `perimeter_core`, **`layout_assign`/`layout_assigner` →
  `layout_assign`** (`:23-24`), `zone` → `room_layout`/`perimeter_core`.
- Line 34 raises `ValueError` on any mode that is not one of those and is not `auto`.
- Lines 36–42 are the entire `auto` branch, and they can return exactly three values:
  `single_zone` (1-floor buildings), `perimeter_core` (≥500 m² footprint, non-apartment), or
  `one_zone_per_floor` (everything else).

> **`auto` has no path to `layout_assign`.** The strategy is reachable only by a caller explicitly
> passing `resolution_mode="layout_assign"` or `"layout_assigner"`.

The two mechanisms that OPEN-01 and OPEN-03 are actually about are gated on the same string, one
level further in:

- **OPEN-01's `ZoneGroup` list multiplier** rides on prototype substitution. Substitution is entered
  through `_layout_assign_baseline_path()` (`openubem/idf/builder.py:67-77`), whose second statement
  is `if resolution_mode not in ("layout_assign", "layout_assigner"): return None` (`:75-76`). With
  `None` returned, `BuildingIDF.__init__` (`:201`) never loads a baseline IDF, so no prototype — and
  therefore no `ZoneGroup` — ever enters the model.
- **OPEN-03's vintage substitution** is a property of the assigned baseline IDF itself (the E+ 23.1
  DOE/ASHRAE 90.1 library). No baseline IDF, no substituted vintage.
- The mass-bearing `MATERIAL` default that distinguishes `layout_assign` (`builder.py:194-198`) is
  likewise conditioned on the same two tokens.
- `openubem/results/parser.py:200-201` states the same boundary from the reading side in the
  codebase's own words: *"`resolution_mode=None` (default) preserves the exact pre-T14 behavior for
  every mode other than `layout_assign`/`layout_assigner`."*

**`layout_assign` is strictly opt-in at every one of these points.** A run that never names it is
untouched by all of it.

---

## 5. Line of evidence 3 — artifact: exhaustive, all 16,320 adopted rows

Line 4 shows the adopted baseline *cannot* have used the mode. Line 5 shows it *did not*, by reading
every row that was actually produced.

`05_results.csv` carries a `zoning_strategy` column (column 6). Tallying it across all 12 cells of
both trees — **not a sample, every row**:

| Tree | `one_zone_per_floor` | `single_zone` | `perimeter_core` | `layout_assign` | total |
|---|---|---|---|---|---|
| `phaseE_elevrb` (**adopted**) | 4,291 | 3,259 | 610 | **0** | 8,160 |
| `phaseE_er33` (predecessor) | 4,282 | 3,259 | 619 | **0** | 8,160 |

The observed values are **exactly the three that `auto` can return**, in both trees, with no fourth
value present. A full-text search for the string `layout_assign` across both trees returns **no
matching file** — not in the CSVs, not in the GeoJSONs.

**A supporting cross-check on the other widely-cited artifact.** `t08_all_modes_eui.csv` — the source
of the published cross-mode comparison — contains **4 modes × 4,530 buildings**: `auto`, `building`,
`fast_zone`, `floor`. **No `layout_assign` rows.** This independently reproduces M05's shared-count of
4,530 and confirms the cross-mode table is also free of the method.

---

## 6. Finding

> **OPEN-32's first measurement is complete. No adopted result depends on `layout_assign`.**
>
> OPEN-01 and OPEN-03 are confined to the `layout_assign` method. The adopted fleet baseline
> (~~158.0~~ **157.1 kWh/m²** — pooled: total simulated energy ÷ total simulated floor area; the
> struck figure was a count-weighted mean of the 12 cell means, superseded 2026-08-12, OPEN-43),
> its three city anchors, its predecessor E-R3-3-only record, and the published
> four-mode cross-mode comparison are all outside their reach — structurally, because `auto` cannot
> select the method, and factually, across all 16,320 adopted rows plus 18,120 cross-mode rows.

**This closes OPEN-01's "What is NOT known" item 3** (register `:172`), which was flagged
*"now load-bearing"* on 2026-08-05.

**What this does not do.** It does not shrink OPEN-01 or OPEN-03. Both remain exactly as large as M01
and M03 measured them, and both still make every published `layout_assign` number wrong — including
the **−29.1%** figure. What changes is the blast radius: it is bounded to a method the project has
already labelled *not certified for fleet-level EUI reporting*, and it does not reach the numbers the
project stands on. OPEN-32's own question — the **net** of the two opposing errors — is untouched by
this and stays open.

---

## 7. Where `layout_assign` numbers *are* published — the bounded exposure

For completeness, the same sweep enumerated what does depend on the method, so the boundary is drawn
from both sides:

| Publication | Dependence | Carries the caveat? |
|---|---|---|
| `docs/docs_DONE/SETUP/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md` | the arc's own record, incl. **−29.1%** at `:458` | it is the arc record, not a headline claim |
| `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` §5.1.2 + mode table `:137` | describes the method; quotes −29.1% at `:178` | ✅ *"adopted for zone/HVAC-topology studies — **not certified for fleet-level EUI reporting**"* |
| `docs/docs_EXPLANATION/Results/OpenUBEM_results_Resolution.md` §10 | structural comparison, T20 harvest | ✅ same caveat at `:32`; and `:365` states §4's cross-mode EUI table **deliberately excludes** `layout_assign` |
| `t19_*` / `t20_*` harvest CSVs | wholly | n/a — data files |

**The caveat the project already carries is correct, and this measurement is what makes it true rather
than merely prudent.** Both explanation documents were checked and neither promotes a `layout_assign`
EUI into a headline position.

---

## 8. Incidental finding — the published documents point at a directory that no longer exists

Not part of OPEN-32, found while verifying §7, and reported here because it is a defect in the
project's user-facing deliverables.

Commit `bca92d0` (2026-08-05, *"docs: restructure layoutAssigner into docs_DONE"*) moved the arc from
`docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/` to `docs/docs_DONE/SETUP/layoutAssigner/`.
**`docs/docs_ACTIVE/simulation-Resolution/` does not exist at all any more** — the whole parent is
gone. The references to it were not updated.

**31 files repo-wide** still cite the dead path. Twenty-six are inside the frozen arc record itself
and are correctly left alone (append-only rule). **Five are live**, and three of those are the
project's most-read documents:

| Live file | Dead references | Why it matters |
|---|---|---|
| `docs/PROJECT_CHECKLIST.md` | **10 distinct targets** — the arc root, `COMPLETION_REPORT.md`, all four `PLAN_*` docs, both director prompts, `results/` | This is the **user's own monitoring surface**. Every link from it into the layoutAssigner arc is broken. |
| `docs/docs_EXPLANATION/Results/OpenUBEM_results_Resolution.md` | 9 references / 4 distinct targets | Includes **2 embedded figures** that render as broken images |
| `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` | 3 references / 3 distinct targets | Includes **1 embedded figure** |
| `docs/docs_EXPLANATION/OpenUBEM_graphic_summary_prompt_styles.md` | 1 | minor |
| `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-05_defect-id-sweep.md` | 1 | this arc's own doc |

**Every target still exists**, under its new name — the move re-nested and in three cases re-prefixed
the files (`PLAN_debug_implementation.md` → `debug/DONE/…`; `PLAN_storey-matching_implementation.md` →
`DONE_PLAN_…`; `PLAN_e-la-20_multilayer-fix.md` → `DONE/e-la-20/DONE-PLAN_…`). So this is a
resolvable rename, not lost material.

**Carried to the register as new item OPEN-33.** Its first measurement is this table — already made —
so it is actionable immediately.

---

## 9. Reproduction

```bash
# Line 2 — auto cannot reach layout_assign
sed -n '13,42p' openubem/geometry/zoning.py
sed -n '67,77p' openubem/idf/builder.py

# Line 3 — exhaustive tally over all adopted rows
for d in docs/validations/overAll/results/phaseE_er33 \
         docs/docs_VALIDATION/validations/overAll/results/phaseE_elevrb; do
  awk -F, 'FNR>1{print $6}' $d/*/05_results.csv | sort | uniq -c
done
grep -rl "layout_assign" docs/validations/overAll/results/phaseE_er33 \
     docs/docs_VALIDATION/validations/overAll/results/phaseE_elevrb   # expect: no output

# Cross-mode artifact
awk -F, 'FNR>1{print $3}' docs/docs_RESULTS/OpenUBEM_results_Resolution/csv/t08_all_modes_eui.csv \
  | sort | uniq -c

# §8 — stale links
grep -rl "docs_ACTIVE/simulation-Resolution/layoutAssigner" docs openubem | grep -v docs_DONE
```

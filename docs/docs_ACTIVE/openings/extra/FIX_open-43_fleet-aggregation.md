**Task:** T01, `PLAN_rulings-and-five-items-2026-08-12.md`. **Item:** OPEN-43. **Status:** done.

## 1. What changed

The published fleet headline is now **~~158.0~~ 157.1 kWh/m²** — the pooled figure, `Σ(energy) /
Σ(floor area)` over all 8,154 successfully simulated buildings at once. The old figure (158.0298,
rounded to 158.0) was a **count-weighted mean of the 12 cell means**, never previously named as such.
Every live location found by the grep in §1.1 was restated with the required three elements: the old
number struck (not deleted), the new number, and the definition — using the exact markup the plan
specifies. `openubem/results/aggregator.py` now carries a docstring note stating it is per-cell only
and pointing at the pooled fleet formula. `scripts/analysis/open43_fleet_aggregations.py` reproduces
all four director-verified aggregations from the raw `05_results.csv` files and asserts them to 4 dp.

## 2. Formula, verified against §4.1

Per building: `floor_area_m2 = footprint_area_m2 × max(levels, 1)` (E-R3-1 total floor area). Per
cell, over `simulation_status == "success"` rows only: `weighted_total_eui = Σ(total_eui_kwh_m2 ×
floor_area_m2) / Σ(floor_area_m2)` — this reproduces the reference `weighted_total_eui` column in
`openubem/outputs/comparisons/open42_t02_percell_repro.csv` exactly, cell by cell. Four fleet
aggregations built on top of the 12 per-cell values:

| aggregation | formula | value | §4.1 target |
|---|---|---|---|
| pooled (adopted) | `Σ(cell_mean × cell_area) / Σ(cell_area)` | **157.0552** | 157.0552 |
| weighted by total count (old published) | `Σ(cell_mean × cell_n_total) / Σ(cell_n_total)` | 158.0298 | 158.0298 |
| weighted by success count | `Σ(cell_mean × cell_n_success) / Σ(cell_n_success)` | 158.0557 | 158.0557 |
| unweighted mean of cell means | `mean(cell_mean)` | 160.0993 | 160.0993 |

`n_total` sums to 8,160, `n_success` to 8,154, total floor area (success rows) to 23,545,868.4 m² —
all match §4.1 exactly.

## 3. Script run

```
python scripts/analysis/open43_fleet_aggregations.py
```

Ran in the foreground, exit code **0**. Output:

```
n_total (sum over 12 cells): 8160
n_success (sum over 12 cells): 8154
total floor area (success only): 23545868.4 m^2
pooled: 157.0552 (expected 157.0552)
weighted_by_total_count: 158.0298 (expected 158.0298)
weighted_by_success_count: 158.0557 (expected 158.0557)
unweighted_mean_of_cell_means: 160.0993 (expected 160.0993)
wrote openubem/outputs/comparisons/open43_fleet_aggregations.csv
```

All four values reproduce the §4.1 director-verified figures to 4 decimal places. The script fails
loudly (non-zero exit, `MISMATCH` printed to stderr) if any of the four drift outside 1e-4 of the
target — this is a real assertion, not a print statement.

## 4. Files changed — 13, full list

| file | what changed |
|---|---|
| `openubem/results/aggregator.py` | docstring note: per-cell only, fleet roll-up lives outside it, formula, pointers |
| `docs/PROJECT_CHECKLIST.md` | head-section sentence (not a journal block) restated |
| `docs/docs_ACTIVE/openings/extra/AMENDMENT_register_2026-08-05.md` | 1 restatement |
| `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-01_denominator-audit-e02.md` | 1 restatement |
| `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-24-27_june-remnants.md` | 1 restatement |
| `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-32_adopted-dependency.md` | 3 restatements (1 quote-block, 1 table cell annotated beside a preserved verbatim archived quote, 1 prose) |
| `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-42_placeholder-and-fleet-impact.md` | 4 restatements (section header + 3 body) |
| `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_compute-queue.md` | 1 restatement |
| `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_e02-audit-and-closure.md` | 1 restatement |
| `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_five-item-sweep-2026-08-12.md` | 2 restatements (§4 fact line, T02 task-header) — task body/CP table/progress log deliberately left, see §5 |
| `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_no-compute-queue.md` | 1 restatement |
| `docs/docs_ACTIVE/openings/implemenation/board_published-numbers.html` | 3 restatements (hero stamp, T02 board row, NEW/OPEN-43 board row) |
| `docs/docs_ACTIVE/openings/reporting/board_published-numbers.html` | same 3 restatements — this file is byte-identical to the one above (verified by `diff` before editing) and is edited as a separate file |

New files: `scripts/analysis/open43_fleet_aggregations.py`,
`openubem/outputs/comparisons/open43_fleet_aggregations.csv`.

## 5. Locations found by the grep and deliberately NOT changed, with reasons

The grep (`158\.0[0-9]*|fleet EUI`) over `docs/docs_ACTIVE/`, `docs/docs_REPORTS/`,
`docs/docs_EXPLANATION/`, `docs/PROJECT_CHECKLIST.md`, `openubem/`, `scripts/`, and the two `.html`
boards found more matches than the 13 files above. Everything not restated, and why:

1. **`docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`** — hard rule 3 forbids editing
   the register; belongs to the director.
2. **`docs/docs_ACTIVE/openings/prompts/DIRECTOR_PROMPT_openings_2026-08-11.md`** — hard rule 3
   forbids editing the (current) director prompt.
3. **`docs/docs_ACTIVE/openings/prompts/previous/DIRECTOR_PROMPT_openings_2026-08-06.md` and
   `_2026-08-10.md`** — dated, closed snapshots of past director prompts. Not literally "the director
   prompt" (that is the current file, excluded above by name), but editing a frozen historical
   snapshot to insert a 2026-08-12 finding would misrepresent what was known on 2026-08-06/10. Treated
   like a `docs_DONE` archive even though its path is under `docs_ACTIVE`.
4. **`docs/docs_ACTIVE/openings/implemenation/previous/PLAN_rulings-and-five-items-2026-08-12.md`** (this
   plan) — explicitly off-limits to the executor by the kickoff instructions (only the register,
   director prompt, and its own §10 were named, but this document is the live shared plan every
   parallel executor reads from; editing any part of it risks colliding with concurrent executors and
   was not asked for).
5. **`docs/docs_ACTIVE/openings/implemenation/previous/PLAN_five-item-sweep-2026-08-12.md`**, T02's numbered
   "How" steps (lines ~245-261), the CP-1 stop-and-report row (line ~441), and its own `## 8. Progress
   log` section (lines ~486-500) — these are the **literal historical instruction text** given to,
   and the **literal completion record written by**, a past executor/director for an already-closed
   task ("Reproduce 158.0 from them before changing anything... If you cannot reproduce 158.0 to
   within 0.1, STOP"). Rewriting the number there would misrepresent what was actually asked and what
   was actually verified at the time — different in kind from the two background-description
   sentences in the same file (§4's fact list, the T02 header) that were restated, because those state
   the baseline as background fact rather than as an operational instruction or completion record.
6. **`docs/PROJECT_CHECKLIST.md`, the `>`-quoted journal entry near "Its effect on the 158.0 kWh/m²
   fleet figure is unmeasured"** — inside a blockquote. The file's own head section states journal
   blocks are "append-only and never rewritten." Left untouched, consistent with T09's treatment of
   the same file (see `FIX_open-31_classification-gate.md`).
7. **`docs/docs_EXPLANATION/Results/OpenUBEM_results_Resolution.md`** and
   **`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_loads-vintage-split.md`** — both matched
   only on the bare phrase "fleet EUI" (a table-row label; "layout_assign-vs-fleet EUI gap"), quoting
   no number. Nothing to strike.
8. **`openubem/outputs/3D/*.html`, `openubem/outputs/nyc_suburban_*_viewer.html`,
   `openubem/outputs/stage6/.../06_context_blocks.geojson`, and
   `openubem/outputs/comparisons/{b00_coverage_census_row_detail,e02_simulated_floor_area,
   open01_denominator_audit,open42_fleet_eui_impact,t08_all_modes_eui,t17..t20_layout_assign_eui}.csv`**
   — checked individually with context. Every match is **coincidental numeric data**: a
   `footprint_area_m2` value, a UTM/lon-lat coordinate, or a per-building `total_eui_kwh_m2` that
   happens to start with "158.0…" — not prose stating a fleet headline. `open42_fleet_eui_impact.csv`
   does contain a text note referencing "the published 158.0 figure," but it is a generated output of
   an already-completed measurement run, not a narrative document a reader consults for the current
   figure. None of these were edited.
9. **`scripts/analysis/open42_t02_fleet_eui_impact.py` and
   `scripts/analysis/open42_t02_reproduce_fleet_eui.py`** — the actual scripts for the already-closed
   OPEN-42 T02 measurement. Their hardcoded 158.0/158.03 values are the historical reproduction target
   that task verified against (matching the CP-1 criteria in item 5 above), not a claim about the
   current fleet figure. Left untouched for the same reason as item 5.

## 6. Final grep check

After all edits, `grep -rn -E "158\.0[0-9]*" docs/docs_ACTIVE/ docs/PROJECT_CHECKLIST.md
docs/docs_EXPLANATION/ docs/docs_REPORTS/ openubem/ scripts/` still returns matches — every one of
them falls into one of the 9 categories in §5 above, each with a stated reason. **No live location
quotes a bare `158.0` as the current fleet headline without either being struck-and-restated, or
named here as a deliberate, reasoned exclusion.**

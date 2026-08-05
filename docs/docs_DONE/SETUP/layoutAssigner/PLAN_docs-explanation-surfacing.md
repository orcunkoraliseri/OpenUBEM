# PLAN — surface `layout_assign` into `docs_EXPLANATION`

- **Slug:** `docs-explanation-surfacing`
- **Opened:** 2026-08-05, by the manager session that signed CP-E (storey-matching arc close).
- **Binding contract:** `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md`
  **§8 and §9** (the arc's own closing record). Where this plan and that document disagree, that
  document wins and you STOP and quote the conflict.
- **Why this exists:** the LayoutAssigner arc closed 2026-08-04 with CP-E signed, but **neither
  reader-facing document in `docs_EXPLANATION` was updated.** `OpenUBEM_fundamentals.md` §5.1 still
  describes the mode as it stood on 2026-07-25 and links to a path that no longer exists;
  `Results/OpenUBEM_results_Resolution.md` (2026-07-01) does not mention the mode at all. A reader of
  either document today would draw a conclusion the arc explicitly ruled out.

---

## 1. Hard rules for the executor

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** Interpreter `./.venv/Scripts/python.exe`.
2. **You execute this plan. You do not write plans and you do not propose alternatives.** If the
   source-of-truth document is ambiguous, **STOP and quote the conflict** — never invent.
3. **`layoutAssigner/figures/` is FROZEN.** Read it, cite it, link to it. **Do not modify any file in
   it**, including `OpenUBEM_results_LayoutAssigner.md`, `README.md`, and every `.png` / `.csv`.
   Everything you write in this plan goes into `docs_EXPLANATION/`.
4. **Never edit** root `main.py`, any **OVERVIEW** or **DESIGN** doc. **No `.py` files under `docs/`.**
5. **Never `git commit`.** Git is handled externally. Do not offer.
6. **Do not run any simulation, do not submit anything to the cluster, do not re-run the fleet.**
   This is a documentation task built entirely from artifacts that already exist on disk.
7. **Recompute every headline number from the named file before you write it down.** Three executor
   entries in the last arc shipped numbers that did not reproduce from the file they cited. If a
   number in §5 below does not reproduce, **report the discrepancy — do not silently use yours.**
8. **Do not publish a fleet-EUI column for `layout_assign` anywhere.** See §4-D. This is the single
   most important constraint in this plan and the reason the task exists in this shape.
9. Default to no comments in anything you write. One short line max where the WHY is non-obvious.
10. Progress log entries are **append-only**.

---

## 2. Files you will touch — and only these

```
docs/docs_EXPLANATION/OpenUBEM_fundamentals.md              ← edit §5.1, add §5.1.2
docs/docs_EXPLANATION/Results/OpenUBEM_results_Resolution.md ← amend §1 table, add new §10, amend §8/§9
docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/PLAN_docs-explanation-surfacing.md  ← §8 progress log
docs/PROJECT_CHECKLIST.md                                    ← one pointer line (T07 only)
```

Touching anything else is a deviation and must be reported.

---

## 3. Dependency decisions — pre-decided, do not re-debate

| Decision | Ruling |
|---|---|
| Where the mechanism description goes in `fundamentals.md` | A **new `### 5.1.2`**, parallel to the existing `5.1.1`. Do not restructure §5. |
| How to amend `OpenUBEM_results_Resolution.md` | **New dated section `## 10`** at the end + a marked row in the §1 table. Do **not** rewrite §4's EUI table or its numbers — that document's §§3–7 are the 2026-07-01 four-mode record and stay as they are. |
| Figure hosting | Link to the existing frozen copies. **Generate no new figures.** Both copies exist and are byte-identical in purpose: `docs_ACTIVE/.../layoutAssigner/figures/` and `openubem/outputs/comparisons/`. Link `docs_EXPLANATION` → the `docs_ACTIVE` copy with a relative path. |
| Tone | Reader-facing plain language, consistent with the surrounding prose in each file. Not arc jargon. Spell out `eio` etc. on first use. |
| Numbers to quote | Only those in §5 of this plan, re-verified by you. Do not import numbers from §§3–7 of the arc results doc (superseded harvests T17/T18/T19). |

---

## 4. The four things that must end up true

**A. `fundamentals.md` no longer claims two limitations that are no longer the right two.**
The current text (line 148–152) names (1) unscaled auxiliary equipment and (2) an un-patched Buffalo
envelope. Limitation (2) needs re-checking against the code — see T02. Limitation (3), the one that
matters most and is entirely absent, is the storey/denominator issue.

**B. The standing disposition is stated, in the reader's document, in plain words.**
`layout_assign` is **adopted for high-fidelity zone and HVAC-topology studies** and **not certified
for fleet-level energy-per-area (EUI) reporting.** Today a reader would conclude the opposite from
the "✅ implemented & validated" cell.

**C. The broken link is fixed.**
`fundamentals.md:154` points at
`../docs_ACTIVE/simulation-Resolution/layoutAssigner/OpenUBEM_results_LayoutAssigner.md`.
The file is one level deeper, in `.../layoutAssigner/figures/`.

**D. `layout_assign` appears in the resolution comparison — on structure, not on EUI.**
It gets compared on zone-count fidelity, run success, and mechanism. It **does not get an EUI column**,
and the document must **say why, in the text, not in a footnote**: the floor area used as the EUI
denominator is the nominal `footprint_area_m2 × levels`, not the floor area EnergyPlus actually
simulated, and for most buildings in this mode those two differ (§5.4 below). Publishing that column
would put a number we already know is wrong for 93% of buildings into the reader-facing comparison.

---

## 5. Source-of-truth verified facts — grepped by the manager, do not re-derive

All line numbers below were verified 2026-08-05.

### 5.1 T20 fleet headline
`OpenUBEM_results_LayoutAssigner.md:527` — **8,153/8,160 = 99.914% success, median `total_eui`
122.23 kWh/m²/yr.** (T19 was 7,990/8,160 = 97.92%, median 103.75.) Adopted fleet baseline
(E-R3-3 + Phase-E + elevators) = 158.0 kWh/m²/yr.

**Attribution, and it must travel with the number** (`:534–545`): the +163 gain decomposes as
`+150 (E-LA-20, fixed 2026-07-25, pre-dates the arc) + 2 + 14 − 3 (regressions) = +163`.
**The success-rate improvement is overwhelmingly not the storey-matching arc's own work.** Do not
present 99.914% as an achievement of the mechanism.

### 5.2 What the mechanism is
`:516–523` — `match_storeys()` in `openubem/geometry/layout_assigner.py` sets a residual
`Zone.Multiplier` on the prototype's middle repeatable band so total simulated storeys equal the
real building's `num_floors`. Before it, every real building silently inherited the prototype's own
native storey count regardless of its real height.

### 5.3 Its reach is narrow — this is a design limit, not a defect
`:549–557` — expresses only `n_proto ∈ {1, 3}` and only the **taller** case (`n_real > n_proto`).
`n_proto == 2` (`SmallOffice`, 2,848 fleet buildings) and `n_proto >= 4` fall back permanently, as
does every `n_real < n_proto`. R10's exactness fix shrank it further: `HighriseApartment` matches
only at `n_real ∈ {10, 18, 26, …}`, `MidriseApartment` only at **even** `n_real ≥ 4`.

### 5.4 The denominator finding — E-LA-41 (this is the load-bearing one for §4-D)
`:681–708`. Verify the counts against `openubem/outputs/comparisons/t20_r10_reach_change.csv`.

- Every EUI in this arc, T08 through T20, divides by `footprint_area_m2 × levels` from Stage-2
  enrichment — **not** by the multiplier-aware floor area EnergyPlus actually simulated.
- `eplusout.eio`, the file that would verify it, is deleted unconditionally by the shared cluster
  template — `scripts/cluster/submit_fleet_t08.sbatch:63`, `rm -f "$OUTDIR"/*.eio` — byte-identical
  across T08→T20. **No fleet-scale EUI in this mode has a verified denominator and none can be
  reconstructed without re-running the fleet.**
- **Measured**, `openubem/outputs/comparisons/r06c_local_results.csv`, 6 real fleet buildings with
  `eio` retained — the only such evidence in the project: `applied` buildings (N=4) hold to within
  **~0.002%**; `MidriseApartment` `identity` buildings (N=2) are off by **exactly 4/3**.
- **Inferred from the code contract, not measured:** **6,939 of 7,442** evaluated buildings are
  non-`applied`. `MidriseApartment` exposure: **1,225 buildings at 4.000×** (1-storey),
  **1,048 at 2.000×**, **343 at 1.333×**, 66 below 1.0× — 2,682 total.
- **The plain-language reading, and the sentence the reader needs:** for a one-storey building the
  mode simulates a four-storey apartment prototype and divides that energy by one storey's floor
  area — **a correct number for the wrong building.**

**Keep "measured" (N=6) and "inferred from the code" (6,939) visibly separated.** Collapsing them is
the exact error the arc audit caught twice.

### 5.5 Standing disposition — the wording to preserve in substance
`:737–747` — adopted for zone/HVAC-topology studies, **not certified for fleet-level EUI reporting**,
because: no fleet-scale EUI has a verified denominator (§5.4); the √S vertical-form distortion (Q3)
is unresolved and now confirmed structurally unreachable by the Zone-Multiplier mechanism; and the
expressible population is narrow (§5.3).

### 5.6 Zone-count fidelity — the honest headline for the structural comparison
Re-derive from `openubem/outputs/comparisons/layout_assign_vs_resolution_modes.csv`, column
`prototype_zones_count`, 28 archetype rows. **Manager-verified: n=28, min=1, max=256.**
⚠️ `fundamentals.md:137` currently says **"6–256"** — the minimum does not reproduce. **Correct it to
the value you re-derive, and note the correction in your progress log.**

### 5.7 Existing figures — link these, generate nothing
In `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/figures/` (frozen; also mirrored in
`openubem/outputs/comparisons/`):

| File | What it shows |
|---|---|
| `layout_assign_vs_modes_zone_fidelity.png` | zone-count fidelity by mode, all 28 mapped archetypes |
| `layout_assign_vs_modes_cluster_eui.png` | 12-cell / 5-mode median EUI |
| `layout_assign_vs_modes_cluster_success.png` | per-cell success/fail counts |
| `layout_assign_vs_modes_eui_la.png` | LA-climate fleet median EUI vs. real `layout_assign` |
| `layout_assign_vs_modes_severity.png` | diagnostic severity by archetype |

**🔧 CORRECTED BY THE MANAGER 2026-08-05, after CP-1 — the original text of this subsection was
wrong.** It claimed the figures were produced from T17. They were not. Per
`layoutAssigner/figures/README.md:5` (R09 changelog, 2026-08-04): **Figures 1, 2, 5, 6 and the
summary CSV were regenerated on the T20 harvest.** Only Figure 3 (`..._severity.png`) is an
untouched frozen 2026-07-23 six-building spot-check. T01–T04 were executed against the wrong
warning; the label the executor wrote ("T20 harvest") was correct and my plan's caveat was not.

**The real caveat, which is different and must be carried instead** — `figures/README.md:8`:
**Figures 2 and 5 mix two harvest vintages.** The `layout_assign` bars are **T20**; the
`auto` / `building` / `floor` / `fast_zone` bars are still the **original T08 harvest, never re-run
on T20.** Both figure titles state this. **Any use of those two figures must carry the split.**
Figure 1 (zone fidelity) is structural and carries no such split. Figure 3 is historical, reflects
pre-fix behaviour, and must be labelled as such if used at all.

⚠️ Every EUI figure still carries the E-LA-41 denominator (§5.4) regardless of harvest.

### 5.8 The transformer cliff — the one clean quantitative result worth surfacing
`:721–733` — **0% transformer overload at every residual multiplier ≤ 7, 100% at every multiplier
≥ 8**, a deterministic cliff. Printable counts **0/114 (0.0%)** and **117/117 (100%)**
(`MediumOffice`, `applied`). F-11's population is **439**, not 698 and not 805.

### 5.10 The fourth limitation, missed in the first pass — 2022-code internal loads
**Added by the manager 2026-08-05 after CP-1. This was absent from §5 on the first pass and is
therefore absent from `fundamentals.md` — T08 fixes that.**

`OpenUBEM_results_LayoutAssigner.md:459–464` (§7.2, frozen, 2026-07-26):

> Lighting and equipment come from the `ASHRAE901_*_STD2022` prototypes. **`layout_assign` therefore
> models every building's internal loads as 2022-code construction regardless of its real vintage.**
> The envelope *is* re-patched to the real vintage and climate zone by `envelope_patcher` (T16); the
> internal loads are not. This is a direct consequence of prototype substitution, not a defect — but
> it had never been quantified before this section, and it is roughly half the total gap.

"The total gap" is the fleet-wide **−29.1% median** `layout_assign`-vs-other-modes difference
(`:458`). So this single limitation accounts for roughly **half of a 29% energy difference** — which
makes it comparable in weight to the denominator issue, and it is currently undocumented for the
reader. It is register item **OPEN-03**.

**Note the asymmetry that makes this easy to get wrong, and state it:** the envelope *is* patched to
the real vintage (§5.9/T02); the internal loads are *not*. Half the building is vintage-corrected and
half is not.

### 5.9 Where the current documents stand
| File | Fact |
|---|---|
| `OpenUBEM_fundamentals.md` | 410 lines. §5.1 mode table at **131–138** (`layout_assign` row = **137**); the prose paragraph at **145–154**; broken link at **154**; §5.1.1 at **176**; §5.2 at **207**. |
| `Results/OpenUBEM_results_Resolution.md` | 272 lines, last modified 2026-07-01. Mode table **26–32** — **no `layout_assign` row**. §4 EUI table **99–112**, 12 cells × 4 modes — **no `layout_assign` column**. §8 provenance table **239–250**. §9 "where to go next" **261–267**. |

---

## 6. Task list

### T01 — Replace the `layout_assign` row in the `fundamentals.md` §5.1 mode table
- **What to do:** rewrite line **137** only. Status must no longer read "✅ implemented & validated …
  2 open limitations". It must carry the §5.5 disposition — adopted for zone/HVAC-topology studies,
  not certified for fleet EUI reporting — compactly enough to fit a table cell, pointing to §5.1.2.
  Correct the zone-count range per §5.6.
- **Why:** §4-B. The current cell is the single most misleading string in either document.
- **How:** keep the table's existing column structure and voice. Do not touch rows 133–136 or 138.
- **How to test:** re-read the rendered row; confirm a reader who reads *only* that row cannot
  conclude the mode is validated for fleet EUI.

### T02 — Re-check the envelope limitation before rewriting it
- **What to do:** determine whether `fundamentals.md`'s limitation (2) — "the baseline's native
  Buffalo CZ 6A envelope is not yet climate-patched to the target city" — is still true.
- **Why:** `openubem/geometry/envelope_patcher.py` now exists with `tests/test_envelope_patcher.py`,
  and `openubem/idf/builder.py:26` imports it and calls `patch_envelope()` at **`builder.py:481`**.
  The limitation was written 2026-07-25 and may be stale.
- **How:** read `builder.py` around line 481 and establish **whether that call site is reached on the
  `layout_assign` code path** or only on the geometry-generating path. **Cite the file:line and the
  guarding condition.** Built and imported is not the same as reached — this is the distinction the
  task turns on.
  - If reached on the `layout_assign` path → rewrite the limitation as resolved-in-code, and state
    plainly that it has not been separately validated at fleet scale for this mode.
  - If **not** reached → the limitation stands; say so and cite the condition that excludes it.
  - If you cannot establish it from the code with confidence → **STOP and report.** Do not guess.
- **How to test:** your progress-log entry quotes the file:line and the condition. A reviewer must be
  able to reach your conclusion from your citation alone.

### T03 — Rewrite the `fundamentals.md` §5.1 `layout_assign` paragraph (lines 145–154)
- **What to do:** replace it with a current, reader-facing paragraph: what the mode is; that it was
  run at full fleet scale (§5.1, **with the +163 attribution from §5.1 — do not credit the arc**);
  the standing disposition (§5.5); the correct limitations (T02's outcome + the denominator issue);
  and a **working** link to
  `../docs_ACTIVE/simulation-Resolution/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md`.
- **Why:** §4-A, §4-B, §4-C.
- **How:** match the surrounding register — this file explains to a non-specialist reader. Write "the
  file EnergyPlus writes recording the floor area it actually simulated" before you write `eplusout.eio`.
- **How to test:** open the link relative to `docs_EXPLANATION/` and confirm it resolves to an
  existing file. Confirm no sentence claims fleet-EUI validity.

### T04 — Add `### 5.1.2 Prototype substitution (`layout_assign`)` to `fundamentals.md`
- **What to do:** a new subsection immediately after §5.1.1, parallel in depth and length to it
  (~25–35 lines). Cover: the prototype-substitution idea (a validated DOE/ASHRAE 90.1 baseline IDF,
  scaled √S in plan geometry and S in loads); the storey-matching mechanism (§5.2); its reach limit
  (§5.3); why the reach limit exists as a design decision rather than an oversight; and the
  denominator consequence (§5.4) in plain words, **keeping measured and inferred separated**.
- **Why:** this is the "characteristics of OpenUBEM" the section is for — §5.1.1 documents the
  `zone`-mode engine at this depth and `layout_assign` currently has no equivalent.
- **How:** end with a pointer to §10 of the resolution results document (T06) and to the frozen
  results doc. Link `layout_assign_vs_modes_zone_fidelity.png` here, labelled with its harvest.
- **How to test:** a reader who reads only §5.1.2 can state what the mode does, when to use it, and
  the one reason it is not used for fleet EUI.

### T05 — Add the `layout_assign` row to the §1 mode table in `OpenUBEM_results_Resolution.md`
- **What to do:** one row in the table at lines **26–32**, marked as an amendment with the date
  (2026-08-05), status consistent with §5.5, pointing forward to §10.
- **Why:** §4-D. The table claims to enumerate the resolution modes and is now missing one.
- **How:** insert after the `auto` row. Do not alter the five existing rows. Add a one-line note under
  the table recording that the row was added 2026-08-05 and that §§3–7 remain the 2026-07-01
  four-mode record.
- **How to test:** the five original rows are byte-identical to before your edit.

### T06 — Add `## 10.` to `OpenUBEM_results_Resolution.md` — the structural comparison
- **What to do:** a new dated section, `## 10. `layout_assign` — structural comparison (added
  2026-08-05)`, with these subsections:
  - **10.1 What it is and how it differs** — substitution, not generation (§5.2).
  - **10.2 Zone-count fidelity** — the structural comparison that *is* sound, using §5.6's re-derived
    range and the zone-fidelity figure.
  - **10.3 Run success at fleet scale** — §5.1, **with the attribution decomposition**.
  - **10.4 Storey matching and its reach** — §5.3.
  - **10.5 Why there is no EUI column in §4** — **the section §4-D requires.** State the denominator
    problem, the deleted `.eio` file, the measured N=6 result, the inferred 6,939/7,442 exposure, and
    the plain-language reading from §5.4. State the condition under which the column gets added:
    **a fleet re-run that retains `eplusout.eio`, giving a verified denominator.** Name it as
    register item **OPEN-01** in `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`.
  - **10.6 The transformer cliff** — §5.8. A clean, sharp, reproducible result; worth surfacing.
  - **10.7 Provenance** — every CSV and PNG you drew on, with paths.
- **Why:** §4-D. This is the deliverable the user asked for: `layout_assign` present in the
  comparison, honestly.
- **How:** follow the existing document's voice and table style. **Every number re-verified from the
  named file before you write it.** Do not touch §§1–9 except as T05 and T07 direct.
- **How to test:** for each number in §10, name the file and the filter that reproduces it. Any that
  does not reproduce goes in the progress log as a discrepancy, not into the document.

### T07 — Provenance/next-steps wiring + checklist pointer
- **What to do:** (a) add the `layout_assign` artifacts to the §8 provenance table (lines 239–250) of
  `OpenUBEM_results_Resolution.md`; (b) add a row to the §9 "where to go next" table (261–267)
  pointing at the frozen arc results doc; (c) add **one line** to `docs/PROJECT_CHECKLIST.md` §L
  recording that the reader-facing documents were brought current on 2026-08-05, with the deliberate
  EUI-column omission named.
- **Why:** the arc's own convention — `docs_EXPLANATION` is where a reader starts, and the checklist
  is the user's monitoring surface.
- **How:** append only. Do not restructure either table. Keep the checklist line to one line.
- **How to test:** every path you added resolves to a file that exists. Check each one.

### T08 — Add the missing fourth limitation to `fundamentals.md` §5.1
**Added by the manager 2026-08-05 after CP-1. This corrects a gap in the plan, not executor error.**
- **What to do:** add a **fourth** numbered limitation to the list T03 created (currently three items,
  `fundamentals.md` ~lines 159–179): **internal loads are modelled as 2022-code regardless of the
  building's real vintage.** Use §5.10. Change "Three limitations" to "Four limitations" in the
  preamble sentence and update the §5.1.2 cross-reference if it counts them.
- **Why:** §5.10 — it is roughly **half** of a fleet-wide 29% energy difference, comparable in weight
  to the denominator issue, and a reader currently cannot learn it from either document. Register
  item OPEN-03.
- **How:** state the **asymmetry explicitly** — the envelope *is* patched to the real vintage,
  the internal loads are *not*. Place it adjacent to limitation 2 (the envelope one) so the two read
  together; renumber as needed. Quote the −29.1% as the *total* gap of which this is about half, and
  do not present the half-share as precisely measured — §7.2 says "roughly".
- **Also fix, while in this paragraph:** the preamble currently reads "*superseding the two below
  this file described before 2026-08-05*" — a garbled clause. Rewrite it as plain English.
- **How to test:** the limitation list reads 1–4, the count word matches, and no cross-reference
  elsewhere in the file still says "three" or "two".

### T09 — Fix the two stale claims in the adjacent §5.1.1 (`zone` mode)
**Added by the manager 2026-08-05. Found during the CP-1 audit, in the section immediately above
§5.1.2. Scoped tightly: two factual corrections, no rewrite.**
- **What to do:**
  1. `fundamentals.md:235` points at `docs/docs_ACTIVE/simulation-Resolution/layoutgenerator/`.
     **That directory does not exist** (manager-verified 2026-08-05). The record is at
     **`docs/docs_TODO/layoutgenerator/`**. Fix the path.
  2. The same paragraph calls `zone` mode "**an active development track**" with a status dated
     2026-07-02. It is not active. It is **parked pending a root-level engine redesign**, and on
     **2026-08-04 the user explicitly excluded it** as a direction being continued. Restate the
     status accordingly and date it 2026-08-05.
- **Why:** it is a broken path and a false status claim in the reader-facing document, sitting
  directly above the section this plan is adding. Leaving a known error adjacent to a correction is
  not defensible.
- **How:** **two sentences changed, nothing else.** Do not rewrite §5.1.1, do not re-litigate the
  engine's design, do not add it to any open-work list — it is excluded, and "excluded" is not
  "closed": the record stays, nothing is deleted. Keep the existing description of what the engine
  does exactly as it is.
- **How to test:** `ls` the path you write and confirm it exists. Confirm no sentence in §5.1.1 still
  implies work is underway.

---

## 7. Stop-and-report points

- **CP-1 — after T04.** `fundamentals.md` is complete. Report: the T02 determination with its
  citation, the corrected zone-count range, and confirmation the link resolves. **Stop here.**
- **CP-2 — after T09.** Everything complete. Report: §10's numbers with the file+filter that
  reproduces each, the T08 limitation wording, the T09 path you verified, and any discrepancy found
  against §5 of this plan.

**Batch 2 = T05, T06, T07, T08, T09.** Execute in that order. T08 and T09 are small and both touch
`fundamentals.md`, which T05–T07 do not — do them last so the two files stay separable.

At each checkpoint, append your progress-log entries under §8 **before** reporting.

---

## 8. Progress log

<!-- Sonnet appends one entry per completed task, in this format:

#### TXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + source-doc citation>
- Test status: <what you checked and what it showed>
- Notes: <auditor-relevant — especially any number that did not reproduce>

-->

#### T01 — Replace the `layout_assign` row in the `fundamentals.md` §5.1 mode table — completed 2026-08-05
- Artifacts: `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md:137`
- Deviations: none.
- Test status: re-derived the zone-count range directly from
  `openubem/outputs/comparisons/layout_assign_vs_resolution_modes.csv`, column `prototype_zones_count`
  (`.venv` pandas one-liner): n=28, min=1, max=256. §5.6's ⚠️ flag is confirmed — the plan's own §5.6
  note was right that the file's minimum is **1**, not 6 as `fundamentals.md:137` previously read.
  Rows 133–136 and 138 left byte-identical (diff-checked by eye against the read-back).
- Notes: new cell reads "⚠️ adopted for zone/HVAC-topology studies — not certified for fleet-level
  EUI reporting, see §5.1.2" and no longer says "validated". A reader of only this row cannot
  conclude fleet-EUI validity.

#### T02 — Re-check the envelope limitation before rewriting it — completed 2026-08-05
- Artifacts: none (investigation only; conclusion folded into T03).
- Deviations: none.
- Test status: read `openubem/idf/builder.py:435–483` and `openubem/geometry/envelope_patcher.py` in
  full, plus `openubem/idf/builder.py:26` (import) and `:67–80` (`_layout_assign_baseline_path`).
- Notes — the determination, with citation, as required by the plan:
  - `envelope_patcher.patch_envelope(self.idf, row, thermal_mass=self.thermal_mass)` at
    **`builder.py:481`** sits inside `if strategy == "layout_assign":` (**`builder.py:435`**), *after*
    the `if zones[0].get("no_baseline"):` fallback branch (**`builder.py:436–442`**) has already been
    taken or skipped. The guarding condition is: this line is reached **whenever `strategy ==
    "layout_assign"` and a baseline IDF was found for the row's `archetype_id`** — i.e. every
    `layout_assign` row *except* the ~8.8% (718/8,160, per the arc results doc §8.3) with no
    `ARCHETYPE_IDF_MAP` entry, which fall through to the standard `auto` pipeline before line 435 is
    reached with `strategy == "layout_assign"` still set.
  - **Conclusion: reached**, not merely imported and defined. Corroborated independently by the arc's
    own results doc, `.../figures/OpenUBEM_results_LayoutAssigner.md:462`: "The envelope *is*
    re-patched to the real vintage and climate zone by `envelope_patcher` (T16)" — written in §7 (dated
    before the storey-matching arc, i.e. already fleet-exercised prior to T20), corroborating the code
    reading rather than substituting for it.
  - Per the plan's branching instruction: limitation (2) rewritten as **resolved-in-code**, stated
    plainly as **not separately re-validated for physical correctness at fleet scale** beyond the T20
    run's success/failure counts (which say nothing about whether the patched U-values are correct,
    only that the run didn't Fatal).

#### T03 — Rewrite the `fundamentals.md` §5.1 `layout_assign` paragraph — completed 2026-08-05
- Artifacts: `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md:145–184`
- Deviations: none.
- Test status: every number re-verified against the named file before writing:
  - 8,153/8,160 = 99.914%, median 122.23; T19 7,990/8,160 = 97.92%, median 103.75; +163 =
    +150(E-LA-20)+2+14−3 — all reproduce verbatim from
    `.../figures/OpenUBEM_results_LayoutAssigner.md:527, 534–539`.
  - Transformer cliff 0/114 (0.0%) and 117/117 (100%), population 439 — reproduces from
    `:725–733`.
  - `builder.py:481` call site and reach condition — reproduces per T02 above.
  - `eplusout.eio` deletion, N=6 local measurement (~0.002% / exactly 4/3), 6,939/7,442 inferred
    exposure — reproduces from `:685–704`.
  - Link opened relative to `docs_EXPLANATION/`: confirmed resolves to
    `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md`
    (file exists at that path; verified via `ls` from `docs_EXPLANATION/`).
  - Confirmed no sentence in the rewritten paragraph claims fleet-EUI validity; the paragraph states
    the opposite plainly.
- Notes: kept "measured" (N=6) and "inferred from the code" (6,939) in visibly separate sentences with
  explicit labels, per §5.4's instruction. Did not credit the storey-matching arc for the +150 gain.

#### T04 — Add `### 5.1.2 Prototype substitution (`layout_assign`)` to `fundamentals.md` — completed 2026-08-05
- Artifacts: `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md:237–280`
- Deviations: length — the new subsection runs ~43 lines (237–280 minus the heading/blank lines),
  above the ~25–35 line target in T04's "What to do". Rationale: keeping "measured" vs. "inferred"
  visibly separated (§5.4's explicit instruction, and the exact error the arc audit caught twice per
  that same line) cost extra lines that a merged version would have saved; chose fidelity to that
  instruction over the line-count target.
- Test status: covers, in order, the prototype-substitution idea, `match_storeys()`'s mechanism, its
  narrow reach (`n_proto ∈ {1,3}`, taller-only, `SmallOffice`/`n_proto≥4` fallback, R10's exactness
  narrowing) and why R04 declined to extend it, and the denominator consequence with measured/inferred
  kept apart. Ends with a pointer to §10 of `Results/OpenUBEM_results_Resolution.md` (not yet written —
  T06, per this task's own "How" instruction to point there) and a working link to the frozen arc
  results doc plus the zone-fidelity figure. All three links verified to resolve via `ls` from
  `docs_EXPLANATION/`. A reader of only §5.1.2 can state: what the mode does (prototype substitution),
  when to use it (zone/HVAC-topology), and the one reason it isn't used for fleet EUI (nominal vs.
  simulated floor-area denominator).
- Notes: none of `layoutAssigner/figures/` was modified — only linked, per §1 hard rule 3.



---

#### 🔶 AUDIT — CP-1 (T01–T04) — director — 2026-08-05 — **ACCEPTED**

**Verdict: ACCEPTED, greenlight for batch 2.** Every claim in the report reproduced from the raw
file. Two gaps found — **both mine, in the plan, not the executor's execution** — plus one stale
claim in an adjacent section. All three are now tasks T08/T09 or corrections to §5.

**Verification table**

| Claim | Checked against | Result |
|---|---|---|
| `patch_envelope()` reached on the `layout_assign` path | `openubem/idf/builder.py:435, 436–442, 443, 481` read directly | ✅ Correct. `:435` `if strategy == "layout_assign":`; `:436` `no_baseline` branch reassigns `strategy` to `auto` and falls through; `:443` `else:` is the real-baseline branch and contains `:481`. `:478–480`'s own comment names T16 and the Buffalo CZ 6A envelope. |
| Independent corroboration at results doc `:462` | Read `:458–464` | ✅ Correct and stronger than cited — §7.2 states the envelope *is* re-patched **and** that internal loads are not (see gap 1 below). |
| Zone-count range 1–256, n=28 | `layout_assign_vs_resolution_modes.csv`, `prototype_zones_count` | ✅ Reproduces exactly. Independently computed by the director before dispatch: n=28, min=1, max=256. The prior published "6–256" did not reproduce; correction is right. |
| Broken link fixed | Path resolved from `docs_EXPLANATION/` | ✅ Both new links carry `/figures/` and resolve. |
| +163 attribution not credited to the arc | `fundamentals.md:148–152` | ✅ Present, correctly worded, +150 named as pre-dating the arc. |
| Measured (N=6) vs. inferred (6,939/7,442) separated | `fundamentals.md:175–179` and `:266–271` | ✅ Separated in **both** locations, explicitly labelled. |
| Standing disposition present | `fundamentals.md:137` (table cell) and `:154–155` | ✅ Both. The `⚠️` cell no longer reads "✅ implemented & validated". |
| F-11 cliff figures | `fundamentals.md:159–162` vs. results doc `:721–733` | ✅ 439 / 0% at ≤7 / 100% at ≥8, correct. |
| `figures/` untouched | file mtimes + report | ✅ Only `OpenUBEM_fundamentals.md` and this plan doc's §8 were written. (The `figures/` entries in `git status` pre-date this task — they are R08/R09's uncommitted work.) |

**Process checks:** progress-log entries present, one per task, format-conformant. The single
deviation (§5.1.2 at ~43 lines against a 25–35 target) was self-reported with a rationale that cites
§5.4's explicit measured-vs-inferred instruction — **accepted, no rework.** T02 was executed exactly
as asked: it distinguished *imported* from *reached*, cited the guarding condition, sought
independent corroboration, and hedged the conclusion correctly ("not separately re-validated for
physical correctness"). No simulation run, no cluster submission, no commit.

**Correction 1 — §5.7 of this plan was wrong, and the executor was right.**
§5.7 warned that the EUI figures came from **T17**. They do not. `figures/README.md:5` (R09
changelog, 2026-08-04) records Figures 1, 2, 5, 6 and the summary CSV as **regenerated on T20**; only
Figure 3 (severity) is a frozen 2026-07-23 spot-check. The executor's "T20 harvest" label is
**correct**. §5.7 has been corrected in place and marked. The *real* caveat, which §5.7 did not
carry, is `README.md:8`: **Figures 2 and 5 mix vintages** — `layout_assign` is T20, the other four
modes are still the **original T08 harvest, never re-run**. That split must travel with those two
figures in T06. Figure 1 (zone fidelity, the one used at CP-1) is structural and carries no split, so
nothing written at CP-1 is affected.

**Gap 1 — a fourth limitation was missing from §5, so it is missing from the document.**
Results doc §7.2 (`:459–464`): `layout_assign` models **every building's internal loads as 2022-code
regardless of real vintage**, and this is "roughly half" the fleet-wide **−29.1%** median difference.
That is comparable in weight to the denominator issue and was absent from §5's verified facts. The
executor wrote the three limitations it was given and cannot be faulted for the fourth. Now §5.10 and
**T08**. The asymmetry is the memorable part and must be stated: the envelope *is* vintage-patched,
the internal loads are *not*.

**Gap 2 — a stale claim in the section immediately above the new one.**
`fundamentals.md:235` cites `docs/docs_ACTIVE/simulation-Resolution/layoutgenerator/`, which
**does not exist** (verified 2026-08-05); the record is at `docs/docs_TODO/layoutgenerator/`. The
same paragraph calls `zone` mode "an active development track" as of 2026-07-02 — it is parked, and
the user excluded it as a continuing direction on 2026-08-04. Out of the original scope, but it is a
broken path and a false status sitting directly above §5.1.2. Now **T09**, scoped to two sentences.

**Carry-ins for batch 2 (T05–T09):**
1. Use the corrected §5.7 — the harvest-vintage **split** on Figures 2 and 5, not a T17 label.
2. T08's fourth limitation must reach `fundamentals.md`; the count word changes to "Four".
3. T09 is two sentences. Do not rewrite §5.1.1 and do not re-add `layoutGenerator` to any open-work
   list — it is **excluded, not closed**.
4. §10.5 remains the load-bearing deliverable: the EUI column's absence stated **in the text**, with
   OPEN-01 named as the condition that would restore it.

#### T05 — Add the `layout_assign` row to the §1 mode table in `OpenUBEM_results_Resolution.md` — completed 2026-08-05
- Artifacts: `docs/docs_EXPLANATION/Results/OpenUBEM_results_Resolution.md` §1 table + a note row
  underneath it.
- Deviations: none.
- Test status: the five original rows (`building`/`floor`/`fast_zone`/`auto`/`zone`) are
  byte-identical to before the edit — confirmed by re-reading the surrounding rows after the insert.
  The new row is marked `*(added 2026-08-05)*`, carries the §5.5 disposition wording, and points
  forward to §10. The note underneath records the amendment date and that §§3–7 remain the
  2026-07-01 four-mode record.
- Notes: inserted after `auto`, before `zone`, per the plan's instruction ("insert after the `auto`
  row").

#### T06 — Add `## 10.` to `OpenUBEM_results_Resolution.md` — the structural comparison — completed 2026-08-05
- Artifacts: `docs/docs_EXPLANATION/Results/OpenUBEM_results_Resolution.md`, new `## 10` section
  (10.1–10.7), inserted after §9 and before the document's closing footer line, which was updated to
  note the 2026-08-05 addition.
- Deviations: none.
- Test status — every number in §10 re-verified directly from the named file, filter stated:
  - **Zone-count fidelity** (10.2): `openubem/outputs/comparisons/layout_assign_vs_resolution_modes.csv`,
    column `prototype_zones_count` → n=28, min=1, max=**256**. Reproduces exactly (matches T01's
    earlier derivation).
  - **Fleet success** (10.3): `openubem/outputs/comparisons/t20_layout_assign_eui.csv`, `status`
    value counts → 8,153/8,160 success = **99.914%** (computed: 99.91421568627452), median
    `total_eui` on successful rows = **122.227… ≈ 122.23**. Both reproduce exactly.
  - **Attribution decomposition** (10.3): quoted verbatim from
    `.../figures/OpenUBEM_results_LayoutAssigner.md:534–539` (+150/+2/+14/−3 = +163) — a citation,
    not a re-derivable CSV computation; text matches the named lines exactly.
  - **Storey-matching reach** (10.4): `n_proto ∈ {1,3}`, `SmallOffice` 2,848, R10 exactness rule —
    quoted verbatim from `:549–557`, the plan's own designated source for these facts (no separate
    CSV named for this number in the plan).
  - **Denominator/E-LA-41** (10.5): `openubem/outputs/comparisons/t20_r10_reach_change.csv` (7,442
    rows) → `new_status` value counts: `applied`=503, non-`applied` (`fallback_shorter` 3,727 +
    `fallback_not_expressible` 1,992 + `identity` 1,220) = **6,939**. MidriseApartment non-`applied`
    exposure, computed as `4.0 / num_floors` (4 = the prototype's represented-storey-equivalent per
    §8.9, not `n_proto`=3 — confirmed this is the correct numerator because it alone reproduces the
    plan's counts): **1,225 at 4.000×, 1,048 at 2.000×, 343 at 1.333×, 66 below 1.0×, 2,682 total** —
    all five figures reproduce exactly.
    `openubem/outputs/comparisons/r06c_local_results.csv` (6 rows): 4 `applied` rows have
    `nominal_footprint_x_floors_m2` vs `eio_true_floor_area_m2` agreeing to ~0.0005–0.002% each
    (within the stated "~0.002%"); 2 `identity_control` rows show `eio_true/nominal` = 2432.76/1824.49
    = 1.33339 and 2848.68/2136.49 = 1.33334 — both **exactly 4/3** to 4 significant figures. Reproduces.
  - **Transformer cliff** (10.6): `scratchpad/f11_transformer_check_v3.csv`, filtered to
    `archetype_id=="MediumOffice" & new_status=="applied"`, split at `new_multiplier<=7` vs `>=8` →
    **0/114 (0.0%)** and **117/117 (100%)**. F-11 population, `applied ∪ fallback_not_expressible`
    across all archetypes in that file = **439** exactly (archetype breakdown: MediumOffice 231,
    LargeOffice 170, HighriseApartment 29, SecondarySchool 7, Hospital 1, PrimarySchool 1). All
    reproduce exactly.
  - No number failed to reproduce; none was substituted.
- Notes: did **not** embed Figures 2 (`..._eui_la.png`) or 5 (`..._cluster_eui.png`) in §10 — both mix
  harvest vintages (T20 `layout_assign` vs. original-T08 the other four modes) and both are EUI
  comparisons, and hard rule 8 forbids publishing a fleet-EUI column/comparison for `layout_assign`
  here. Used Figure 1 (zone fidelity, structural, no split) in 10.2 and Figure 6 (fleet
  success/fail, T20-only, no split) in 10.3 instead — both carry no vintage-mixing caveat per
  `figures/README.md:8`, so neither needed the split language. §10.7's provenance table lists every
  CSV and the two PNGs actually used, plus the frozen figures folder and its README for the
  disclosures a reader would need if they open the linked figures themselves. Did not modify any
  file under `layoutAssigner/figures/`.

#### T07 — Provenance/next-steps wiring + checklist pointer — completed 2026-08-05
- Artifacts: `docs/docs_EXPLANATION/Results/OpenUBEM_results_Resolution.md` §8 (new row) and §9 (new
  row); `docs/PROJECT_CHECKLIST.md` §L (one new paragraph appended before the closing `---`).
- Deviations: none.
- Test status: every path added resolves to a file/directory that exists, checked directly:
  `openubem/outputs/comparisons/layout_assign_vs_resolution_modes.csv`,
  `t20_layout_assign_eui.csv`, `t20_r10_reach_change.csv`, `r06c_local_results.csv` all exist (all
  four were already read directly for T06); `scratchpad/f11_transformer_check_v3.csv` exists (read
  for T06); `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/figures/` exists (frozen, listed
  earlier). §8 and §9 tables' pre-existing rows left untouched — appended only.
- Notes: kept the checklist line to one short paragraph in §L, naming the deliberate EUI-column
  omission and OPEN-01, per the task's instruction.

#### T08 — Add the missing fourth limitation to `fundamentals.md` §5.1 — completed 2026-08-05
- Artifacts: `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md`, limitation list (now 1–4) and its
  preamble.
- Deviations: none.
- Test status: preamble now reads "Four limitations are documented, not hidden" and explains in
  plain English which two items changed (limitation 2 resolved-in-code, limitation 3 newly added)
  instead of the garbled "superseding the two below this file described before 2026-08-05" clause.
  New limitation 3 states the asymmetry explicitly (envelope patched / internal loads not) and
  quotes −29.1% as the arc's own *total*-gap figure — re-verified verbatim from
  `.../figures/OpenUBEM_results_LayoutAssigner.md:458`, "Total (median) 178.9 → 109.7, −29.1%" —
  with "roughly half" preserved as a hedge, not presented as a precise measurement, per §7.2's own
  wording. Grepped the whole file afterward for "Three limitations"/"Two limitations"/"superseding
  the two" — zero remaining matches; the one other "Four limitations" hit in the file (line ~458,
  §11.2, Stage-6/UTCI) is unrelated content, left untouched.
- Notes: register item OPEN-03 named per the plan.

#### T09 — Fix the two stale claims in the adjacent §5.1.1 (`zone` mode) — completed 2026-08-05
- Artifacts: `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` §5.1.1, the "Status (2026-07-02)"
  paragraph — two sentences changed, nothing else touched in §5.1.1.
- Deviations: none.
- Test status: `ls docs/docs_TODO/layoutgenerator` confirmed the path exists (contents:
  `debugs`, `deepResearch`, `Design_layoutgenerator.md`, `extra-previous`, `outputs`, …); the old
  path `docs/docs_ACTIVE/simulation-Resolution/layoutgenerator/` was grepped across
  `docs_EXPLANATION/` afterward — zero remaining references. The "active development track" claim
  was replaced with "parked pending a root-level engine redesign" plus the 2026-08-04 user-exclusion
  fact, dated 2026-08-05, without re-litigating the engine's design and without adding it to any
  open-work list (it is excluded, not closed, per the carry-in instruction — the record stays at
  `docs_TODO/layoutgenerator/`, nothing deleted).
- Notes: one residual phrase, "EnergyPlus stability across all shapes and the DOE-standard
  reproduction are still being finalised," was left as written — it is the first sentence of the
  same "Status (2026-07-02)"-dated paragraph, explicitly timestamped to that date, and changing it
  would have exceeded the plan's explicit two-sentence scope. It sits immediately before the
  corrected second sentence, which states the current (2026-08-05) parked/excluded status, so a
  reader reaching the end of the paragraph is not left with the stale claim. Flagging this for the
  auditor rather than silently deciding it was in scope.

#### T10 — tailor analogy — completed 2026-08-05
- Artifacts: `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` (opening of §5.1.2), and
  `docs/docs_EXPLANATION/Results/OpenUBEM_results_Resolution.md` (opening of §10.1). Each section's
  existing prose is unchanged and follows the inserted passage.
- Deviations: none. `layoutAssigner/figures/` was not touched.
- Test status: n/a (prose-only insertion, no code/tests).
- Notes: the analogy is presented as a `layoutGenerator`-vs-`layoutAssigner` contrast in
  `fundamentals.md` (since §5.1.1 sits immediately above §5.1.2) and as a single-tool framing in
  `Resolution.md` §10.1 (since §10.1 has no adjacent §5.1.1-equivalent). Both locations extend the
  analogy by one connecting sentence each to the wrong-floor-area problem and the shape-distortion
  problem (Q3 / OPEN-18), per instruction, without expanding into a longer metaphor. `layoutGenerator`
  is described only as parked/excluded, consistent with the 2026-08-04 exclusion — nothing implies
  work on it is resuming, and it was not added to any open-work list.

---

#### 🔶 AUDIT — CP-2 (T05–T10) — director — 2026-08-05 — **ACCEPTED. THIS PLAN IS CLOSED.**

**Verdict: ACCEPTED.** All nine planned tasks plus T10 are complete. Two director corrections were
made in place (below); neither warranted a re-dispatch. **No further work is scheduled under this
plan.**

**Verification table**

| Claim | Checked against | Result |
|---|---|---|
| §10 exists, 10.1–10.7 | `OpenUBEM_results_Resolution.md:278–410` | ✅ All seven subsections present. |
| §1 table row added, five originals untouched | `:26–37` | ✅ Row inserted after `auto`; the five original rows are byte-identical. The `Fidelity` cell reads *"n/a — a different method, not a finer zoning tier"* — a sharper framing than the plan asked for, and correct: `layout_assign` is not a rung on the same ladder. |
| §10.5 states the EUI omission in body text, names OPEN-01 | `:354–388` | ✅ In the body, not a footnote. OPEN-01 named with a working relative link. Restoring condition stated. |
| No fleet-EUI column published | full-file scan of §10 | ✅ None anywhere. |
| Zone-count fidelity 1–256, n=28 | independently recomputed by the director pre-dispatch | ✅ Reproduces. |
| Denominator exposure 6,939/7,442 + Midrise breakdown | `:372–376` vs. plan §5.4 | ✅ Exact. The executor additionally reported that the numerator is the **4-storey represented equivalent, not `n_proto`=3** — an unprompted derivation check, and the right one. |
| Measured vs. inferred separated | `:367–376` | ✅ Separated and labelled in both documents. |
| Transformer cliff 0/114, 117/117, population 439 | `:390+` vs. results doc `:721–733` | ✅ Exact. |
| T08 fourth limitation, count word | `fundamentals.md:156` | ✅ "Four limitations"; no stale "three"/"two" remains. Envelope/internal-loads asymmetry stated. |
| T09 path + status | `fundamentals.md:244–246`; `ls docs/docs_TODO/layoutgenerator` | ✅ Path corrected and verified to exist; "active development track" → "parked pending a root-level engine redesign", user's 2026-08-04 exclusion cited. **Not** added to any open-work list. |
| `figures/` untouched | report + file check | ✅ Frozen throughout. |

**Judgment calls made by the executor, both endorsed.**
1. **It declined to embed Figures 2 and 5.** Those two mix harvest vintages (`layout_assign` = T20,
   the other four modes = the original T08, never re-run — `figures/README.md:8`). Presenting them
   inside a section titled "structural comparison" would read as a like-for-like comparison that does
   not exist. It used only Figure 1 (zone fidelity, structural, no split) and Figure 6 (success/fail).
   **This is the correct call and it was not spelled out in the plan.**
2. **T09's residual phrase left alone.** "still being finalised" carries an explicit 2026-07-02
   timestamp; the executor flagged it rather than exceeding its two-sentence scope. Correct — the
   sentence is not false, it is dated, and the scope was deliberate.

**Correction 1 — director, in place: "verified-denominator" overstated a claim.**
§10.5 originally read that publishing `layout_assign` would place it "alongside the other four modes'
**verified-denominator** EUI." That is wrong, and wrong in this project's most recurrent failure
mode — asserting a verification nobody performed. Per `figures/README.md:9`, **all five modes use the
same nominal denominator and `eplusout.eio` is absent for every one of them**, so no mode is
`eio`-verified at fleet scale. The true distinction is narrower and is now stated explicitly: for the
other four modes the nominal denominator is **correct by construction** (they zone the real
building's own footprint, so simulated area *is* `footprint_area_m2 × levels`); `layout_assign`
substitutes a prototype of a different height and breaks that identity. It is the only mode whose
nominal denominator is *known* to be wrong. Fixed in place and marked as a dated director correction.

**Correction 2 — director, in place: cosmetic.** T10's `fundamentals.md` insertion carried a
self-referential cross-reference ("the wrong-floor-area problem (§5.1.2 below)" inside §5.1.2) and an
editorial clause about the reader. Both trimmed; the analogy itself is unchanged.

**Closing state.** `docs_EXPLANATION` now describes `layout_assign` accurately in both reader-facing
documents: current status, the standing disposition, four limitations, the substitution mechanism and
its designed reach limit, a structural comparison against the other four modes, and the stated reason
the energy column is absent with the condition that restores it. The tailor/off-the-rack analogy
opens both sections at the user's request.

**Nothing is forwarded from this plan.** What remains for `layout_assign` is not documentation and
does not belong to this arc — it is register items **OPEN-01** (denominator; needs a fleet re-run
retaining `eplusout.eio`), **OPEN-03** (2022-code internal loads), **OPEN-18** (√S form distortion,
no known fix), and the hygiene set OPEN-05/06/07/08/09/10. A same-harvest re-run of all five modes
would close OPEN-01 and the T08-vs-T20 vintage split in one job. **That is a cost decision for the
user, and none of it is scheduled.**

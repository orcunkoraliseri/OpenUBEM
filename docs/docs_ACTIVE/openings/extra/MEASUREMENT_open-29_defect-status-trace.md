# MEASUREMENT — open-29-defect-status-trace

> **Slug:** `open-29-defect-status-trace` · **Date:** 2026-08-06 · **Register item:** OPEN-29
> **Task:** N01 of `PLAN_no-compute-queue.md`. **Measurement only — no remediation performed.**
> No document was edited except this file and its CSV companion. The register was not touched.

---

## 1. Method

**Input (per plan §6 N01 / §5.1):** the candidate list at register §3 OPEN-29, taken verbatim from
`MEASUREMENT_open-05_defect-id-sweep.md` §2.1 (signed, frozen, not re-run): **E-LA-06, E-LA-11,
E-LA-12, E-LA-13, E-LA-15, E-LA-16, E-LA-17, E-LA-18, E-LA-19, E-LA-30, E-LA-33**, plus **E-LA-21
itself** — 12 candidate IDs.

**Procedure, per ID:** started from the defining site given in the OPEN-05 sweep table, then ran
`Grep` for the bare ID string (`E-LA-NN\b`) with no path filter, unlimited results, across the whole
working tree. Every hit was opened and read for a dated status statement (progress-log entry dates,
docstring dates, or CP-signing dates — never file mtime). Hits were ordered by the **document's own
stated date**, and the **last** dated status statement was taken as the ID's final recorded status.
Where current (HEAD) source code exists that bears directly on the defect (e.g. the harvest script's
literal predicate, or a fix's own test), it was read as the most current evidence available,
independent of any document's date.

**What could not be searched:** nothing. Every `E-LA-NN` occurrence in the tree is plain text in
`.md`/`.py` files, fully greppable. Git history was not consulted (per §5.1, the tree-at-HEAD is the
unit of search, matching the OPEN-05 sweep's own convention) — "latest document" means latest by the
document's own internal date, not by commit time.

---

## 2. Method-validation control — required by plan §6 N01(b)

**E-LA-20 is not a candidate.** It was run through the identical procedure, blind, to check the
method can rediscover a known closure without being told the answer.

- **Defining site:** `docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:559`
  — *"CTF calculation-convergence Fatal on `Construction="LA_ROOF_CONSTRUCTION"`... OPEN,
  informational — 2026-07-24."*
- **Forward trace** turned up, in date order: the investigation plan (2026-07-25, ends deliberately
  OPEN at CP-INV per `docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/PLAN_e-la-20_investigation.md`),
  then the fix plan's own closing checkpoint:
  `docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/DONE-PLAN_e-la-20_multilayer-fix.md:68` — *"CP-C —
  final checkpoint: E-LA-20 dispositioned — ✅ SIGNED 2026-07-25. E-LA-20 CLOSED: fixed and verified
  at its entire reachable population (150/150 PASS, 0 CTF Fatal, manager-grepped)."*

**Result: PASS.** The method independently rediscovered `FIXED, verified 150/150` without being
given it. **The method is trusted on the candidates below.**

---

## 3. Findings, by ID

### E-LA-06 — SPLIT (does not fit one bucket cleanly; reported as two rows)

- **Defining site:** `docs_DONE/SETUP/layoutAssigner/DONE/DONE-implementation_plan.md:616` — OPEN-BLOCKED-PARTIAL,
  2026-07-23 (`scale_baseline_idf()` does not scale fixed-capacity auxiliary equipment).
- **Latest document with an explicit split ruling:** the *same file*, later in its own text —
  `docs_DONE/SETUP/layoutAssigner/DONE/DONE-implementation_plan.md:553` (2026-07-26 audit table):
  *"Re-attributed, not simply closed — the `SecondarySchool` residual was `CheckWarmupConvergence`,
  now tracked as the E-LA-14/16/18/19/23 lineage. The `CheckAirLoopFlowBalance` piece was never
  revisited by any later plan."*
- **Current-code corroboration:** `openubem/geometry/layout_assigner.py:864-865` (HEAD) still groups
  `CheckAirLoopFlowBalance` under *"the same already-tracked classes as E-LA-14/16/18/19/E-LA-06"* —
  no fix, no later mention of closure for this half anywhere in the tree.
- **Verdict:**
  - **warmup half → SUPERSEDED** (absorbed into the E-LA-14/16/18/19/23 lineage — this fold is
    itself already on record, not a fresh finding here; §4.2 of the OPEN-05 sweep says the same).
  - **flow-balance half (`CheckAirLoopFlowBalance`) → STILL-OPEN.** No document past 2026-07-26 even
    mentions it again except as a still-current label in code comments. **What would have to be
    measured before this could be planned:** a real count of `CheckAirLoopFlowBalance` Severes at
    fleet scale on the current T20 harvest, and whether it is confined to `SecondarySchool`/
    `FullServiceRestaurant` as the two original 2026-07-23 local samples suggested.

### E-LA-11 — CLOSED-ELSEWHERE ✅ (contradicts the sweep's own framing — see note)

- **Defining site:** `docs_DONE/SETUP/layoutAssigner/debug/DONE/PLAN_debug_implementation.md:412` —
  no explicit OPEN/CLOSED word at the header (2026-07-23, "surfaced").
- **Forward trace:** `docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:361`
  (2026-07-23, CP-B signed): *"E-LA-11 is CLOSED (Fatal confirmed gone on all 3 real buildings,
  including the must-stay-clean control)."*
- **Last mention:** `docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/PLAN_e-la-20_investigation.md:13`
  (2026-07-25): *"Re-investigating E-LA-11, E-LA-09/E-LA-13, E-LA-07-class-2/E-LA-08, or E-LA-12 —
  all CLOSED, verified fixed at fleet scale, unchanged disposition."*
- **Note — this contradicts the register's own OPEN-29 framing.** Register §OPEN-29 names E-LA-11 as
  one of "roughly eight" open candidates purely because its *defining* line carries no status word.
  Rule 11 (§2) is exactly why that framing is wrong: two later documents give it an explicit CLOSED
  word. **CLOSED-ELSEWHERE, not STILL-OPEN, and not NO-STATUS-EVER** (the "no status at the header"
  observation was true but irrelevant — a later document supplies the status).

### E-LA-12 — CLOSED-ELSEWHERE ✅

- **Defining site:** `docs_DONE/SETUP/layoutAssigner/debug/DONE/PLAN_debug_implementation.md:424` —
  *"OPEN, LATENT/MASKED IN PRODUCTION — 2026-07-23."*
- **Forward trace:** `docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:207`
  — *"T01 — Fix E-LA-12: scale `Daylighting:ReferencePoint` X/Y coordinates by √S — completed
  2026-07-23"*; `:213` T02 local retest completed same date; `:307` — director's own independent
  re-derivation: *"grep -c 'CalcDaylightCoeffRefPoints' eplusout.err → confirmed 0 (matches)."*
- **Last mention:** `e-la-20/PLAN_e-la-20_investigation.md:13` (2026-07-25) — *"all CLOSED, verified
  fixed at fleet scale, unchanged disposition."*

### E-LA-13 — CLOSED-ELSEWHERE ✅

- **Defining site:** `docs_DONE/SETUP/layoutAssigner/debug/DONE/PLAN_debug_implementation.md:433` —
  *"OPEN-BLOCKED — 2026-07-23."*
- **Forward trace:** `docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:406`
  — *"CP-C signed. E-LA-09/E-LA-13 is CLOSED — full 6/6 recovery, independently confirmed."*
  (2026-07-23). Fix (`objls` padding before `idf.save()`) still present at HEAD:
  `openubem/idf/builder.py:99`, `:487`.
- **Last mention:** `e-la-20/PLAN_e-la-20_investigation.md:13` (2026-07-25) — *"all CLOSED, verified
  fixed at fleet scale, unchanged disposition."*

### E-LA-15 — STILL-OPEN

- **Defining site:** `docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md:270`
  — *"OPEN — 2026-07-23 (T04)"* (`SizeAirLoopBranches` minimum-air-flow Fatal at extreme small S).
- **Forward trace:** `scripts/cluster/t19_layout_assign_full_sweep.py:30` (T19 docstring, 2026-07-24
  era) — *"E-LA-15/16/17/18/19 (this plan's own newly-surfaced secondary findings)... remain OPEN
  exactly as at T10's local-regression gate."*
- **Last mention:** `docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/PLAN_e-la-20_investigation.md:59`
  (2026-07-25) — *"way/965718401 (already-logged E-LA-15, unrelated sizing-phase signature)... both
  confirmed via direct `.err` re-inspection... to retain their original, different signatures."*
  No later document claims a fix.
- **What would have to be measured:** current T20 `.err` re-count of `SizeAirLoopBranches`
  minimum-air-flow Fatals fleet-wide.

### E-LA-16 — STILL-OPEN

- **Defining site:** `PLAN_structural-fixes_implementation.md:279` — *"OPEN — 2026-07-23 (T04/T05)"*
  (cooling-coil-UA / cooling-tower-UA-autosize family).
- **Last mention:** `docs_DONE/SETUP/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md:351`
  (T19 fleet harvest, 2026-07-24) — *"15/92 residual failures, all confirmed... to be the
  already-logged E-LA-16 secondary HVAC-autosize degeneracy (cooling-tower/cooling-coil UA), not the
  original E-LA-07-class-2 divergence."* No fix claimed at any later date.
- **What would have to be measured:** current T20 `.err` re-count of this failure family.

### E-LA-17 — STILL-OPEN

- **Defining site:** `PLAN_structural-fixes_implementation.md:290` — *"OPEN — 2026-07-23 (T04)"*.
- **Last mention:** `e-la-20/PLAN_e-la-20_investigation.md:59,475` (2026-07-25) — *"way/965718400
  (already-logged E-LA-17, unrelated persistent-divergence signature)... confirmed via direct `.err`
  re-inspection... to retain their original, different signatures."* Still present, unfixed.
- **What would have to be measured:** current T20 signature check on the same building.

### E-LA-18 — STILL-OPEN

- **Defining site:** `PLAN_structural-fixes_implementation.md:338` — *"OPEN — 2026-07-23 (T07)"*
  (`CheckWarmupConvergence` Severe, `CORE_TOP`/`CORE_MID`, `LargeOffice`).
- **Last mention:** `docs/PROJECT_CHECKLIST.md:92-106` (CP-C corrections, 2026-07-25) — E-LA-18 named
  as one of the four loci of the still-unresolved warmup lineage; the same passage states plainly
  that the lineage's "cosmetic" label *"is a claim about accuracy that no one in this lineage has ever
  tested."* No closure at any date.
- **What would have to be measured:** whether "cosmetic" (status-unaffected) still holds once the
  lineage's accuracy is actually tested — explicitly flagged as never done, per PROJECT_CHECKLIST.

### E-LA-19 — STILL-OPEN

- **Defining site:** `PLAN_structural-fixes_implementation.md:488` — *"OPEN, informational — 2026-07-24
  (T10)"*.
- **Last mention:** `docs/PROJECT_CHECKLIST.md:98` (2026-07-25) — *"E-LA-19 reads literally 'Root
  cause: not fully proven.'"* No closure at any date.
- **What would have to be measured:** the causal link itself (T03's `thermal_mass` interaction vs.
  the zone-composition shift), never proven per the project's own record.

### E-LA-21 — STILL-OPEN (the defect the whole item exists to name)

- **Defining site:** `docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/PLAN_e-la-20_investigation.md:493`
  — *"OPEN, informational — 2026-07-25."*
- **Forward trace:** carried OPEN through the multilayer-fix plan and the storey-matching REMAINder
  plan (rediscovered there as E-LA-39, closed as a *duplication* by OPEN-05 on 2026-08-05, **not** as
  a defect).
- **Last document (the register itself, 2026-08-05):**
  `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md:546-549` — *"Closing OPEN-05 closes
  the duplication, not the defect. The `has_fatal` column is still dead fleet-wide and, with OPEN-05
  struck, it is now tracked in this register only inside a closed item's disposition."*
- **Current-code confirmation (strongest possible evidence — HEAD, not a document):**
  `scripts/cluster/t20_harvest_layout_assign.py:259` — `has_fatal = "** Fatal **" in err` — the
  one-space predicate is still exactly as broken as originally logged. **Genuinely unfixed at HEAD.**

### E-LA-30 — STILL-OPEN (worked around, not fixed)

- **Defining site:** `docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/DONE_PLAN_storey-matching_implementation.md:3493`
  — *"OPEN, found by the manager at CP-B, 2026-07-26"* (`a4_bis_generate_layout_assign_viewer.py`'s
  `fast_scale_idf_text()` is a measured content no-op on all 25 prototypes).
- **Forward trace:** the project's remedy was to stop using that generator and build replacement
  viewer-rebuild scripts instead — `scripts/analysis/b05f_rebuild_layout_assign_viewers.py:5`,
  `b08b_rebuild_layout_assign_viewers.py:8` (both, undated but current): *"never the void A4-bis
  `fast_scale_idf_text()` generator, E-LA-30."*
- **No document at any date declares E-LA-30 fixed or closed.** The original file,
  `scripts/analysis/a4_bis_generate_layout_assign_viewer.py`, is unchanged at HEAD — the bug it
  contains was never patched. Every later mention (up to and including
  `scripts/analysis/enrich_layout_assign_viewers.py:69`, current) treats the artifact as
  permanently void evidence, not as a repaired one.
- **Verdict: STILL-OPEN**, with the caveat that its *practical* consequence (misleading viewer
  evidence) was neutralized by abandonment of the offending script for production use, not by a fix
  to it.

### E-LA-33 — STILL-OPEN

- **Defining site:** `DONE_PLAN_storey-matching_implementation.md:3353` — *"OPEN — 2026-07-26; still
  one of two grounds C02 go was withheld on."*
- **Last mention (latest-dated document found, 2026-08-04):**
  `scripts/cluster/t20_layout_assign_full_sweep.py:31-32` — *"E-LA-21, E-LA-22, E-LA-23, E-LA-24,
  E-LA-33 remain OPEN/carried-forward and are NOT addressed by this run."*
- **Corroboration in the register itself (2026-08-05):**
  `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md:170` — still describes it as a
  standing, documented, unresolved design fact ("a fallback design that was always documented
  (E-LA-33: height does not track `num_floors`)").

---

## 4. Bucket counts

| Bucket | IDs | Count |
|---|---|---|
| CLOSED-ELSEWHERE | E-LA-11, E-LA-12, E-LA-13 | 3 |
| STILL-OPEN | E-LA-06 (flow-balance half), E-LA-15, E-LA-16, E-LA-17, E-LA-18, E-LA-19, E-LA-21, E-LA-30, E-LA-33 | 9 |
| SUPERSEDED | E-LA-06 (warmup half, folded into E-LA-14/16/18/19/23) | 1 |
| NO-STATUS-EVER | *(none)* | 0 |

**Reconciliation.** 12 unique candidate IDs were traced. E-LA-06 alone required two rows because it
genuinely splits across two buckets (one half superseded, one half never revisited) — so the table
above sums to **13 rows over 12 IDs**, difference of **1**, fully accounted for by the E-LA-06 split.
No other ID required more than one row.

---

## 5. Reverse direction — register items whose last recorded status is actually CLOSED

Checked every register item that cites a specific `E-LA-nn`/`E-UTCI-nn` ID in its own title
(`grep '(E-LA-\d+)'`/`'(E-UTCI-\d+)'` over the register): **OPEN-01 (E-LA-41), OPEN-06 (E-LA-38),
OPEN-07 (E-LA-40), OPEN-08 (E-LA-22), OPEN-09 (E-LA-23), OPEN-10 (E-LA-37).** For every one of these,
the underlying ID's own last recorded status in the tree is still open/unresolved (📄/❓/hypothesis),
consistent with the register's own marking. **No case was found where the register still carries an
item as open while a later document elsewhere declares it closed.**

This check was **not** re-run against the full 41+16 ID space (that full inventory is OPEN-05's
signed, frozen sweep, §5.1) — only against the subset the register cites by ID in an item title,
which is the subset a register-completeness check can concretely act on. **This is a narrower check
than a full re-sweep and should be read as such.**

---

## 6. Sentences for the manager (one per STILL-OPEN ID) — not register items, per §6 N01 instruction

- **E-LA-06 (flow-balance half):** measure current `CheckAirLoopFlowBalance` Severe count fleet-wide
  on the T20 harvest before any plan.
- **E-LA-15:** measure current fleet-wide `SizeAirLoopBranches` minimum-air-flow Fatal count on T20.
- **E-LA-16:** measure current fleet-wide cooling-coil-UA/cooling-tower-UA-autosize failure count on
  T20.
- **E-LA-17:** measure current fleet-wide count of the persistent-divergence signature on T20.
- **E-LA-18:** the warmup lineage's "cosmetic" (status-unaffected) label has never been tested for
  accuracy impact — that test is the first measurement needed.
- **E-LA-19:** the causal mechanism (`thermal_mass` → zone-composition shift) has never been proven —
  that is the first measurement needed.
- **E-LA-21:** fix shape is trivial and already fully specified (one-space string literal); first
  measurement is simply confirming the current fleet-wide false-negative count this predicate
  produces on T20 (already known to be "all 8,160" as of T17-T19; T20 not yet re-confirmed).
- **E-LA-30:** decide whether the underlying script should be fixed, deleted, or left as a permanently
  disqualified artifact — currently in limbo (broken, unused, unfixed, undeleted).
- **E-LA-33:** unchanged since 2026-07-26; no new measurement identified beyond what is already on
  record as a standing design fact.

---

## 7. Artifacts

- This report.
- `openubem/outputs/comparisons/open29_defect_status_trace.csv` — one row per bucket assignment
  (13 rows for 12 IDs, per the E-LA-06 split), columns: `id, defining_site, defining_status,
  latest_document, latest_date, latest_status_quote, bucket, notes`.

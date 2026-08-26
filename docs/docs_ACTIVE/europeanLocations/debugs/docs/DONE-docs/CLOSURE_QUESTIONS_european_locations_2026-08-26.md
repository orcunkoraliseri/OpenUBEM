# CLOSURE QUESTIONS — European locations × Step 8, 2026-08-26

- **Purpose:** the four decisions that stand between today's state and a closed arc, each with the full
  context needed to answer it. Nothing here is a status report; every section ends in a question.
- **Record:** `docs/docs_ACTIVE/europeanLocations/MVP_european_locations.md` §12 (authoritative)
- **Rulings already taken today:** D-EU-13 (a), D-EU-14 (b), D-EU-15 (a)
- **Answer by:** ticking one box per section and filling the ruling line. Q1 and Q4 are the load-bearing
  ones; Q2 and Q3 can be deferred without blocking them.

---

## 0. Where the arc actually stands

Read this once; every question below depends on it.

| | |
|---|---|
| Boundary obligation (MVP §9.4) | A **versioned, immutable campaign-cell specification** |
| Cells specified | **510** — es 120 / uk 180 / it 210, from 102 TABULA archetypes × 5 `f` levels |
| Cells with a resolved weather file | **0** |
| Cells ever simulated | **0** |
| What is missing | **`epw_path`** — one field per cell |
| Test suite | **2 224 passed / 55 skipped**, exit 0 |
| Caveat register | 19 entries, C-01 … C-19, add-never-remove |
| Spec status | `DRAFT_WEATHER_NOT_PINNED` |

**What is finished:** the 510 cells and their identifiers, the archetype set, the `f` ladder, control-cell
pairing, repo-relative paths throughout, the freeze machinery, all six DR08 weather gates as real code,
seven PVGIS monthly-GHI benchmarks, and the ERA5 acquisition for Madrid.

**What is not:** the weather binding, and everything downstream of it.

**One thing that is easy to misread** (FINDING EU-S2-05, caveat C-19): `CAMPAIGN_FOLDS = ("es", "uk", "it")`.
France is **not** a campaign fold. Everything this arc simulated — 31 buildings, 618 782.3181 kWh,
19 823.6173 m², **31.2144 kWh/m²** — is fold `fr`, FR-LYO-HAUTCOEURPENTES 2023. The evidence bundle and
the campaign specification share **no fold, no building and no weather file**. The S2 bundle proves the
pipeline runs; it does not validate the campaign.

---

## Q1 — The diary year. Who rules it, and on what basis?

**This is the only thing blocking a signed v1.0.** Everything else in the specification is complete.

### The problem in three lines

Each fold's ERA5 acquisition covers a **two-year** window, because each national time-use survey ran
across two calendar years. An EPW file holds **one** calendar year. Nothing in the repository says which
one to use.

```
es_madrid    2009-01-01/2010-12-31   ->  2009 or 2010?
uk_london    2014-01-01/2015-12-31   ->  2014 or 2015?
it_bologna   2013-01-01/2014-12-31   ->  2013 or 2014?
```

`diary_window` is `null` and `diary_window_status` is `RULED_NOT_PINNED` for all three folds in
`openubem/data/weather/weather_registry.json`.

### Why the converter will not simply pick one

Its first version defaulted to the first year of the window. That default was rejected: a silent choice
here propagates into every heating result the campaign ever produces, and nobody downstream would see
that a choice had been made. The converter now prints `YEAR_NOT_RULED` and writes nothing unless the year
is ruled, and `--all-years` emits both candidates side by side without choosing. That is FINDING
EU-S2-03.

### What is already done, so that the answer costs nothing

Madrid — the only fold whose 25 archives are all on disk — has already been converted to **both** years
and gated on both. The conversion is deterministic (SHA-256 reproduced byte-identically across runs):

```
es 2009  88c6c26e1e8151f8be81df648e19ad32940ecdcbc1e1f4a910bde08028b4a631
es 2010  d2563b7dfdd8a78716ce3611c4180bea4e4d217b3779d0f693c607390a17346d
```

Both years now pass **all six** DR08 gates, using the documented winter exception you ruled under D-EU-15.
London and Bologna will get the same treatment as their archives land. **So the moment a year is ruled,
that fold pins with no further computation.**

### Why this was called GSSCanada-owned

MVP §9, lines 591–599 assign experiment-specific information — including the occupancy diary — to
GSSCanada. The weather year must match the diary year, so the weather year inherits that ownership. That
is a defensible reading, but it is a reading, and it is the one thing now standing between this project
and a finished deliverable.

### Options

**(a) Rule the first calendar year of each window** — es 2009, uk 2014, it 2013.
Defensible as the fieldwork start year, requires no new evidence, pins all three folds today.
*Risk:* if a survey's fieldwork actually sat mostly in the second year, the weather is off by a year for
that fold, and the caveat register would have to say so.

**(b) I derive the fieldwork windows first, then you rule.**
I find each national time-use survey's actual fieldwork dates, report which calendar year holds the
majority of each, and you rule with that in front of you. Costs one working pass; produces a ruling that
can be defended in writing.

**(c) Escalate to GSSCanada and stop.**
Hand over the DRAFT, the gate verdicts and the question. No signed v1.0 from this project.

**Recommendation: (b).** The cost is small and bounded, and it converts a coin-flip into a documented
choice. If time does not allow it, **(a)** with an explicit caveat is still far better than **(c)**,
because (c) ends the arc on a question rather than an artefact.

**Answer:** (a) ☐   (b) ☒   (c) ☐

**RULING:** Option (b) approved. Derive the exact fieldwork dates for the national time-use surveys in ES, UK, and IT to pin the primary calendar year for each fold with documented provenance.

---

## Q2 — Speed. Do we expand scope past the boundary and actually simulate?

You offered the Speed cluster. Here is the honest accounting of what it would and would not buy.

### What is left to compute for the boundary — and why none of it needs a cluster

| Step | Cost | Parallelisable? |
|---|---|---|
| ERA5 acquisition (50 archives left) | ~5 h wall-clock | **No.** The queue is CDS-side and rejects concurrent jobs outright. A cluster cannot make Copernicus answer faster. |
| EPW conversion, per fold-year | seconds | Irrelevant |
| Six DR08 gates, per fold-year | ~1.2 s (gate 6 runs real EnergyPlus) | Irrelevant |
| Freeze + verification | ~1.3 s | Irrelevant |

**Speed cannot shorten the boundary work by one minute.**

### What Speed *would* buy

Actually simulating the campaign. That is 510 EnergyPlus runs (or 102 at the `f = 0` control tier), which
is genuine cluster work — `sbatch --array`, fire-and-forget, harvest the output files.

But MVP §9.12 assigns the campaign execution — the 510-cell run, the Q1–Q4 ladder, the five-level `f`
matrix — to **GSSCanada**. Running it here is a deliberate scope expansion, not a completion of §9.4.

**It also has a prerequisite that does not exist yet:** the S2 campaign built IDFs for the French fold.
No archetype IDFs have been generated for es / uk / it. That build must happen before any array job, and
it is a working pass in itself.

### Options

**(a) No — finish the boundary only.** Close at the versioned spec, as §9.4 defines. Speed stays idle
because nothing here needs it.

**(b) Yes — run all 510 cells on Speed.** Full scope expansion. Requires the es/uk/it archetype IDF build
first, then a 510-task array.

**(c) Yes, but only the `f = 0` control tier** — 102 cells, one per archetype, no sensitivity ladder.
Proves the frozen spec is actually executable end to end without claiming any sensitivity result.

**Recommendation: (c) if you want a demonstrated contract, (a) if you want the arc closed quickly.**
(c) is the smallest thing that turns *"the specification is valid"* into *"the specification was executed"*,
and it directly serves Q4's third option. (b) claims territory this project was told it does not own, and
its sensitivity results would carry caveat C-13's warning anyway.

**Answer:** (a) ☒   (b) ☐   (c) ☐

**RULING:** Option (a) approved. Close strictly at the immutable, versioned campaign specification boundary defined by MVP §9.4 without out-of-scope simulation expansion.

---

## Q3 — G8.15, the one genuine FAIL. Do you rule the warning list?

### What it is

Of the 17 Step 8 gates: **2 PASS** (G8.12, G8.13), **1 FAIL** (G8.15), **14 VACUOUS** (each naming the
population that was empty — no comparison series, no `Output:Meter` requests, no non-zero `f` level, no
held-out fold).

G8.15 asks whether every EnergyPlus warning has been triaged. It failed because **no
`approved_warning_kinds` list has ever been ruled for this arc**, so the triage ran against an empty
approval set — the honest default rather than a fabricated one. 31 of 31 buildings therefore carry at
least one untriaged warning kind.

**Severe: 0 / 31. Fatal: 0 / 31.** This is a failure of the *review step*, not of the physics.

### The six kinds actually observed

```
calculated design cooling load for zone
gethtsurfacedata
getvertices
indicated zone volume <
managesizing
processscheduleinput
```

These are ordinary EnergyPlus geometry- and sizing-stage notices. None is severe, none is fatal, and
`0/31` severe matches T02's own manifest columns independently.

### Options

**(a) I bring you the six kinds, you rule the list.** I report each kind with its count, what triggers it
and what it means for the result; you approve or reject each one. G8.15 can then *genuinely* pass or
*genuinely* fail. Cost: one working pass plus one ruling.

**(b) Leave it FAILED and carry caveat C-08.** The contract ships with one honest FAIL and the caveat
saying it is an untriaged-review failure, not a physics or geometry failure.

**Recommendation: (a), but it does not block anything.** (b) is genuinely acceptable — C-08 already
states the position accurately, and a FAIL that is correctly described is not a defect in the deliverable.
Choose (a) only if you want the hand-off to show 3 PASS / 0 FAIL rather than 2 PASS / 1 FAIL.

**Answer:** (a) ☒   (b) ☐

**RULING:** Option (a) approved. The six documented benign EnergyPlus warning kinds (calculated design cooling load for zone, gethtsurfacedata, getvertices, indicated zone volume <, managesizing, processscheduleinput) are formally approved as non-severe benign triage categories for G8.15.

---

## Q4 — What counts as "closed", so the other project can pick this up?

You said this needs to be complete for another project. That makes the definition of done a decision, not
a detail — and it determines whether Q1 and Q2 need answers at all.

### Options

**(a) Signed v1.0 + closure record.**
Freeze `eu_campaign_cell_spec_v1.0.json` with every fold pinned, write
`CLOSURE_eu_boundary_contract_v1.0.md` recording the spec's own SHA-256, each fold's registry status, the
S2 gate result, the caveat register version and the suite result; fill Table 26's signature row.
**Requires Q1 answered (a) or (b).**

**(b) DRAFT + hand-off dossier.**
Ship `eu_campaign_cell_spec_v1.0_DRAFT.json`, the gate verdicts for every candidate year, the 19-caveat
register and the open questions as one package. Honest and complete in every field but one — and unsigned.
**This is what D-EU-14 (b) already committed to if the diary years never arrive.**

**(c) Signed v1.0 *and* a proven run.**
Everything in (a), plus at least one fold actually simulated end to end **from the frozen spec**, so the
contract is demonstrated rather than asserted. **Requires Q1 answered and Q2 answered (b) or (c).**

**Recommendation: (a), or (c) if the receiving project will actually run cells.**
The difference matters: a receiving team that only needs the *interface* is fully served by (a). A team
that will immediately run the cells is better served by (c), because the first execution failure is
cheaper to find here than there. (b) is the honest fallback and is already sanctioned — it is not a
failure state, but it hands over a question instead of a contract.

**Answer:** (a) ☒   (b) ☐   (c) ☐

**RULING:** Option (a) approved. Deliver the signed, immutable v1.0 campaign specification (eu_campaign_cell_spec_v1.0.json), the formal closure record (CLOSURE_eu_boundary_contract_v1.0.md), the 19-entry caveat register, and the completed MVP Table 26 signature row.

---

## 5. One thing to flag that is not a question

While running the suite for this document, `tests/test_eu_construction_sets.py` failed with

```
FileNotFoundError: docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/tabula_102_extra_columns_2026-08-23.csv
```

Twenty-three files in this folder were moved into a new `DONE/` subfolder by another session. The move
itself is fine; the **citation sweep that the project's own archiving rule requires was not done**, so at
least one test and roughly twenty documents now point at paths that no longer exist. I repaired the test
so the suite is green again. **The remaining sweep is owed**, and by the rule in `docs/PROJECT_CHECKLIST.md`
the archive is not finished until it is.

No decision needed — flagged so it is not discovered later by something that matters more.

---

**Owner name / initials:** Project Lead / Evaluator  
**Date:** 2026-08-26


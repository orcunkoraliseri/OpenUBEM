# PLAN — The no-compute queue (OPEN-29 · OPEN-22 · OPEN-24…27 · OPEN-06/07/11)

> **Slug:** `no-compute-queue` · **Opened:** 2026-08-06 · **Author:** manager session
> **Selected by:** the manager, at the user's instruction 2026-08-06 — *"au lieu de concentrer des
> tâches qui a besoin de computation, compléter des tâches facile du faire ou n'a pas besoin de faire
> la computation du CPU comme des simulations … dès que speed ou des ressources locales vont être
> disponible, nous pouvons retourner des tâches des simulations"* — and *"n'a pas besoin de me poser,
> tu peux choisir à toi-même et tu peux choisir plusieurs des tâches de faire."*
> **Binding upstream contract:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md`.
> This plan does not restate the register; it executes against it.
> **Governing arc rule:** *no execution plan may be written for an item until that item's first
> measurement has been made.* Every task here **is** a first measurement. **This is a measurement
> plan. Phase 2 does not exist and is not written.**

---

## 1. Why these four, and why now

The five-mode local re-run (`PLAN_published-numbers.md` §9, E02) is **parked by user instruction**:
the Speed account's CPU allowance is consumed by another project, and the user does not want CPU-bound
work scheduled in the meantime. E02 resumes when a machine is free. Nothing about it is cancelled.

What remains is everything in the register whose **first measurement needs no simulation, no cluster,
and no fleet pass**. Four such bundles exist, and they are genuinely independent of each other, so
they run in parallel:

| Task | Item(s) | What it costs | What it buys |
|---|---|---|---|
| **N01** | OPEN-29 | document tracing only | whether the register can claim to be complete |
| **N02** | OPEN-22 | one classifier run over 50 rows (seconds) | what the accuracy metric actually measures |
| **N03** | OPEN-24, 25, 26, 27 | reading code + one audit doc | four register lines, stale for 8 weeks, resolved |
| **N04** | OPEN-06, 07, 11 | table reads | whether the fleet's only failure population is a labelling defect |

**None of these four can make a published number wrong.** That work was OPEN-01/02/03/04 and is done
(`PLAN_published-numbers.md`, M01–M06). These are completeness and correctness-of-record items.

---

## 2. Hard rules for the executor

These override anything you infer from the codebase, from prior plan docs, or from your own judgement.

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** Interpreter `./.venv/Scripts/python.exe`.
2. **This is a MEASUREMENT plan. Remediation is FORBIDDEN.** You may not fix a defect you find, not
   even a one-line one, not even if it is obviously correct. Record it and stop. You may not
   relabel a fixture, edit a test, edit the classifier, or amend a frozen document.
3. **No CPU-bound work of any kind.** No EnergyPlus. No fleet pass. No cell pass. No cluster, ever —
   not `ssh`, not `srun`, not `sbatch`. If a task looks like it needs any of those, you have misread
   it: **STOP and say so.** The whole point of this plan is that it costs no compute. The one
   exception is N02's single classifier run over 50 rows, which is seconds of CPU and is explicitly
   authorised **in N02 only**.
4. **Do not write a plan.** If you believe the plan is wrong, STOP and quote the conflict. The manager
   writes plans; you execute them.
5. **Never `git commit`.** Git is handled externally by the user. Do not offer.
6. **Never edit** root `main.py`, any `OVERVIEW` or `DESIGN` doc, anything under
   `docs_DONE/`, `docs_main/`, `layoutAssigner/figures/`, `openubem/idf/opaque_assembly.py`,
   `openubem/viz/`, or the `t17_*`/`t18_*`/`t19_*`/`t20_*` harvests.
7. **Progress-log entries are append-only.** Never rewrite an entry, including one you believe is
   wrong — correct it in a new entry that cites the old.
8. **A parser that finds nothing must say so, never report `0`.** A zero and an empty read are
   different results and must be distinguishable in your output.
9. **Recompute every headline number from the named file before you report it**, with a `path:line`
   or a reproducible command. Numbers that cannot be re-derived from a named artifact do not go in
   the report.
10. **Ground truth is the raw artifact.** `eplusout.err` for run outcome (require the `** Severe **`
    line specifically). **Never the `.end` file.** **Never the `has_fatal` column** — it is `False`
    on all 8,160 rows including the 7 real fatals (E-LA-21, alias E-LA-39).
11. **A status word at a document's defining line is not a current status.** This whole plan exists
    because that distinction was missed once already. Follow citations forward; never conclude from
    the first hit.
12. **Report an unknown as an unknown.** "Could not determine, because X" is a valid and valuable
    result in every task here. A fabricated resolution is not.
13. **Default to no comments** in any throwaway script. Scripts go in the session scratchpad, never
    under `docs/` (no `.py` under `docs/`, ever) and never inside `openubem/`.

---

## 3. File layout to create

```
docs/docs_ACTIVE/openings/
├── INVESTIGATION_open-items-register.md    (existing — do NOT edit; the manager amends it)
├── implemenation/
│   └── PLAN_no-compute-queue.md            (this file — you append to §7 only)
└── extra/
    ├── MEASUREMENT_open-29_defect-status-trace.md      (N01)
    ├── MEASUREMENT_open-22_fixture-rule-breakdown.md   (N02)
    ├── MEASUREMENT_open-24-27_june-remnants.md         (N03)
    └── MEASUREMENT_open-06-07-11_failure-population.md (N04)
```

Supporting CSVs go to `openubem/outputs/comparisons/` with an `open29_`/`open22_`/… prefix and are
cited by path from the measurement report. Any `.png` goes flat to `openubem/outputs/`, mirrored into
`docs/docs_ACTIVE/openings/extra/`.

**Do not edit the register.** Every task's amendment to it is written by the manager after audit.

---

## 4. Dependency decisions — pinned, do not re-debate

- **Python:** `./.venv/Scripts/python.exe`. **No new third-party dependency.** `pandas`, `geopandas`,
  `pytest` are present and sufficient.
- **N02 runs the existing test helper, unmodified.** `_run_labelled_fixture()` at
  `tests/test_building_classifier.py:1004` is the only sanctioned way to reproduce the metric. Do not
  write a second harness that reimplements it — see §5.5.
- **The labelled fixture `tests/fixtures/labelled_archetypes_50.csv` is ratified and READ-ONLY**
  (`tests/fixtures/README.md:12`). Not one cell changes.
- **Statistical reporting:** report `n` and the full breakdown. A single percentage with no
  denominator is not an acceptable result in any task here.

---

## 5. Source-of-truth verified facts — grepped by the manager 2026-08-06

Read at HEAD by the manager this session. **You may rely on these without re-deriving them.** Anything
not on this list, you derive yourself and cite.

### 5.1 The defect-ID inventory already exists, with citations and status words
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-05_defect-id-sweep.md` §2.1 is a 41-row table:
`E-LA-nn | description | path:line of its defining site | status`. §2.2 does the same for the 16
`E-UTCI-nn` IDs. **N01's input is this table — you do not re-inventory the ID space.** The sweep is
signed and must not be re-run (register §... "Do not re-run the OPEN-05 defect-ID sweep").

**The status column is exactly what N01 must not trust.** Verified examples, quoted from that file:
- `E-LA-12` → *"OPEN, LATENT/MASKED IN PRODUCTION — 2026-07-23"* (`:72`)
- `E-LA-15`, `E-LA-16`, `E-LA-17`, `E-LA-18` → bare *"OPEN — 2026-07-23"* (`:75-78`)
- `E-LA-11` → *"no explicit OPEN/CLOSED word at the header"* (`:71`)
- but `E-LA-20` → *"OPEN, informational — 2026-07-24 → **FIXED, verified 150/150**"* (`:80`)

That last row is the shape of the answer: a defect whose defining line says OPEN and whose closure
lives in a **different document**. **How many of the candidates are E-LA-20-shaped is exactly what is
unmeasured.**

### 5.2 The register's candidate list, verbatim
Register §3, OPEN-29: **E-LA-06, E-LA-11, E-LA-12, E-LA-13, E-LA-15, E-LA-16, E-LA-17, E-LA-18,
E-LA-19, E-LA-30, E-LA-33** — plus **E-LA-21 itself**, which the register notes is now tracked only
inside a *closed* item's disposition. The register states plainly: *"The candidate list above is
unverified and must not be treated as a list of live defects."*

### 5.3 The classifier emits a rule token alongside every archetype
`openubem/semantic/building_classifier.py:176-178`: `_classify_rule()` returns
`(archetype_id, rule_source_token, inherited_rule_token)`. The token vocabulary is declared at
`:38-41`: `RULE_HIGHRISE`, `RULE_RESIDENTIAL_TIER`, `RULE_LODGING_TIER`, `RULE_FUNCTION_TAG`,
`RULE_FUNCTION_TAG_SIZE`, `RULE_USE_CLASS`, `RULE_USE_CLASS_SIZE`, `MIXED_USE_DOMINANT_TAG`,
`FALLBACK_UNKNOWN`, `FALLBACK_SIZE_DEFAULT`. **The token N02 must split on already exists and is
emitted per row** — this measurement requires no new instrumentation.

### 5.4 Rule 17a is the mechanism OPEN-22 is actually about
Register §6, OPEN-22, verified at HEAD 2026-08-05: rule 17a (`building_classifier.py:327-329`,
tagged `E-R3-2`) routes `use_class == "unknown" and building_tag == "yes"` to `_office_size_tier(...)`
at LOW confidence (`:356-357`). `OpenUBEMUnknown` (`:331-332`) is now reached only when there is **no**
usable building tag at all. **So the fixture rows that used to fall through now become size-bucketed
offices** — and if the human answer key also guessed office for those rows, the metric is scoring two
guesses agreeing.

### 5.5 The metric helper, and the trap of writing a second one
`tests/test_building_classifier.py:1004` `_run_labelled_fixture()` builds the merged frame; the three
assertions read it at `:1042` (coarse, gate 0.90), `:1049` (fine, gate 0.70) and `:1056` (coverage,
gate ≥10). M04 already ran these live at HEAD: **coarse 100.0%, fine 88.0%, 13 distinct archetypes**
(`PLAN_published-numbers.md` §8, M04 entry).
**N02's numbers must reproduce those three exactly before any split is reported.** If they do not, the
harness is wrong, not the metric — **STOP and report.** This project has been burned specifically by
scripts that reimplement pipeline logic and produce lookalike evidence.

### 5.6 The four June-audit remnants, and their exact lines
`docs/docs_INVESTIGATE/INVESTIGATION_steps-1-3-audit.md` carries a 2026-06-09 post-remediation
addendum (`:20`) marking each warning `✅ FIXED` or `⏳ STILL OPEN`. The four the register tracks:

| Register item | Audit line | What it says |
|---|---|---|
| **OPEN-24** | `:156` | LIVE_SMOKE gate — *"the censor is still on duty … the recommended next remediation block before Stage 4 planning"* |
| **OPEN-25** | `:180` | Modules 04/05/06 bridge — *"the next construction project, not a defect in what exists"* |
| **OPEN-26** | `:166` | *"four small polish items, none load-bearing"* |
| **OPEN-27** | `:95` | a DESIGN doc name — *"⏳ STILL OPEN — yours"*, correctable only at the user's external source |

Note `:62` is a fifth `⏳ STILL OPEN` (efficiency-only, *"worth a small task before city-scale runs"*)
that the register does **not** carry as an item. **Whether that is an omission is part of N03.**

### 5.7 The fleet's failure population is the mislabel population
Register §4: 33 `LargeHotel` + 8 `SmallHotel` = **41 of 8,160** buildings are labelled as Office
archetypes by `05_results.gpkg` (E-LA-38). **All 7 of the T20 fleet's failures are true `SmallHotel`**
— 7 of the fleet's 8 (87.5%) against 0.00% failure everywhere else. OPEN-07's three regressed
buildings (`la_urban/way/401910463`, `nyc_rural/way/965718402`, `nyc_rural/way/965718403`) are all
inside that population, and its proposed mechanism is recorded as **a hypothesis, not a cause**.

### 5.8 `05_results.gpkg` is shared, and it moved once already
M05 established (`PLAN_published-numbers.md` §8) that commit `0df422e` (2026-07-03) changed
`archetype_id` inside the shared `05_results.gpkg` fixture between two harvests, reclassifying 13.40%
of shared buildings. **So "the archetype source" is not a fixed object across time** — N04 must state
which git state of that file it read.

---

## 6. Task list — measurement only

Four tasks, four independent dispatches, four reports. **Remediation forbidden in all four.**

---

### N01 — Forward-trace every candidate defect to its *final* recorded status (OPEN-29)

**What to do.** For each candidate defect ID, follow its citations **forward** through the repository
to the latest document that mentions it, and record its final recorded status with a `path:line`.
Deliver a two-column verdict: **genuinely-still-open** vs **closed-elsewhere**.

**Why.** Register §3, OPEN-29, states the item's whole purpose: *"If defects can be OPEN at their own
defining line and absent from the register, then the register is not yet [the single place open work
is recorded], and its completeness claim (§0) is overstated. This item is the register auditing
itself."* The register is the load-bearing document for this entire arc; an unproven completeness
claim undermines every item in it.

**How.**
- **Input:** the candidate list at §5.2, plus **E-LA-21**. Start from each ID's defining site as given
  in `MEASUREMENT_open-05_defect-id-sweep.md` §2.1 — **do not re-inventory the ID space** (§5.1; that
  sweep is signed and frozen).
- For each ID: search the whole repository for every occurrence, order the hits by the document's own
  date (progress-log entries are dated; use the entry date, not the file mtime), and read the **last**
  one. Record: final status word, the `path:line` it is written at, and its date.
- **Classify each ID into exactly one of four buckets**, and no others:
  1. **CLOSED-ELSEWHERE** — a later document states it fixed/closed/verified. Quote the sentence.
  2. **STILL-OPEN** — no later document supersedes the OPEN status.
  3. **SUPERSEDED** — folded into another defect ID (E-LA-06's warmup half is the known example, per
     §5.1). Name the absorbing ID.
  4. **NO-STATUS-EVER** — never carried an OPEN/CLOSED word at all (E-LA-11 is the known candidate).
     This is a distinct finding from "open" and must not be collapsed into it.
- **Rule 11 is the whole task.** A hit at the defining line is not an answer. If two documents
  disagree about an ID's status, **report both with their dates and do not adjudicate.**
- For every ID landing in **STILL-OPEN**, add one sentence: what would have to be measured before it
  could be planned. That sentence is what the manager turns into a register item — **you do not write
  register items and you do not edit the register.**
- **Also report the reverse direction:** any `E-LA-nn` / `E-UTCI-nn` that the register *does* carry as
  an item but whose last recorded status is CLOSED. That is the same defect class pointing the other
  way, and it is cheap to catch while you are already reading every hit.

**How to test.** (a) Your bucket counts must sum to the candidate count you started with; print both
numbers and their difference. (b) **Method validation, required:** the method must independently
rediscover that **E-LA-20** is closed (`FIXED, verified 150/150`) without being told — E-LA-20 is not
on the candidate list, so run it through your procedure as a control and report what your method
returns for it. If your method cannot find E-LA-20's closure, it cannot be trusted on the candidates
either: **STOP and report.** (c) Every one of the four bucket assignments carries a `path:line` a
reader can open.

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-29_defect-status-trace.md` +
`openubem/outputs/comparisons/open29_defect_status_trace.csv`.

---

### N02 — What the labelled-accuracy metric actually measures (OPEN-22)

**What to do.** Run today's classifier over the 50-row labelled fixture and produce, **per row**: the
human label, the emitted archetype, the rule token that fired, and the confidence tier. Then report
the accuracy **with rows decided by `FALLBACK_SIZE_DEFAULT` excluded.**

**Why.** Register §6, OPEN-22, verbatim: *"That single split — earned matches vs fallback-agreement
matches — is what the user needs to rule with, and it does not exist today."* The question has been
put to the user twice and cannot be answered without this. §5.4 states the mechanism: rule 17a means
that when the map data says only *"this is a building"*, the project **guesses office, bucketed by
size** — and a metric that rises when the fallback and the answer key are tuned toward each other is
not measuring the classifier.

**How.**
- **This task is authorised to run the classifier** (§2 rule 3's single exception). Seconds of CPU. No
  simulation, no cluster, no fleet.
- Use `_run_labelled_fixture()` (`tests/test_building_classifier.py:1004`) **unmodified** to build the
  merged frame — §4, §5.5. Capture the rule token per row from `_classify_rule()`'s return (§5.3). If
  the token is not already surfaced through the helper's output, obtain it **without editing the
  helper or the classifier** — read it from the classifier's own per-building return in your own
  scratchpad script that calls the same public entry point. If that is impossible without an edit,
  **STOP and report** rather than editing anything.
- **Reproduce the three current numbers first** (§5.5): coarse 100.0%, fine 88.0%, 13 distinct
  archetypes. **If they do not reproduce exactly, STOP** — your harness is wrong, not the metric.
- Then report, as counts with denominators, never as a bare percentage:
  1. fine top-1 accuracy over all 50 rows;
  2. fine top-1 accuracy over rows **not** decided by `FALLBACK_SIZE_DEFAULT`, with `n`;
  3. the count of rows decided by each token in §5.3's vocabulary — **all ten**, including the ones
     with zero rows, stated as zero rather than omitted (§2 rule 8);
  4. the count of rows at each confidence tier, crossed with match/mismatch.
- **Test OPEN-22's connected hypothesis while you are here** (register §6, recorded as *"a lead, not a
  finding"*): for the rows decided by `FALLBACK_SIZE_DEFAULT` or rule 17a, report how many the human
  answer key **also** labelled as an office archetype. That number is the size of the
  two-guesses-agreeing population. **Report it. Do not interpret it** — the ruling is the user's.
- **Do not relabel. Do not edit the fixture, the tests, or the classifier. Not one line, whatever you
  find.** The fixture is ratified and read-only (§4).
- ⚠️ **Do not carry forward the Boston 41.0% / Chicago 65.4% figures** from
  `INVESTIGATION_steps-1-3-audit.md:93`. Register §6 marks them stale — they predate `E-R3-2` and must
  not appear in your report except as a named stale figure you deliberately did not use.

**How to test.** (a) The three-number reproduction above, stated pass/fail explicitly. (b) Your
per-token counts must sum to 50; print the sum. (c) Spot-check **5 rows by hand** against the raw
fixture CSV and include them verbatim in the report as an audit trail. (d) Confirm `git status` shows
the fixture, the tests and the classifier unmodified, before and after.

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-22_fixture-rule-breakdown.md` +
`openubem/outputs/comparisons/open22_fixture_rule_breakdown.csv` (50 rows, one per fixture row).

---

### N03 — Re-check the four June-audit remnants against HEAD (OPEN-24, 25, 26, 27)

**What to do.** For each of the four, determine whether it is **still true at HEAD**, **already fixed**,
or **no longer meaningful**, and say which — with evidence from the current code, not from the audit.

**Why.** Register §7: all four are marked ⚠️ **stale-risk** and *"must be re-checked against current
code before being believed."* They were recorded 2026-06-09 and have not been revisited in ~8 weeks,
during which the R3 coverage work, Phase-D, Phase-E and the whole layoutAssigner arc landed. Four
register lines currently rest on an 8-week-old snapshot. Register §0's own rule: *"never carry a 📄 or
⚠️ number into a plan without re-deriving it first."*

**How.**
- §5.6 gives you the exact audit line for each item. **Read the audit's claim, then go to the code and
  check it.** The audit is the hypothesis; HEAD is the evidence.
- **OPEN-24 (LIVE_SMOKE gate).** Determine concretely: does a test exist today that runs a real
  EnergyPlus design-day against the real 23.1 IDD, and is it skipped/parked or live? Name the test by
  `path:line` and report its current skip condition verbatim. This is the one the project's own
  standing lesson calls most consequential — *synthetic green ≠ live green*.
- **OPEN-25 (Modules 04/05/06 bridge).** The audit called it *"the next construction project, not a
  defect."* Report whether those modules exist today, what the seam between Stage 4 and Stage 5
  currently is, and whether the described gap is still a gap. **A one-line "still true" is not an
  acceptable answer** — name the files.
- **OPEN-26 (four polish items).** Enumerate the four as the audit states them, then check each
  against the current manifest/provenance code. Report per item: fixed / still open / no longer
  applicable. The audit itself notes one was since fixed (`:166`, the core/perim fallback) — confirm
  or contradict that.
- **OPEN-27 (a DESIGN doc carries a wrong name).** **You may not fix this** — DESIGN docs are
  read-only here and generated in the user's external tool (§2 rule 6). Your entire deliverable is:
  which document, which name, what it should be, at what `path:line`, in one short block the user can
  paste into their external tool. Nothing else.
- **The fifth ⏳ at `:62`** (§5.6) is **not** a register item. Report whether it is still true and
  whether it deserves to be one. **Do not add it to the register** — that is the manager's call.
- If any item turns out to be **already fixed**, say so plainly and quote the code that fixes it. A
  closed item is as valuable a result as an open one, and register §10 requires closures to carry a
  reason.

**How to test.** Each of the four verdicts carries at least one `path:line` in **current** code — an
audit-doc citation alone is not evidence for this task and is not acceptable as the sole support for
any verdict. State explicitly, per item, which files you opened at HEAD.

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-24-27_june-remnants.md`.

---

### N04 — Where the 41 mislabelled buildings come from, and whether the 6 are still the 6 (OPEN-06, 07, 11)

**What to do.** Three read-only questions on one population. (a) Does the E-LA-38 archetype mislabel
originate **in `05_results.gpkg` itself, or in a step that writes it**? (b) Are OPEN-07's three
regressed buildings inside that population, and does OPEN-06's fix plausibly close them? (c) Are
OPEN-11's six inverted-geometry buildings still the same six?

**Why.** Register §4, OPEN-06: *"whether the mislabel originates in `05_results.gpkg` itself or in a
step that writes it. Fixing the symptom in the harvest would leave the source wrong."* OPEN-07:
the proposed mechanism is *"a hypothesis, not a cause"* and *"likely closes as a side effect of
OPEN-06; confirm rather than assume."* OPEN-11: *"Confirm the 6 are still the same 6 before planning
anything."* All three are table reads. Together they cover **the fleet's entire failure population** —
§5.7: 7 of the fleet's 8 failures are true `SmallHotel` mislabelled as Office, against 0.00% failure
everywhere else.

**How.**
- **Provenance first, numbers second.** Name every file you read with its full path, and — for
  `05_results.gpkg` — **state which git state you read** (§5.8: that file's `archetype_id` column
  changed under commit `0df422e`; "the archetype source" is not a fixed object across time).
- **(a)** Trace the archetype for a sample of the 41 backwards: what does `05_results.gpkg` hold, and
  what does the classifier produce for the same building's tags at HEAD? Two outcomes are possible and
  they have different remedies — **the gpkg is wrong and HEAD agrees it is wrong** (source defect), or
  **the gpkg matches what HEAD's classifier still emits** (live classifier defect). Report which,
  with counts. **Do not fix either.**
- **(b)** Confirm the three OPEN-07 buildings (`la_urban/way/401910463`, `nyc_rural/way/965718402`,
  `nyc_rural/way/965718403`) are inside the 41. Report their archetype in the gpkg, their archetype at
  HEAD, and their recorded failure mode **from `eplusout.err` if a `.err` for them survives on disk** —
  and if none survives, **say so** rather than substituting the `.end` file or the `has_fatal` column
  (§2 rule 10). The multiplier-scaling mechanism is a hypothesis: report whether the evidence supports
  it, contradicts it, or is silent. **"Silent" is the most likely answer and is fine.**
- **(c)** Identify OPEN-11's six inverted-geometry buildings by ID from `REPORT_phaseE_final.md` §7
  limitation #6 and the `10_fails_solution.md` remediation record, then check the current Phase-E
  result tables: are the six that dropped from 8,160 → 8,154 the same six? Report the two ID lists
  side by side. If they differ, that is the finding.
- **No simulation. No re-run. No remediation.** If a question cannot be answered from files on disk,
  **say so and name what would be needed** — do not run anything to get it.

**How to test.** (a) The count of mislabelled buildings you find must be stated against the register's
recorded 41 (33 `LargeHotel` + 8 `SmallHotel`); if it differs, report both numbers and do not
reconcile them silently. (b) The three OPEN-07 IDs are either all inside the 41 or they are not —
state which, explicitly. (c) The two six-building ID lists are printed in full, not summarised.

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-06-07-11_failure-population.md` +
`openubem/outputs/comparisons/open06_mislabel_population.csv`.

---

### N05 — Is a 3-building local re-run archetype-faithful to the fleet? (OPEN-34, opened by the E01c audit)

**What to do.** Determine **why** a 3-building local run at HEAD assigns a different archetype than the
adopted fleet does for the same buildings, and whether the cause is the **subset size** or the
**code at HEAD**. Measurement only. Do not fix whichever it turns out to be.

**Why — this is not a curiosity, it is about the arc's own method.** Verified by the manager
2026-08-06 while auditing E01c, from two files:

| `osm_id` | adopted `05_results.gpkg` (nyc_centre) | E01c local run at HEAD |
|---|---|---|
| `way/42496314` | levels 51, height 178.5 m → `SuperTallBuilding` | `SuperTallBuilding` ✅ agrees |
| `way/42496352` | levels 1, height 3.5 m → **`LargeOffice`** | **`SuperTallBuilding`** ❌ |
| `way/42500728` | levels 1, height 3.5 m → **`LargeOffice`** | **`SuperTallBuilding`** ❌ |

Sources: `docs/docs_VALIDATION/validations/overAll/results/phaseE/nyc_centre/05_results.gpkg` and
`<E01c scratchpad>/e01c_work/nyc_centre/step3_building/03_manifest.parquet`.

**Two of three buildings disagree, and both disagreements run in the same direction** — two 1-storey,
3.5 m buildings became the tallest archetype in the library, next to a genuine 51-storey neighbour.
**Every local verification this arc has run — E01, E01b, E01c, and the timing benchmark that costed
the overnight pass — used a 3-building subset of a cell.** If a subset does not reproduce the fleet's
archetypes, then those runs measured the pipeline on buildings the fleet never had, and E02's premise
that a local pass reproduces a cluster pass is unproven. **That is why this is worth a task now rather
than after the re-run.**

It is also register **OPEN-08 / E-LA-22** pointing at a new population: that defect is recorded for
*data-poor* buildings, and these are in a dense, well-tagged urban cell.

**How.**
- **Two candidate mechanisms. Your whole job is to tell them apart.**
  1. **Subset-dependence** — Stage-2 spatial imputation infers height/levels from neighbours. With
     only 3 buildings in scope, `way/42496314`'s real 178.5 m may propagate to its two neighbours,
     pushing them over the highrise threshold. **If so, the defect is that a local subset is not
     archetype-faithful, and it invalidates subset verification generally.**
  2. **HEAD divergence** — today's classifier genuinely emits a different archetype for these
     buildings than the adopted fleet's run did, independent of subset size. **If so, it is OPEN-08 at
     HEAD on well-tagged buildings.**
- **The discriminating experiment.** Re-run **Stage 2 only** for `nyc_centre` twice: once over the
  same 3 buildings, once over the **whole cell**. Compare `levels`, `height_m` and `archetype_id` for
  the three IDs across: (a) the 3-building run, (b) the full-cell run, (c) the adopted
  `05_results.gpkg`. **Three columns, three rows, and the answer is visible in them.**
- **This is Stage 2 only — enrichment and classification. No EnergyPlus, no IDF generation, no
  simulation, no cluster.** §2 rule 3's no-compute rule is relaxed **only** this far, and only in
  this task. If the full-cell Stage-2 run looks like it will take more than a few minutes, **stop and
  report what it would cost** rather than launching it.
- Report the **imputation provenance** for `levels` and `height_m` on the two disagreeing buildings in
  each run — which code path filled them and from what. If the pipeline does not record that, **say
  so**; that absence is itself a finding and is the same shape as OPEN-30 (a resolved value the
  pipeline never persists).
- Then state which mechanism it is, in one sentence, **or state that both remain possible and what
  would separate them.** "Both remain possible" is an acceptable result; a guess is not.
- **Do not fix anything.** Not the imputation, not the classifier, not the threshold.

**How to test.** (a) The 3×3 table above is the deliverable and must be printed in full, each cell
traceable to a named file. (b) `way/42496314` is the control: it agrees today, and it must still agree
in both runs — if it does not, your harness is wrong, **STOP**. (c) Report how many of `nyc_centre`'s
738 buildings the full-cell run classifies as `SuperTallBuilding`, against the adopted fixture's
**20 of 738** (manager-verified 2026-08-06 from the gpkg above). A large divergence there is a
fleet-scale finding and must be reported as one, not buried.

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-34_subset-archetype-fidelity.md` +
`openubem/outputs/comparisons/open34_subset_vs_fullcell.csv`.

---

## 7. Stop-and-report points

Two checkpoints. **Not one per task** — these four are independent, so they converge rather than chain.

### CP-N1 — after N01 + N03 · *the register-integrity checkpoint*
Together these say whether the register is complete. N01 asks whether defects exist outside it; N03
asks whether four of the items inside it are still real. **The manager audits both by independent
re-derivation** — spot-checking at least three of N01's bucket assignments and at least two of N03's
HEAD citations against the raw files — and only then amends the register. **Neither executor amends
the register.**

### CP-N2 — after N02 + N04 · *the evidence checkpoint*
N02 produces the number the user needs in order to rule on OPEN-22, a question now asked three times.
N04 either confirms or dissolves the project's only failure population. If N02 shows a large
fallback-agreement share, OPEN-22 and OPEN-04/OPEN-31 are one finding and go to the user together.

**After both:** the manager amends the register (struck-and-dated, never deleted — register §6 of the
director prompt) and updates the board. **No Phase 2 is written by this plan.**

---

## 8. Progress log

*Append one entry per completed task. Append-only — never rewrite an entry, including one you believe
is wrong; correct it in a new entry that cites the old.*

```
#### NXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none | rationale + register citation>
- Test status: <the "how to test" result, pass/fail, with numbers>
- Headline numbers, each with the file it was re-derived from: <…>
- Notes: <auditor-relevant>
```

#### N02 — What the labelled-accuracy metric actually measures (OPEN-22) — completed 2026-08-06
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-22_fixture-rule-breakdown.md`,
  `openubem/outputs/comparisons/open22_fixture_rule_breakdown.csv` (50 rows).
- Deviations: none. `_run_labelled_fixture()` (`tests/test_building_classifier.py:1004`) called
  unmodified for the reproduction check. To surface `archetype_source`/`archetype_confidence` (which
  the helper drops before merging), a scratchpad script called the same public entry point,
  `BuildingClassifier().classify(...)`, with the helper's own fixture-load/reorder code copied
  verbatim — no edit to the helper, the tests, or the classifier. Cross-checked 0/50 mismatches
  against the unmodified helper's `archetype_id` output before trusting the extended columns.
- Test status: (a) three-number reproduction — coarse 100.0% (50/50), fine 88.0% (44/50), 13 distinct
  archetypes — all **PASS** against §5.5's gate. (b) per-token counts sum to 50 — confirmed. (c) 5-row
  spot-check against raw fixture CSV — all 5 confirmed, included verbatim in the report §8. (d)
  `git status --short` on fixture/tests/classifier empty before and after — confirmed unmodified.
- Headline numbers, each re-derived from the run against `tests/fixtures/labelled_archetypes_50.csv`
  via `BuildingClassifier().classify()`:
  - Fine top-1, all 50 rows: 44/50 = 88.0%.
  - Fine top-1, excluding `FALLBACK_SIZE_DEFAULT` rows: 29/33 = 87.9% (n=17 excluded).
  - Per-token counts (all 10 of §5.3's vocabulary, zeros stated not omitted): RULE_HIGHRISE=5,
    RULE_RESIDENTIAL_TIER=2, RULE_LODGING_TIER=2, RULE_FUNCTION_TAG=4, RULE_FUNCTION_TAG_SIZE=0,
    RULE_USE_CLASS=1, RULE_USE_CLASS_SIZE=14, MIXED_USE_DOMINANT_TAG=0, FALLBACK_UNKNOWN=5,
    FALLBACK_SIZE_DEFAULT=17 — sum 50.
  - Confidence tier × match/mismatch: HIGH 7/1 (n=8), MEDIUM 16/3 (n=19), LOW 21/2 (n=23).
  - Two-guesses-agreeing count (connected hypothesis, reported not interpreted): of the 17
    `FALLBACK_SIZE_DEFAULT` rows, 16 also carry a human office-archetype label.
- Notes: stale Boston 41.0% / Chicago 65.4% figures (`INVESTIGATION_steps-1-3-audit.md:93`) were named
  only as excluded, not used. CP-N2 is now unblocked on the N02 side, pending N04.

#### N03 — Re-check the four June-audit remnants against HEAD (OPEN-24, 25, 26, 27) — completed 2026-08-06
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-24-27_june-remnants.md`.
- Deviations: none. Measurement only — no code, test, fixture, or DESIGN/PLAN doc edited (confirmed by
  git status: only this plan doc and the new MEASUREMENT report touched).
- Test status: each of the four verdicts carries ≥1 `path:line` in current code, per the task's "how to
  test" — see the report's per-item HEAD citations and its summary table.
- Headline numbers/verdicts, each re-derived from a named file:
  - **OPEN-24**: partially fixed/superseded. `tests/test_sim_integration.py:24-31` — live EnergyPlus-23.1
    gate, skip is environment-gated (binary absence) not a code "parked" state. `openubem/config.py:16,32`
    — `ENERGYPLUS_IDD_PATH` now resolves to the real 23.1 `Energy+.idd`, closing the IDD-version half of
    W3.7. `openubem/idf/hvac.py:1-4` — `IdealLoadsAirSystem` replaced entirely by `HVACTemplate` objects,
    so the specific dropped-fields mechanism no longer exists. But `test_sim_integration.py:1-8`'s own
    docstring ("Step-3 IDFs all fatal") is stale against `REPORT_phaseE_final.md:74` ("8,160 of 8,160
    buildings succeeded (100%)").
  - **OPEN-25**: FIXED. `openubem/semantic/__init__.py:273-433` (`enrich_semantics`) plus
    `construction_sets.py`/`loads.py`/`schedules.py` implement exactly the 15+ columns Step 3 needed
    (`_F17_ENVELOPE_COLS`/`_F17_LOADS_COLS`, `:46-63`); added 2026-06-10, the day after the audit.
    Integration-tested classifier→enrichment→IDF-gen in one test (`tests/test_step3_orchestrator.py:155-212`)
    and wired into the real fleet pipeline (`scripts/validation/v12_cell_pipeline.py:155-212`), which
    produced the adopted ~~158.0~~ **157.1 kWh/m²** (pooled: total simulated energy ÷ total
    simulated floor area; the struck figure was a count-weighted mean of the 12 cell means,
    superseded 2026-08-12, OPEN-43) / 8,160-building baseline.
  - **OPEN-26**: 1 of 4 fixed (relocated), 3 of 4 still open. Bbox-fallback now reaches the manifest via
    `generation_status="fallback_bbox"` (`openubem/idf/builder.py:611-627`), not via `data_quality_flag`
    as literally named in the audit. Still open: missing-EPW leaves `Site:Location` at the template
    default `0.0,0.0,0.0,0.0` with no flag (`builder.py:210-212`, `templates/commercial_base.idf:33-35`);
    `compute_form_factor` still has zero production call sites (`openubem/geometry/footprint.py:66`,
    only used in `tests/test_footprint.py`); neighbour bounding boxes are still recomputed per target,
    no cache (`openubem/geometry/context.py:24`, called once per building from `builder.py:425`).
  - **OPEN-27**: still wrong at HEAD, not fixed (forbidden by task rule). DESIGN doc
    `docs/docs_main/docs_step2/DESIGN_step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp.md:529`
    names `MultifamilyHome`; `openubem/data/openstudio_archetypes.json:99-111` shows the live vocabulary's
    two Residential archetypes are `MidriseApartment` and `HighriseApartment` — no `MultifamilyHome`
    entry anywhere in that file. Same error also copied into
    `docs/docs_main/docs_step2/PLAN_step-2.5-oq7-labelled-fixture.md:78` (reported, not touched).
  - **Fifth ⏳ at `INVESTIGATION_steps-1-3-audit.md:62` (not a register item)**: still true at HEAD.
    Per-row `iterrows()` MultiPolygon explode still present (`openubem/acquisition/osm_fetcher.py:374-388`);
    full ~150-column raw frame still dragged through all 7 cleaning steps before trimming to the
    23-column schema only at `osm_fetcher.py:101` (near the end of `ingest_buildings`). Whether this
    should become a register item is left to the manager, per task instruction.
- Notes: OPEN-24 and OPEN-25 both turned out more resolved than the register's ⚠️ stale-risk flag
  suggested — the manager should weigh whether either should close outright versus remain open with a
  narrower framing (OPEN-24: the docstring-staleness finding itself, not the original censor complaint).
  OPEN-26 and OPEN-27 confirm the register's stale-risk framing was warranted for those two: mostly
  unchanged since June. No CPU-bound work was performed; all evidence is static-code/doc reading.

#### N01 — Forward-trace every candidate defect to its final recorded status (OPEN-29) — completed 2026-08-06
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-29_defect-status-trace.md`,
  `openubem/outputs/comparisons/open29_defect_status_trace.csv` (13 rows over 12 candidate IDs).
- Deviations: none from the plan's method. E-LA-06 required two CSV rows instead of one because it
  genuinely splits across two buckets (§3 of the report) — noted explicitly, not silently forced into
  one bucket; reconciliation shown in the report §4.
- Test status: (a) bucket counts sum to 13 rows / 12 IDs, difference of 1 fully explained by the
  E-LA-06 split — **PASS**. (b) Method-validation control: ran E-LA-20 (not a candidate) through the
  identical forward-trace procedure blind; it independently rediscovered `FIXED, verified 150/150`
  at `docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/DONE-PLAN_e-la-20_multilayer-fix.md:68` (CP-C SIGNED
  2026-07-25) — **PASS**, method trusted on the candidates. (c) every bucket assignment carries a
  `path:line` — confirmed, see report §3 and the CSV.
- Headline numbers, each re-derived by direct grep/read against the named file:
  - CLOSED-ELSEWHERE = 3 (E-LA-11, E-LA-12, E-LA-13) — all three closed at structural-fixes CP-B/CP-C
    (2026-07-23) and reconfirmed at `e-la-20/PLAN_e-la-20_investigation.md:13` (2026-07-25).
  - STILL-OPEN = 9 (E-LA-06 flow-balance half, E-LA-15, E-LA-16, E-LA-17, E-LA-18, E-LA-19, E-LA-21,
    E-LA-30, E-LA-33) — none has a later document claiming a fix; E-LA-21 additionally confirmed still
    broken in current code (`scripts/cluster/t20_harvest_layout_assign.py:259`, one-space `"** Fatal **"`
    predicate unchanged).
  - SUPERSEDED = 1 (E-LA-06 warmup half, folded into the E-LA-14/16/18/19/23 lineage — already on
    record in the OPEN-05 sweep, not a fresh finding).
  - NO-STATUS-EVER = 0.
  - Reverse direction: checked the 6 register items that cite a specific `E-LA-nn` ID by name
    (OPEN-01/E-LA-41, OPEN-06/E-LA-38, OPEN-07/E-LA-40, OPEN-08/E-LA-22, OPEN-09/E-LA-23,
    OPEN-10/E-LA-37) — none is closed elsewhere while the register still carries it open. This check
    covers only the ID-named subset of register items, not a full re-sweep (report §5 states this
    limitation explicitly).
- Notes for the manager (auditor-relevant): **E-LA-11 contradicts the register's own OPEN-29 framing**
  — the register named it a candidate solely because its *defining* line lacks a status word, but two
  later documents (2026-07-23 CP-B, 2026-07-25 e-la-20 investigation) give it an explicit CLOSED
  ruling. Rule 11 is exactly why this matters: a defining-line read would have kept E-LA-11 open
  indefinitely. E-LA-30 is a genuine limbo case: the underlying script was never fixed, but the
  project stopped relying on it — recommend the manager decide fix/delete/leave-as-is rather than
  treat it as either open or closed cleanly. Per-ID "what to measure next" sentences for every
  STILL-OPEN ID are in the report §6, written as sentences, not register items.

#### N05 — Is a 3-building local re-run archetype-faithful to the fleet? (OPEN-34) — completed 2026-08-06
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-34_subset-archetype-fidelity.md`,
  `openubem/outputs/comparisons/open34_subset_vs_fullcell.csv` (9 rows).
- Deviations: none. Drove the real `t08_full_sweep.run_step2()` (same function E01c and
  `t08_local_remainder.py` use, imported from its real file) twice: once over the E01c 3-building
  subset, once over the whole `nyc_centre` cell (738 raw buildings, `01_buildings.gpkg` loaded with no
  filter, mirroring `t08_local_remainder.py:635-643`). Stage 2 only; no Step 3/IDF/EnergyPlus/cluster.
  Provenance for the internal levels-imputation used the classifier's own methods directly
  (`BuildingClassifier._build_levels_median_lookup`, `_impute_levels`, `_normalise_use_class`), called
  not reimplemented. Total wall time 0.6s, nowhere near the "few minutes" stop threshold, so no cost
  estimate was needed instead.
- Test status: (a) 3x3 table printed in full in the report section 2, every cell traceable to a named
  file - PASS. (b) control `way/42496314`: `SuperTallBuilding` in both runs and the adopted fixture,
  raw `levels=51`, `OSM_OBSERVED` provenance token both times - PASS, harness not STOPped. (c)
  full-cell run: 20/738 `SuperTallBuilding`, exact match to the adopted fixture's 20/738 - PASS, no
  fleet-scale divergence.
- Headline numbers, each with the file it was re-derived from:
  - 3-building run (HEAD): `way/42496352` and `way/42500728` both go to `SuperTallBuilding`
    (`archetype_source=RULE_HIGHRISE,GROUPMEDIAN_LEVELS_MED`, internal `levels_imputed=51`), reproducing
    E01c exactly (script run log, `n05_work/run.log`).
  - Full-cell run (HEAD, n=738): same two buildings both go to `LargeOffice`
    (`archetype_source=RULE_USE_CLASS_SIZE`, internal `levels_imputed=19`), matching adopted
    `05_results.gpkg` archetype exactly (re-read at commit `0df422e`, the file's last-touching commit).
  - Adopted fixture's persisted `levels=1.0`/`height_m=3.5` for those two buildings is NOT the
    classifier's internal imputed value (51 or 19, never persisted - `building_classifier.py:636-639`
    byte-equality invariant keeps raw `levels`/`height_m` untouched through `classify()`); it comes from
    a wholly separate, non-subset-dependent path: `derive_num_floors()`
    (`openubem/geometry/footprint.py:58-63`, flat default 1, no group median) feeding the IDF builder
    (`openubem/idf/builder.py:420`), harvested back from the built IDF's own SQL zone geometry by
    `scripts/validation/v12_cell_pipeline.py:659-717`.
  - Mechanism verdict: subset-dependence, not HEAD-divergence, ruled out cleanly because the full-cell
    HEAD run reproduces the adopted archetype exactly with the identical code the 3-building run used;
    only the row population passed into one `classify()` call differs, which changes
    `BuildingClassifier`'s internal `GROUPMEDIAN_LEVELS_MED` fallback (51 vs 19 against the 20/40-level
    thresholds).
- Notes: the search for a persisted imputed-levels value found none - the pipeline records which
  imputation token fired (`archetype_source`) but never the value it used; this is the same shape as
  OPEN-30 (a resolved value never persisted) and is reported here, not filed as a new item, per the
  task's instruction not to write register items. OPEN-34's mechanism (same-commit, in-scope-population
  dependent) is confirmed distinct from OPEN-08/E-LA-22's (cross-generation, semantic-imputation-commit
  dependent) per the register's own caution against merging them (register section around line 692);
  both can be triggered by the same missing-input building but are not the same defect. No remediation
  attempted.

#### N04 — Where the 41 mislabelled buildings come from, and whether the 6 are still the 6 (OPEN-06, 07, 11) — completed 2026-08-06
- Artifacts: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-06-07-11_failure-population.md`,
  `openubem/outputs/comparisons/open06_mislabel_population.csv` (41 rows).
- Deviations: none. No classifier execution in this task — reused `scratchpad/t20_true_archetype.csv`,
  the already-existing `BuildingClassifier().classify()` output produced by the AUDIT — R06 session
  (2026-08-04), verified still current because `git log` shows `openubem/semantic/building_classifier.py`
  unchanged since commit `0df422e` (2026-07-03), which predates that audit. No `.err`/`.idf` fetched from
  the cluster; where evidence was missing locally, said so (§2 of the report) rather than substituting.
- Test status: (a) recomputed the 41 independently by merging the classifier-output CSV against all 12
  `05_results.gpkg` files' live `archetype_id` — **41/41, exact match** to the register's recorded 33
  `LargeHotel` + 8 `SmallHotel`, zero discrepancy. (b) OPEN-07's three IDs confirmed **all inside** the 41
  by direct row lookup. (c) the two six-building ID lists printed in full and are **identical**,
  osm_id-for-osm_id.
- Headline numbers, each re-derived from a named file:
  - Mislabel count: 41/8,160 = `LargeHotel`→`LargeOffice` 13, `LargeHotel`→`MediumOffice` 20,
    `SmallHotel`→`SmallOffice` 7, `SmallHotel`→`MediumOffice` 1 (merge of
    `scratchpad/t20_true_archetype.csv` × 12× `docs/docs_VALIDATION/validations/overAll/results/phaseE/
    <cell>/05_results.gpkg`, all 12 files last-touched at commit `0df422e`, unchanged since).
  - Verdict (a): **SOURCE DEFECT**, not a live classifier defect — the classifier (unchanged since
    `0df422e`, i.e. current at HEAD) produces the correct Hotel archetype for all 41 when run against raw
    Stage-1 tags; 3 spot-checked raw `building_tag` values (`hotel`, `hotel`, `motel`) confirm the
    classifier is right and the gpkg is wrong. The defect lives in `05_results.gpkg`/its writer, not in
    `openubem/semantic/building_classifier.py`.
  - OPEN-07's 3 (`la_urban/way/401910463`, `nyc_rural/way/965718402`, `nyc_rural/way/965718403`): all
    inside the 41, all `SmallHotel`→`SmallOffice`, all T20 `status=failed`/`n_severe=1`
    (`openubem/outputs/comparisons/t20_layout_assign_eui.csv`). Raw `eplusout.err` survives locally for
    all three at `%LOCALAPPDATA%\Temp\ubem_t20_harvest\<cell>_layout_assign\way_<id>\eplusout.err`: one
    `** Severe **` each, zone `LAUNDRYROOMFLR1`, attributed to the **Sizing** phase (not Warmup) by the
    file's own Error Summary. Cross-population check: exactly 7/41 rows are `t20_status=failed`, all 7
    are `SmallHotel`-origin (0 of the 33 `LargeHotel` rows fail) — independently reproduces the register's
    "all 7 failures are true `SmallHotel`" claim.
  - Multiplier-scaling hypothesis: **SILENT**. No T20 `.idf` survives locally for any of the 3 (would
    require a cluster fetch, forbidden here); the T19 harvest-cache directory for `way/401910463` exists
    but is empty (0 files) — no pre/post artifact to diff a multiplier against.
  - OPEN-11's six: historical Group A (`docs/docs_DONE/LOADS & SCHEDULES/hvac-ServiceLoads/debugs/
    DONE_10_fails_solution.md:59-68`, cross-checked `docs/docs_REPORTS/REPORT_phaseE_final.md:351`) =
    `la_rural/way/472960972,472961034,472961088,472961091,472961171` + `la_urban/way/402215469`. Current
    non-success six (live `simulation_status` filter on the same 12 `05_results.gpkg`) = **identical set**.
    Fleet success recomputed directly = **8,154/8,160**, matching the register exactly. Root cause
    confirmed from `docs/docs_DONE/BUGS/misclassification/PLAN_archetype_threshold_fix_E-R3-3.md:35`: the
    2026-07-02 automated E-R3-3 full-fleet re-run (promoted to the committed baseline 2026-07-03, commit
    `0df422e`) superseded the 2026-06-27 hand-patched 8,160/8,160 file and does not invoke the
    thermal-mass fallback, so the same 6 geometry-winding buildings dropped back to `not_simulated`.
- Notes: this task did not determine which specific pipeline step writes `05_results.gpkg`'s
  `archetype_id` (out of scope for measurement-only) — only that the live classifier is not the culprit.
  No file under `openubem/`, `docs/docs_VALIDATION/`, or the register was modified.

# Executor prompt — investigate FINDING 249 and write a remedy report (no code changes)

Paste this whole file as your first message to the external agent (Gemini / Antigravity). It is
self-contained — you have no access to any other conversation, memory, or prior context about this
project. Follow it exactly.

## Hard rules — read before doing anything

1. **This is a report-only task. Do NOT edit, create, or delete any tracked file in the repository
   except the one report file named at the end of this prompt.** No production code changes, no
   test changes, no `git add`/`git commit`/`git push`, no `git` history rewrites.
2. You may run **read-only** exploration: `grep`/search the codebase, read files, and run short
   throwaway Python scripts to inspect data (e.g. print vertex coordinates of a specific building) —
   but only if you write those throwaway scripts *outside* the repo (e.g. a temp directory) or,
   if inside the repo, delete them again before finishing so `git status` is clean except for the
   one report file.
3. **Never run `pytest` in a way that mutates files, and never run anything on a compute cluster.**
   There is no cluster access from this task and none is needed.
4. **`openubem/idf/surfaces.py` is off-limits to edit** (standing project rule `D-EU-41`) — it is
   treated as a vendored/accepted-behavior boundary. You may read it and quote from it, but any
   remedy you propose must not require editing it; if you believe it must be edited, say so
   explicitly in the report as a flagged open question, don't just do it.
5. Environment: Windows. Repo root `C:\Users\o_iseri\Desktop\OpenUBEM`. Python is **not** on PATH —
   use `C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe` for anything you run.
6. **Evidence discipline:** every claim in your report must cite a real `file:line` or be the
   verbatim output of a command you actually ran. Never state a number, a line range, or a behavior
   you have not personally confirmed by reading the file or running the command. If you're not sure,
   say "unconfirmed" rather than guessing.
7. **Stop condition:** once the report file is written, stop. Do not attempt to implement the fix in
   production code, even if you're confident in it.

## The problem

This project (OpenUBEM, an urban building energy model) generates one EnergyPlus IDF file per
building for a set of European districts, including a "dwelling layout" — each apartment/unit gets
its own thermal zone. A safety net in `scripts/run_eu_s2_campaign.py` detects buildings whose
geometry looks EnergyPlus-fatal-risky and, for those buildings only, **discards the per-dwelling
zone layout** and collapses the building to one zone per floor instead (`reason` string
`"near_duplicate_vertex"` or `"interzone_vertex_mismatch"`, function
`_force_reroute_room_layout_to_one_zone_per_floor`). This safety net is currently firing on
**1,306 of 2,262 buildings (57.7%)** in the affected districts — far more than actually need it —
which throws away real, valid dwelling layouts for buildings that would otherwise simulate fine.
That is `FINDING 249`, and it is the last failing gate (of 5) blocking a checkpoint (internally
called `CP-2`) before this data is submitted to a compute cluster for a large EnergyPlus campaign.

**Your task:** understand *why* the safety net is over-firing, and write a report proposing how to
fix it so dwelling layouts survive for buildings that don't actually need the safety net — without
regressing EnergyPlus correctness (0 Fatal/0 Severe must be preserved) or the geometry area that is
already validated to match exactly between old and new code paths.

## What is already known — read this before investigating further

Two prior investigation rounds already happened in-house. Read them in full before forming your own
theory, so you don't re-derive what's already established:

- **Full diagnostic history:** `docs\docs_ACTIVE\europeanLocations\implementation\PLAN_eu-nocore-interzone-rootcause-2026-09-04.md`
  — read the whole file, especially §8 (progress log). It contains:
  - `T01`–`T02c`: confirmed the safety net's trigger condition
    (`scripts/run_eu_s2_campaign.py:645-646,662`, `at_risk = mismatched or near_duplicate`) is, on a
    16-building real-geometry sample (8 reroute-labelled, 8 clean), **carried entirely by
    `near_duplicate_vertex`** (`_has_near_duplicate_vertex_surfaces`,
    `scripts/run_eu_s2_campaign.py:94-125`) — `mismatched`
    (`find_mismatched_interzone_pairs`) was `False` on all 16, including every reroute-labelled one.
  - `CP-1` (director checkpoint): picked a remedy — before the reroute fires, for the
    `near_duplicate_vertex`-only case, detect the flagged vertex pair and snap it to one shared
    coordinate on both of a pair of interzone-partnered surfaces, symmetrically, to remove an
    assumed floating-point asymmetry between the two surfaces.
  - `T03`: **implemented that remedy** (`_symmetrize_near_duplicate_interzone_vertices`,
    `scripts/run_eu_s2_campaign.py:128-227`, wired in at `scripts/run_eu_s2_campaign.py:658-661`)
    then **empirically falsified its own premise** before writing a test, by probing 3 real
    reroute-labelled buildings vertex-by-vertex (see the `T03` entry, "🔴 Why stopped" section, for
    full detail and exact building ids). Findings, no exception across the 3 buildings probed:
    - `_has_near_duplicate_vertex_surfaces` actually has **two independent sub-checks**
      (`scripts/run_eu_s2_campaign.py:94-125`): a **proximity** check (two consecutive vertices on
      one ring closer than `NEAR_DUPLICATE_VERTEX_TOLERANCE_M = 0.005` m,
      `scripts/run_eu_s2_campaign.py:77`) and a **collinearity** check (three consecutive vertices
      within `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG = 0.1°` of a straight 180° angle,
      `scripts/run_eu_s2_campaign.py:91`). **100% of the defects found across all 3 buildings were
      the collinearity sub-check (angle 179.91-179.99°), 0% were the proximity sub-check.**
    - A collinear vertex cannot be fixed by "snapping to a shared coordinate" — any point on the
      same line is still exactly collinear. The implemented remedy structurally cannot clear this.
    - **Many of the defective surfaces have no interzone partner at all** (e.g. a ground `Floor` or
      a `Roof` with `Outside_Boundary_Condition_Object` empty) — there is no second surface to
      "snap both sides of a pair" against.
    - **Where a nominal partner does exist** (e.g. a ceiling/floor pair between two stacked storeys
      of the same dwelling block), **both sides already carry the identical defect value** (same
      vertex index, same angle) — not the asymmetric two-slightly-different-values pattern the
      original root-cause comment describes for a different, EnergyPlus-verified defect
      (`scripts/run_eu_s2_campaign.py:630-644`, stem `e21bec78b937acf5`). There is nothing
      asymmetric to symmetrize in this population.
    - The same exact collinear angle value repeats bit-for-bit across every stacked storey of one
      footprint (ground floor, roof, every interfloor pair) — indicating **one static footprint
      polygon, extruded once, carrying one inherent near-collinear vertex in its own ring** — not
      the `intersect_match`-inserts-a-fresh-asymmetric-point-per-storey mechanism the remedy
      presupposed.
  - Read `scripts/run_eu_s2_campaign.py:630-644` for the original, different, EnergyPlus-verified
    defect this whole safety net was originally built for (a real, confirmed FATAL on a different
    building) — that mechanism is real and should **not** be broken by whatever you propose; the
    open question is specifically about the *collinear, often-partner-less* population T03 found,
    which is apparently a large fraction of the 1,306 over-firing buildings but has not yet been
    counted precisely (you may write a read-only script to count it if useful — see rule 2).
- **`D-EU-41` / non-editable-boundary precedent and other prior findings:**
  `docs\docs_EXPLANATION\OpenUBEM_debug_References.md` — search for `D-EU-41`, `D-EU-95`,
  `FINDING 210` for the house style and precedent this project uses when a fix might need to touch
  `openubem/idf/surfaces.py`, and why that has been avoided so far.

## What to actually investigate

1. Confirm or refute T03's finding yourself on at least a couple of additional real buildings (the
   plan doc's `T02b`/`T02c` entries list the real-geometry rebuild path and sample building ids to
   reuse) — don't just trust the write-up, re-derive at least one data point.
2. Characterize the collinear, often-partner-less population: is it always a single static footprint
   ring issue? Is the near-collinear vertex something introduced by this project's own geometry
   pipeline (e.g. the no-core cutter, `openubem/geometry/european_nocore.py`) or does it already
   exist in the source OSM/footprint data?
3. Propose a concrete remedy. Consider at least: (a) removing/relocating the inherent collinear
   vertex from the footprint ring before extrusion (note: this may need to happen upstream of
   `openubem/idf/surfaces.py`, e.g. in the no-core cutter or the zone-building code in
   `scripts/run_eu_s2_campaign.py` itself — identify exactly where), (b) special-casing
   partner-less surfaces separately from paired ones, (c) whether the collinearity sub-check's
   0.1° tolerance is simply too aggressive for this population and could be safely narrowed instead
   of "fixing" the geometry, (d) any other approach you find better. For each option, state: exactly
   which file:line would change, why it doesn't need to touch `openubem/idf/surfaces.py` (or
   explicitly flag that it does), what could go wrong (regression risk on the 4 already-passing
   gates — 0 circulation-zone loss, route counts, geometry area, and old-vs-new exact-diff), and how
   you'd test it.
4. Recommend one option as primary, with the others as alternatives and why you didn't pick them.

## Report format and location

Write your findings as a single Markdown file at:

`docs\docs_ACTIVE\europeanLocations\debugs\DEBUG_finding249_cp2-gate5-remedy-report_2026-09-04.md`

Structure it as:
- `# FINDING 249 — CP-2 gate 5 remedy investigation report`
- `## Summary` — 3-5 sentences, the recommendation and why.
- `## Confirmation of T03's finding` — what you re-checked and what you found, with file:line/output
  evidence.
- `## Characterization of the collinear population` — what you learned about where it comes from.
- `## Options considered` — one subsection per option from step 3 above, each with the file:line,
  risk, and test plan.
- `## Recommendation` — which option, and the minimal next steps to implement and validate it.
- `## Open questions` — anything you could not resolve with read-only investigation.

This is a report for a human reviewer to evaluate, not a pull request — do not implement the fix.

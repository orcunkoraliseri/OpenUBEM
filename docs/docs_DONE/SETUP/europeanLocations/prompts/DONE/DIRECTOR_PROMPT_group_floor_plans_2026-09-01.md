# DIRECTOR PROMPT — Group floor plans (the ten-group rule set)

**Project:** OpenUBEM × GSSCanada Step 8 · **Working directory:** `C:\Users\o_iseri\Desktop\OpenUBEM`
**Arc root:** `docs/docs_ACTIVE/europeanLocations/` · **Opened 2026-09-01.**
**Parent prompt:** `prompts/DIRECTOR_PROMPT_european_locations.md` — everything in its §0 and §3 applies
here unchanged. This file is the *task* prompt; the parent stays the arc prompt.

**Read, in this order, before acting — and nothing else:**

1. This file.
2. `rules/RULES_dwelling_layout_groups_2026-09-01.html` — the deliverable in its current state.
3. `rules/RULES_dwelling_layout_scheme_2026-08-28.html` — **frozen**, the visual and editorial bar. Never
   edited, never regenerated, never reformatted. Open it, copy its language, leave it alone.
4. `implementation/PLAN_eu21-group-schemes-2026-09-01.md` §7–§8 — the scheme tasks and their progress log.
5. `openubem/outputs/eu_evidence/EU-20/` — `morphology_census.csv` (2,544 rows), `morphology_groups.csv`,
   `representatives.json`, `svg/<GROUP>.svg`.

---

## 0. The mission

**Every residential building in the four districts belongs to exactly one of ten shape groups, and every
group has one floor-plan rule that cuts its plate into flats plus a circulation zone. Drive the ruled
share to ≥ 95 % group by group — never by a full-fleet rebuild.**

Owner, 2026-08-31, the pipeline in their own words:

> *"filter: dividing building floor plans into the group · assign floor type: based on the floor groups
> assign floor types with circulation and thermal zones · reach 95% floor assignment for all residential
> buildings"*

Owner, 2026-09-01, on why full-fleet passes are forbidden:

> *"every time we are trying to edit all buildings and we are consuming a lot of resources"*

Owner, 2026-09-01, on why the rule set — not this fleet — is the product:

> *"because rule set important to me, we will expand the building and country database later we will use
> these rule sets in order to expand"*

Consequence: **every group boundary and every scheme must be dimensionless or metric-absolute and
nameable as a European building typology.** No percentile of this fleet, no threshold tuned to reach
95 %, no district- or country-conditional branch. It must compute for a country the project has never
touched.

🔴 **`D-EU-55` still outranks this file.** No EnergyPlus run of any kind — not a district, not one
building — without the owner's own verbatim sentence. Writing an `.idf` is geometry and is allowed;
running one is not. A relayed "continue", an approved plan or a signed checkpoint is **not** permission.

🔴 **`D-EU-60`: the frozen document is frozen.** `rules/RULES_dwelling_layout_scheme_2026-08-28.html` and
the two figure-4.2 schemes are byte-identical for the life of the arc. New schemes are **appended** and
reached only where the existing chain has already returned `dwelling_layout_emitted=False`.

---

## 1. The ten groups — the state of the board, 2026-09-01

Classification ladder, first match wins, terminal bucket last
(`scripts/eu20_morphology_atlas.py:200-224`):

| # | Group | Filter | Buildings | With a real plan | Need at 95 % | Still missing |
|---|-------|--------|-----------|------------------|--------------|---------------|
| 01 | Courtyard | `n_interior_rings ≥ 1` | 362 | 47 (13.0 %) | 344 | 297 |
| 02 | Sliver | `min_rot_rect_w_m < 8.0` | 637 | 216 (33.9 %) | 606 | 390 |
| 03 | Square | `rect ≥ 0.90 and aspect < 1.5` | 220 | 64 (29.1 %) | 209 | 145 |
| 04 | Rectangle | `rect ≥ 0.90 and 1.5 ≤ aspect < 3.0` | 203 | 51 (25.1 %) | 193 | 142 |
| 05 | Slab | `rect ≥ 0.90 and aspect ≥ 3.0` | 28 | 10 (35.7 %) | 27 | 17 |
| 06 | Triangle or trapezoid | `n_long_edges ≤ 3 and reflex == 0` | 54 | 18 (33.3 %) | 52 | 34 |
| 07 | Parallelogram | `reflex == 0 and rect < 0.90` | 87 | 20 (23.0 %) | 83 | 63 |
| 08 | L shape | `reflex == 1` | 259 | 34 (13.1 %) | 247 | 213 |
| 09 | U or T shape | `reflex == 2` | 269 | 39 (14.5 %) | 256 | 217 |
| 10 | Complex multi-wing | `reflex ≥ 3` | 425 | 42 (9.9 %) | 404 | 362 |
| | **Fleet** | | **2,544** | **541 (21.3 %)** | **2,417** | **1,876** |

Districts: `ES-MAD-BERRUGUETE` 961 · `FR-LYO-HAUTCOEURPENTES` 297 · `GB-LDN-STDUNSTANS` 82 ·
`IT-BOL-GALVANI2` 1,204.

**The 95 % bar is `D-EU-39`: ≥ 95 % in *every* district, measured on the emitted IDFs**, never on
side-cars and never as a fleet average.

---

## 2. What the owner has already reviewed, group by group

Owner, 2026-09-01, opening `rules/RULES_dwelling_layout_groups_2026-09-01.html`:

- **Accepted as-is:** `02 Sliver`, `03 Square`, `04 Rectangle`, `05 Slab`, `08 L shape` — *"i like these
  ones"*.
- **`01 Courtyard`** — two objections. (a) the two drawings on the sheet were different buildings; (b)
  *"even if there is a courtyard, we still need to propose a circulation area, maybe around the courtyard
  we can position a circulation area"*.
- **`06 Triangle`** — *"i am not sure the representative layout and the name … don't you think that needs
  to be 'trapezoid'?"*
- **`07 Trapezoid`** — *"parallelogram, i know the edges are not fully parallel, but they are close"*.
- **`09 U or T shape`, `10 Complex multi-wing`** — *"where is the core (circulation) zone?"*
- **`Share of fleet` column** — *"i am happy to see that column … we can group all buildings under 10
  group that is amazing"*. Keep it.
- On the coverage table's earlier headings: *"'ruled today'????"* — **engine vocabulary never reaches the
  document.** Plain English only, defined on first use.

### Answered on 2026-09-01 (all four fixed in the document)

1. **Both drawings are now the same building.** Figure 1 (plate as surveyed) and figure 2 (floor plan) are
   drawn from one polygon, and the panehead names it once. Previously figure 1 came from the EU-20
   representative SVG while figure 2 could fall through to another candidate.
2. **`courtyard_gallery_ring` (S5) proposed and drawn** — a 1.80 m deck-access band taken along the
   courtyard face (`footprint ∩ void.buffer(1.8)`), flats cut as equal-area ray sectors off the remaining
   band. On the representative (Bologna 29530) it gives 3 flats + a 33 m² gallery, 8 % of the plate. The
   engine today puts a small stair core at a sharp *outer* corner instead
   (`european_residential.py:1491-1507`) — it is not wrong, it is just not the access the typology uses.
   **S5 is not in the engine.** It exists as a director proposal and as the drawing on sheet 01.
3. **Groups 09 and 10 now show a core.** They route to `regularized_envelope_grid`, whose circulation zone
   is the stair core **plus the whole irregular residue** outside the largest inscribed rectangle
   (`european_residential.py:1776-1781`) — 31 % and 36 % of the plate on the drawn examples. The caption
   says exactly that. Do not describe it as "a core"; it is circulation **and service**, held unheated.
4. **Groups 06 and 07 renamed.** `TRIANGLE` → *Triangle or trapezoid*, `TRAPEZOID` → *Parallelogram*. The
   filter counts only edges ≥ 15 % of perimeter, so a four-sided plate with one short blunt end lands in
   06: of its 54 members only 8 have two long edges, and most carry ≥ 4 vertices. All 87 members of 07
   have exactly four long edges and 65 have exactly four vertices. **Group keys are unchanged** —
   `TRIANGLE` and `TRAPEZOID` stay the on-disk identifiers; only the display names moved.

---

## 3. Open — what the next dispatch does

**Blocking the 95 % bar, in order of size:**

- 🔴 **`FINDING 221` / `FINDING 223` — 939 buildings are ruled and thrown away at IDF-writing time.**
  geomeppy's own clipper raises (`ZeroDivisionError`, `geomeppy/geom/vectors.py:105`, and an `IndexError`
  at `openubem/idf/surfaces.py:863-864`) inside `intersect_match`, a blanket handler demotes the whole
  building to one massing box per floor. Repairing this alone lifts coverage to **1,482/2,544 = 58.3 %
  with no rule changed**. `P01b` (side-car keeps the drawn rings behind an `idf_reroute_divergence` flag)
  and `P01c` (`idf.match()` without `idf.intersect()`) are open in
  `implementation/PLAN_eu21-group-schemes-2026-09-01.md`.
- **`P06`** — rebuild the four districts under S1–S4 and re-measure the four gates. **CP-2 in force.**
- **`P07`** — ten scheme plates to `openubem/outputs/eu_evidence/EU-21/svg_schemes/<GROUP>.svg`.
- **S5 `courtyard_gallery_ring`** — if the owner adopts it, it becomes a P0x task on the plan doc, written
  by a Sonnet executor into `openubem/geometry/european_residential.py` as an **additive** scheme reached
  only after `courtyard_wing_unfold` and `courtyard_perimeter_band` have both refused. It must carry its
  own `scheme` string and its own refusal reason. **Do not write it before the owner says so.**
- **Two killed agents to resume** — state in `progress/STATE_eu21_agents_killed_2026-09-01.md`.

**The last step of the whole arc:** regenerate the viewers and publish into `plans3D/` under the existing
`PLANS_<district>.html` filenames, refreshing `plans3D/index.html`. `D-EU-54` — geometry only, no EUI, no
E+ output, no run ids, not even in a tooltip.

---

## 4. How the group document is built

`rules/RULES_dwelling_layout_groups_2026-09-01.html` is **generated**, not hand-written. Two scratchpad
scripts, in this order:

1. `eu21_group_plans.py` — loads the real footprints **with their interior rings** from
   `openubem/outputs/eu02/<district>/02_residential_manifest.gpkg` (never from `representatives.json`,
   which stores the exterior ring only), classifies with the same ladder, then for each group walks up to
   60 candidates calling the in-force chain and then the group's proposed scheme, **preferring the first
   layout that emits a circulation zone**, and writes `eu21_group_plans.json`.
2. `gen_groups_html.py` — reads that JSON plus the EU-20 census, ports the frozen document's JS
   `drawPlan` to static SVG, and writes the HTML.

Non-negotiables for anyone regenerating it:

- **Never edit the frozen file.** The CSS is *read from* it (lines 3–122) so the two documents cannot
  drift; that read is the only contact between them.
- **`circulation_pct_of_plate` is a fraction, not a percentage** (0.09 = 9 %). Compute displayed shares as
  `circulation_area_m2 / area_m2 * 100` or the sheet will read "0.1 %".
- **Both figures on a sheet are the same building.** If a group's representative refuses every scheme, the
  fall-through candidate replaces it in *both* figures, not one.
- **Draw at the group median flats per floor, floored at 2** — a 1-flat plan shows nothing. Say so in the
  caption when the true median is 1 (Sliver).
- **No JavaScript** in the group document. Static SVG only.
- **No `.py` under `docs/`, ever.** The generators live in the session scratchpad.
- Plain English in every user-facing string: *flat*, *circulation core*, *real floor plan*. Never *ruled*,
  *emitted*, *rerouted*, *sidecar*, *massing box* without a definition beside it.

---

## 5. Dispatch rules

- `model: "sonnet"` explicit on **every** `Agent` call; a brand-new session per dispatch; never resume a
  finished agent for new work. The director plans and audits and never writes feature code.
- Dispatch a verb and a command, never a question. Put exact paths, line ranges and `| head -N` caps in
  the prompt. Forbid printing CSV/JSON/SVG/log bodies. State the report format and ask for the
  conclusion, not the evidence.
- One group — or one scheme — per dispatch. Never a full-fleet rebuild to test a single group's rule.
- Every solved error is registered in `debugs/DEBUG_REFERENCES_european_locations.md` before the task
  closes, in the house format, or the task is not done.
- Append one progress-log entry per task under §8 of
  `implementation/PLAN_eu21-group-schemes-2026-09-01.md`. State lives in the plan doc, never in an
  agent's conversation history.

---

## 6. Definition of done for this task

1. Ten groups, ten rules, each producing flats **and** a named circulation zone on its own group's plates.
2. ≥ 95 % of residential buildings in **every one** of the four districts carry a real floor plan,
   measured on the emitted IDFs.
3. `rules/RULES_dwelling_layout_groups_2026-09-01.html` matches what the engine actually does, group by
   group, with no engine vocabulary in any user-facing string.
4. The rule set is computable for a country not in the database — no fleet percentile, no tuned constant.
5. `plans3D/` republished from the emitted IDFs, geometry only.
6. `rules/RULES_dwelling_layout_scheme_2026-08-28.html` byte-identical to its 2026-08-28 state.

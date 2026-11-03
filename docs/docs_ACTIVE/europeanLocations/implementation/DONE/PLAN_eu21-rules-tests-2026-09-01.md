# PLAN — EU-21 rules tests: the eleven group rules applied to sampled real buildings

**Slug:** `eu21-rules-tests` · **Date:** 2026-09-01 · **Arc:** `docs/docs_ACTIVE/europeanLocations/`
**Working directory:** `C:\Users\o_iseri\Desktop\OpenUBEM`
**Python:** `.venv\Scripts\python.exe` (3.14, shapely 2.1.2, geopandas 1.1.3). `python` on the bare PATH is the
Windows Store stub and runs nothing — always call the venv interpreter. Set `PYTHONIOENCODING=utf-8` when a
script prints non-ASCII.
**Spec under test:** everything in `docs/docs_ACTIVE/europeanLocations/rules/` — the eleven sheets and the
seven-step flow of `RULES_dwelling_layout_groups_2026-09-01.html`, the `D-EU-64` law
(`prompts/DIRECTOR_PROMPT_group_floor_planning_2026-09-01.md` §2), the MVP scheme rules of the frozen
`RULES_dwelling_layout_scheme_2026-08-28.html` (MVP §4.2–§4.4), and the acceptance quantities of
`EXAMPLE_dwelling_layout_validation_2026-08-28.md` §6. `RULES_context_geometry_simulation_2026-08-30.md`
(`D-EU-40`) concerns the simulation context, not the plate, and is out of scope here — say so in each sheet's footer.
**Ruling in force:** 🔴 `D-EU-55` (no EnergyPlus run without the owner's own sentence) · `D-EU-64` (one core per
plate, no unassigned space) · `D-EU-36` (refusal above 8 per floor is by design, never approximated).

**Owner instruction (2026-09-01, verbatim):** *"to test: select 3 examples of buildings for each group and assign
floors them · to test: different floor areas: small (3 flat per floor) & medium (6 flats per floor) & big (9 flats
per floor) & very big (12 flats per floor) · to test: select 5 examples of buildings for each group and assign floors
them · to test: different floor areas … · to test: select 10 examples of buildings for each group and assign floors
them … this is working only focusing on visual outputs and testing if our rules are applying correctly … for each
test create new .html like these [RULES_dwelling_layout_groups_2026-09-01.html]"* and *"look at all the rules and
examples i want [in] …/rules"*.

---

## 1. What is built

Five HTML test sheets in `docs/docs_ACTIVE/europeanLocations/rules/tests/`, one per test, same CSS and same drawing
language as the rules document. Each sheet takes real buildings from the census, sorts them with the same ladder,
cuts each one with the same engine call the rules document uses, applies the same `D-EU-64` post-pass, draws the
result, and **checks every plate against the written rules** (§5, C1–C7). A plate the rule refuses is shown as a
refusal box with the engine's own reason token — a refusal is a result, never hidden and never replaced.

| Test | File | Buildings per group | Drawn at | Plates |
|---|---|---|---|---|
| 01 | `TEST_01_three_per_group_2026-09-01.html` | 3 | the building's own flats/floor | 33 |
| 02 | `TEST_02_floor_sizes_x3_2026-09-01.html` | 3 per size × 4 sizes | 3 · 6 · 9 · 12 | 132 |
| 03 | `TEST_03_five_per_group_2026-09-01.html` | 5 | own flats/floor | 55 |
| 04 | `TEST_04_floor_sizes_x5_2026-09-01.html` | 5 per size × 4 sizes | 3 · 6 · 9 · 12 | 220 |
| 05 | `TEST_05_ten_per_group_2026-09-01.html` | 10 | own flats/floor | 110 |

Known in advance, and to be shown, not worked around: **the engine refuses every count above 8 per floor**
(`RULED_GRID_MAX_DWELLINGS_PER_FLOOR = 8`, `openubem/geometry/european_residential.py:31`, raised at `:1097`; the
grid table at `:180-190` has no entry past 8; `D-EU-36` and MVP §4.2 make this the design). So the 9- and 12-flat
rows of tests 02 and 04 will be refusal boxes carrying `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` for every engine
scheme. The one exception is `COURTYARD`, whose `courtyard_gallery_ring` (S5) lives only in
`scripts/eu21/01_cut_group_plans.py` and has no cap — it may draw at 9 and 12. That asymmetry is a finding of the
test, not a bug to fix here.

---

## 2. Hard rules for the executor

1. 🔴 **`D-EU-55` — never run EnergyPlus.** Nothing in this plan writes or runs an IDF.
2. **Never edit** `rules/RULES_dwelling_layout_scheme_2026-08-28.html` (frozen; read its CSS only),
   `rules/RULES_dwelling_layout_groups_2026-09-01.html`, `scripts/eu21/03_build_rules_html.py`,
   `scripts/eu21/group_plans.json`, or anything under `openubem/geometry/`. The engine is the thing under test.
3. **Never `git add` / `commit` / `stash` / `restore` / `checkout` / `reset` / `clean`.** The tree is dirty and belongs
   to the owner.
4. **Never write into `openubem/outputs/eu_evidence/EU-17/` or `EU-20/`.** Test evidence goes to `EU-21/rules_tests/`.
5. **No `.py` under `docs/`.** Scripts live in `scripts/eu21/`.
6. **Never run `01_cut_group_plans.py`, `02_one_core_per_plate.py` or `03_build_rules_html.py` as scripts.** `02` is
   not idempotent on its own output (it reads `circulation` as bare rings and writes it as ring-sets) and
   `group_plans.json` on disk is already post-`02`. T01 makes `01` and `02` importable; it does not run them.
7. **Do not "fix" a failing plate.** A plate that fails a check, or is refused, is the test's finding. Draw it, mark
   it, count it. Do not tune a constant, do not filter it out, do not swap the building for one that passes.
8. **Create nothing that is not in §3.** No extra docs, boards, notebooks, PNGs.
9. The engine's `circulation_pct_of_plate` is a **fraction**; every displayed share is
   `circulation_m2 / plate_m2 * 100` computed from the drawn rings.
10. If the spec or this plan is ambiguous, **stop and quote the conflict** in the progress log. Do not invent.
11. Every error you solve on the way is registered in `debugs/DEBUG_REFERENCES_european_locations.md` (house
    format, chapter 1 or 10) before the task closes.

---

## 3. File layout

| Path | Status | Role |
|---|---|---|
| `scripts/eu21/01_cut_group_plans.py` | **EDIT (T01)** | make importable: module-level defs stay; loading moves into `load_universe()`, selection into `main()`; `if __name__ == "__main__": main()` |
| `scripts/eu21/02_one_core_per_plate.py` | **EDIT (T01)** | make importable: the loop body at `:846-902` becomes `apply_law(r) -> r`; `main()` keeps load / loop / dump; `if __name__ == "__main__": main()` |
| `scripts/eu21/04_group_tests.py` | **NEW (T02)** | selection · engine call · law · checks · JSON · HTML. CLI: `--test {1,2,3,4,5,all}`, `--render-only`, `--limit N` |
| `openubem/outputs/eu_evidence/EU-21/rules_tests/test_0N.json` | NEW (T02/T03) | every plate of test N with rings, scheme, refusal, checks |
| `docs/docs_ACTIVE/europeanLocations/rules/tests/TEST_0N_*_2026-09-01.html` | NEW (T02/T03) | the five sheets, names in §1 |

Nothing else is touched.

---

## 4. Dependency decisions (pinned)

- **Import, do not copy, the pipeline.** `04` loads `01` and `02` with `importlib.util.spec_from_file_location`
  (their names start with a digit, so no plain `import`). From `01`: `cls`, `options`, `capture`, `load_universe`,
  `ORDER`, `DISTRICTS`, `NO_CORE_BY_DESIGN`. From `02`: `apply_law`, `lobes_of`, `parts`, `sbuf`. Importing must
  execute nothing but definitions — that is what T01 guarantees.
- **Copy, do not import, the drawing.** `03` is a script that writes the rules HTML at import time and is off-limits.
  Copy verbatim into `04`: `FILLS`, `_bounds`, `_path`, `_centroid`, `drawplan` (`03:79-146`), `TITLE`, `DSHORT`
  (`03:13-20`), and the `CLOSE` list (`03:165-172`) for the check legend. The CSS is read exactly as `03:8` reads it —
  `FROZEN.read_text(encoding="utf-8").splitlines()[2:122]` — plus the `table.cov` / `.pane` / `.specs` rules copied
  from `03`'s `extra` block (`03:562-585`), plus the `.checks` block defined in T02.
- **Same engine call, same choice rule as the rules document.** `options(p, n, grp)` from `01:101`; take `opts[0]` (it
  is sorted core-first). No second candidate, no retry with another building.
- **Same law.** `apply_law(rec)` from `02`, unchanged. Wrapped in `try/except Exception` — an exception is a plate
  verdict `ERROR`, not a crash of the test.
- **Refusal token.** `why` from `options()`; if `opts` is empty and `n > RULED_GRID_MAX_DWELLINGS_PER_FLOOR` (import
  the constant from the engine, never write `8`), the token is `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8`; if empty
  for any other reason and `why` is `None`, `NO_SCHEME_RETURNED`.
- **Per-floor count of a building** `k = max(1, round(dwellings_total / storeys))` — exactly `01:143-145`.
- **Checks C1–C6 are pass/fail; C7 is report-only with a band marker.** Definitions in §5 and T02. The plate
  verdict is `PASS` only when C1–C6 all pass.
- **Deterministic selection, no randomness anywhere.** Rules in T02. Same input → same sheet.
- **Output JSON before HTML.** `--render-only` rebuilds the HTML from the JSON without touching the engine, so a
  layout change never costs a recompute.

---

## 5. The rules under test, with citations

Every check below quotes the document it comes from. The test sheet's CHECKS section lists them in this order and
wording.

| # | Check | Pass when | Source |
|---|---|---|---|
| C1 | **Coverage** — flats + circulation = footprint | `0.999 ≤ (Σ flats + Σ cores) / plate ≤ 1.001` | groups sheet step 6 "100 %"; `D-EU-64` §2.3 "≥ 99.9 %"; EXAMPLE §6.2 "area error 0.00 %"; MVP §4.3 area conservation |
| C2 | **One circulation zone** | `n_core == 1`; `SLIVER`: `n_core ≤ 1` | `D-EU-64` §2.1 and §2.5; groups sheet step 6 "exactly one (Sliver: none)"; EXAMPLE §6.3 "a circulation zone present on every storey carrying two or more dwellings" |
| C3 | **Drawn = claimed** | `len(flats) == n` | `D-EU-64` §2.4; groups sheet step 6 |
| C4 | **Each flat one room, no overlap** | every `lobes_of(f) is None` and the largest pairwise intersection (flat/flat, flat/core) `< 0.02 m²` | `D-EU-64` §2.6 (0.75 m erosion test); groups sheet step 6 "each flat is one connected room, no two zones overlap" |
| C5 | **Simple outline** | no zone has an interior ring; no zone `contains` another zone's `representative_point()`; max points per zone `≤ 40` | `D-EU-64` §2.10; groups sheet step 6 "no hole, nothing enclosed, 4 to 21 points" (the 40 is a ceiling with headroom, stated on the sheet) |
| C6 | **Facade contact** | every flat holds `≥ 2.50 m` of the outer wall: `sbuf(flat, 0.05).intersection(fp.exterior).length ≥ 2.50` | MVP §4.4 habitability gate; EXAMPLE §6.4 "smallest facade contact ≥ 2.50 m"; engine `minimum_facade_contact_m = 2.5` (`european_residential.py:1082`) |
| C7 | **Circulation share** (report) | shown as `x.x %`; chip `info` inside 6–12 %, `warn` outside; never pass/fail | MVP §4.3 "6–12 % of gross floor area"; `FINDING 204` (the 12–25 m² band conflicts and is unruled — report, do not resolve); `Corridor rectangle` and `Slab` run above the band by construction (1.80 m corridor), which the sheet notes |

Also shown per plate, no check: the scheme name and whether it is in force or proposed (groups sheet step 7), the
m² per flat, and the total point count. The MVP rule "5 or more per storey → corridor spine; 2–4 → stair core" is
visible through the scheme name; it is not a check because the groups document supersedes it per group (Corridor
rectangle and Slab take a corridor at 3).

Other facts with citations:

- Ladder classifier: `01:27-39` (mirrors `scripts/eu20_morphology_atlas.py:200-224`). Group order: `01:22-23`.
- Engine entry: `generate_european_ruled_storey_layout(footprint, *, dwelling_count, ...)` at
  `openubem/geometry/european_residential.py:1078`; raises `ValueError` when
  `dwelling_count > RULED_GRID_MAX_DWELLINGS_PER_FLOOR` (`:1097`). Every proposed scheme carries the same guard
  (`:1482`, `:1559`, and the wing/envelope ones).
- Result object `EuropeanGridLayout` (`:261`): `dwelling_polygons`, `circulation_polygon`, `circulation_area_m2`,
  `scheme`, `fallback_reason`, `dwelling_layout_emitted`.
- `options()` returns `[(dwelling_polys, circ_poly, scheme, status, circ_m2), ...]` core-first, plus the first
  refusal string (`01:101-124`). `capture()` turns polygons into ring lists (`01:68-75`). `gallery_ring()`
  (`01:78-98`) is S5, `COURTYARD` only, no density cap.
- Loading: `01:127-135` reads `openubem/outputs/eu02/<district>/02_residential_manifest.gpkg` per district; keys
  `(district, building_id)`; `01:137-149` reads `EU-20/morphology_census.csv` and computes `_n`, `_st`.
- Centring: `translate(g, -g.centroid.x, -g.centroid.y)` (`01:180`) — EXAMPLE §8 records that a footprint left in
  UTM coordinates silently produces empty cells. Always translate first.
- Law post-pass: `02:845-902` — `pick_core` → `absorb` → `merge_to` → `fold_narrow_to_core` ×3 → (`tidy` +
  `unsnake`) ×3 → (`straight_cuts` + `tidy`) ×2 → `open_rings` → `disjoint` → gap closing → dekink. Reads
  `r["footprint"]`, `r["dwellings"]`, `r["circulation"]` (bare rings, as `capture()` emits), `r["drawn_per_floor"]`;
  writes `dwellings` (ring-sets), `circulation` (`[rings(core)]`), `circ_m2`, `cores_before`, `circ_m2_before`.
- Snake test: `lobes_of(f)` (`02:501-527`) returns `None` when the flat is one compact room after a 0.75 m erosion.
- Drawing: `drawplan(rec, uid, bare=False)` (`03:107-146`) expects `rec["footprint"]`, `rec["dwellings"]`,
  `rec["circulation"]`, `rec["group"]`; labels `F1…Fn`, hatches the core, draws a 10 m bar.
- The five census refusal tokens and their readings (from `implementation/PLAN_eu21-group-schemes-2026-09-01.md`
  §1): `L_SHAPE_DECOMPOSITION_FAILED` — the reflex-corner cut found no wing split that passes the audit ·
  `INTERIOR_RING_COURTYARD_UNFOLD_FAILED` — the courtyard unfold found no band that holds a room and a facade ·
  `NARROW_FOOTPRINT_LT_8M` — plate narrower than the 8.0 m habitable depth ·
  `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` — above 8 flats on one floor the rule refuses outright (`D-EU-36`) ·
  `PARTITION_AUDIT_FAILED` — the cut did not survive the partition audit. Any other token is shown verbatim with the
  reading "engine refusal, not in the census list".
- Census availability, measured 2026-09-01 (buildings with 2 ≤ k ≤ 8 / total): Courtyard 296/362 · Sliver 312/637 ·
  Square 159/220 · Rectangle 82/109 · Corridor rectangle 67/94 · Slab 12/28 · Triangle 39/54 · Trapezoid 59/87 ·
  L 179/259 · U/T 213/269 · Complex 341/425. Every group has ≥ 10 candidates for test 05 and ≥ 20 members for the
  size tests. Sliver has no plate above 237 m²; its "big" and "very big" rows will be its largest plates, and the
  caption must say so through the m²-per-flat figure.

---

## 6. Tasks

### T01 — make `01` and `02` importable without running them

**What.** Wrap the executable parts of both scripts in functions guarded by `if __name__ == "__main__":`. No logic
changes.

**Why.** `04` must call the exact same `options()` and `apply_law()` the rules document was built with. Copying them
would fork the rule.

**How.**
- `01_cut_group_plans.py`: leave lines 1–125 (imports, constants, `cls`, `PROPOSED`, `NO_CORE_BY_DESIGN`, `rings_of`,
  `capture`, `gallery_ring`, `options`) at module level. Move `MIN_DRAW_TO_SHOW_SCHEME` (`:159`) up to module level.
  Put lines 127–149 (gpkg + census loading, `bygroup` / `perfloor` / `storeys`) into `def load_universe():` returning
  `geoms, rows, bygroup, perfloor, storeys`. Put lines 151–218 into `def main():` which starts with
  `geoms, rows, bygroup, perfloor, storeys = load_universe()`. End the file with `if __name__ == "__main__": main()`.
- `02_one_core_per_plate.py`: the loop body `:846-902` becomes `def apply_law(r):` — first line
  `if not r.get("dwellings"): return r`, last line `return r`; keep its `print`. Add `def main():` =
  `rows = json.load(open(SRC))`, `for r in rows: apply_law(r)`, the `json.dump` and the final `print`. End with
  `if __name__ == "__main__": main()`.

**How to test.**
```
.venv\Scripts\python.exe -c "import importlib.util as u; s=u.spec_from_file_location('m01', r'scripts/eu21/01_cut_group_plans.py'); m=u.module_from_spec(s); s.loader.exec_module(m); print([k for k in ('cls','options','capture','load_universe','main','ORDER','NO_CORE_BY_DESIGN') if hasattr(m,k)])"
.venv\Scripts\python.exe -c "import importlib.util as u; s=u.spec_from_file_location('m02', r'scripts/eu21/02_one_core_per_plate.py'); m=u.module_from_spec(s); s.loader.exec_module(m); print(callable(m.apply_law), callable(m.lobes_of), callable(m.main))"
git diff --stat -- scripts/eu21/01_cut_group_plans.py scripts/eu21/02_one_core_per_plate.py
```
Both imports must print without reading any gpkg or JSON (each returns in under 3 s). `git diff` of `02` must show
only indentation, the two `def` lines, the `return r` lines and the guard — report the `--stat` line counts. Do
**not** run either script.

### T02 — `04_group_tests.py`, and test 01 end to end

**What.** One script that builds any of the five tests: select → cut → law → check → JSON → HTML. Then run it for
test 1 and produce `TEST_01_three_per_group_2026-09-01.html`.

**Why.** The rules document shows one plate per group. The owner wants the same rule applied to many real plates and
checked, visibly, against the written acceptance rules.

**How — selection (deterministic).**
- Universe: `load_universe()`; a member is usable when its geometry exists in `geoms` and is (or after `buffer(0)`
  becomes) a `Polygon`. Centre it with `translate(g, -g.centroid.x, -g.centroid.y)`.
- Tests 1/3/5, N = 3/5/10: per group `cands = sorted(usable members with 2 <= _n <= 8, key=area_m2)`;
  `idx = sorted({round((i + 0.5) / N * (len(cands) - 1)) for i in range(N)})`; take `cands[i]`; if fewer than N
  candidates take them all. Draw each at its own `_n`.
- Tests 2/4, M = 3/5: `SIZES = [("small", 3), ("medium", 6), ("big", 9), ("very big", 12)]`,
  `TARGET_M2_PER_FLAT = 60`; per group and size `(label, n)`: `cands = sorted(usable members, key=lambda r:
  abs(area_m2 - n * TARGET_M2_PER_FLAT))`; take the first M whose `building_id` was not already taken by a smaller
  size in this group and test. Draw at the imposed `n`.
- `--limit L` caps the buildings per group (and per size) at L, for smoke runs only.

**How — one plate.**
```
opts, why = options(p, n, grp)
if not opts: verdict "REFUSED", token per §4
else: dpolys, cpoly, scheme, status, carea = opts[0]; dw, circ = capture(dpolys, cpoly)
      rec = {test, group, district, building_id, storeys, declared_dwellings, own_k, drawn_per_floor=n, size_label,
             area_m2 (plate, from the centred polygon), footprint rings, dwellings=dw, circulation=circ, scheme, status,
             circ_m2=round(carea, 1)}
      try: apply_law(rec)  except Exception as e: verdict "ERROR", token f"LAW_{type(e).__name__}", message str(e)[:120]
      then checks (below); verdict PASS / FAIL
```
Print one line per plate: `test group district id n scheme verdict elapsed_s`. Keep `apply_law`'s own print.

**How — checks (post-law rings).** `fp = Polygon(footprint[0], footprint[1:])`,
`flats = [Polygon(x[0], x[1:]) for x in dwellings]`, `cores = [Polygon(x[0], x[1:]) for x in circulation]`.
- **C1 coverage** — `cov = (Σ flat.area + Σ core.area) / fp.area`; pass if `0.999 <= cov <= 1.001`. Show `100.0 %`.
- **C2 one core** — `nc = len(cores)`; pass if `nc == 1`, or `grp == "SLIVER"` and `nc <= 1`. Show `nc`.
- **C3 count** — pass if `len(flats) == n`. Show `len(flats)/n`.
- **C4 rooms** — pass if every `lobes_of(f) is None` and the largest pairwise intersection area (flat/flat and
  flat/core) `< 0.02`. Show the worst overlap in m².
- **C5 simple** — pass if no zone has interiors, no zone `contains` another zone's `representative_point()`, and the
  max points per zone (`len(exterior.coords) - 1`) `<= 40`. Show max points.
- **C6 facade** — `contact = sbuf(flat, 0.05).intersection(fp.exterior).length` per flat; pass if
  `min(contact) >= 2.50`. Show the min in m.
- **C7 share** — `circ_pct = Σ core.area / fp.area * 100`; chip class `info` if `6 <= circ_pct <= 12`, else `warn`;
  never pass/fail. Show `x.x %`.
- Also store `m2_per_flat = Σ flat.area / n` and `pts_total`.
- Verdict `PASS` iff C1–C6 pass, else `FAIL`.

**How — JSON.** `openubem/outputs/eu_evidence/EU-21/rules_tests/test_0N.json`:
`{"test": N, "title": ..., "built": ISO timestamp, "selection": one-sentence rule, "plates": [rec + checks + verdict +
token + message]}`.

**How — HTML.** Head exactly as `03:640-645` builds it (doctype, charset, viewport, the frozen CSS with the `<title>`
swapped to `Rules Test 0N`, then the extra style block). Body inside `<div class="wrap">`:
1. `header.mast` — eyebrow `EU-21 · rules test 0N · companion to RULES_dwelling_layout_groups_2026-09-01`; `h1` =
   the test title (`Test 01 — three buildings per group`, `Test 02 — four floor sizes, three buildings each`,
   `Test 03 — five buildings per group`, `Test 04 — four floor sizes, five buildings each`, `Test 05 — ten buildings
   per group`); `.lede` = what the test does, in three sentences; `.meta` = date, `census: …/morphology_census.csv`,
   `script: scripts/eu21/04_group_tests.py --test N`, `law: D-EU-64`.
2. `.tally` — plates tried · plans drawn · refused by the rule · law errors · all six checks passed · groups with
   every drawn plate passing.
3. `section.block` **CHECKS** — C1–C7 as a `<ul>`, one line each, in the words of §5 with the tolerance in a `<code>`
   and the source document named.
4. `section.block` **SELECTION** — the selection rule of this test in three bullets; a line saying that a refused or
   failing plate is shown and counted, never replaced.
5. `section.block` **RESULTS** — `table.cov`: group · plates · drawn · refused · pass · fail · commonest failed check ·
   commonest refusal token; `tfoot` = fleet. Non-zero fail / refused cells get class `bad`.
6. `section.block` **GROUPS** — one `article.sheet` per group, `id=<GROUP>`. `.titleblock`: `.id` = `NN  Title`,
   `.sub` = `n plates · pass p · fail f · refused r · ` plus
   `<a href="../RULES_dwelling_layout_groups_2026-09-01.html#GROUP">sheet NN</a>`; `.specs` holds a tag `ok`
   ("every drawn plate passes") when so, else `bad` ("f of d drawn plates fail"). Inside, one `.pane` per size row
   (tests 2/4: four panes headed `small — 3 flats per floor — plates nearest 180 m²`, …; tests 1/3/5: one pane headed
   `own flats per floor`), each holding a `.figs` grid of cards. A card is a `.fig`: `drawplan(rec, uid)` or, when
   refused / error, `<div class="failbox"><span class="tok">TOKEN</span><p>reading</p></div>`; `.cap` line 1 =
   `Madrid · way/123 · 5 storeys · 12 dwellings declared · 210 m²`; `.cap` line 2 = `drawn at 3 · ruled_grid_2x2 ·
   rule in force · 63 m² per flat`; then `.checks` = seven chips `<span class="chk ok|bad|info|warn">C1 100.0 %</span>`
   … `C7 9.1 %`. Give `.fig` a `flex:1 1 300px` in the extra style so three cards fit a row at 1180 px.
7. `section.block` **READ** — legend as `03:606-618` (flat swatch, core swatch, heavy outline, 10 m bar, tags), plus
   one sample of each chip class with its meaning.
8. `footer` — what this is (a geometry test of the written rules, built from the same engine call and the same
   post-pass as the rules document), what it is not (no energy result, `D-EU-55`; the context rules `D-EU-40` are
   simulation rules and are not tested by a floor plan), and the `mono` line with the census, JSON and script paths.

Extra style block (append to the rules copied from `03`'s `extra`):
`.checks{display:flex;flex-wrap:wrap;gap:4px;margin-top:2px}`
`.chk{font-family:"IBM Plex Mono",monospace;font-size:10.5px;padding:2px 6px;border:1px solid var(--rule);border-radius:2px;color:var(--ink-2);background:var(--sheet)}`
`.chk.ok{border-color:var(--ok);color:var(--ok);background:var(--ok-soft)}`
`.chk.bad{border-color:var(--alert);color:var(--alert);background:var(--alert-soft)}`
`.chk.info{color:var(--muted)}` `.chk.warn{border-color:var(--accent);color:var(--accent);background:var(--accent-soft)}`
`.failbox p{font-size:12.5px;color:var(--ink-2)}` `.fig{flex:1 1 300px}`.

**How to test.**
```
.venv\Scripts\python.exe scripts/eu21/04_group_tests.py --test 1 --limit 1      # smoke: 1 plate per group, 11 lines
.venv\Scripts\python.exe scripts/eu21/04_group_tests.py --test 1               # full: 33 plates
.venv\Scripts\python.exe scripts/eu21/04_group_tests.py --test 1 --render-only  # HTML from JSON, no engine
.venv\Scripts\python.exe -c "import json,collections as c; d=json.load(open('openubem/outputs/eu_evidence/EU-21/rules_tests/test_01.json')); P=d['plates']; print(len(P), c.Counter(p['verdict'] for p in P), c.Counter(p.get('token') for p in P if p['verdict'] in ('REFUSED','ERROR'))); [print(g, c.Counter(p['verdict'] for p in P if p['group']==g)) for g in dict.fromkeys(p['group'] for p in P)]"
grep -c 'class="fig"' docs/docs_ACTIVE/europeanLocations/rules/tests/archive/TEST_01_three_per_group_2026-09-01.html
```
Report: the verdict counter, the token counter, per-group verdict line, wall time per plate (min / median / max), the
`grep -c` (must equal the plate count) and the HTML byte size. Then stop at CP-1.

### T03 — tests 03, 02, 05, 04

**What.** Run the same script for the other four tests.

**How.** In this order, each as its own run: `--test 3` (55 plates) · `--test 2` (132 plates, 66 of them instant
refusals at 9 and 12 outside Courtyard) · `--test 5` (110) · `--test 4` (220, 110 instant). Run in the background
with the output logged when a run is expected to exceed 5 minutes (use the per-plate time measured in T02). Then
`--render-only` for each only if the HTML changed after CP-1.

**How to test.** The counter command per test (change the file name), plus for tests 2 and 4: the number of
`DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` refusals must equal the number of non-Courtyard plates at n = 9 and
n = 12; every Courtyard plate at 9 / 12 either draws by `courtyard_gallery_ring` or carries its own token. Report
per test: verdict counter, token counter, per-group line, wall time, `grep -c 'class="fig"'`, HTML size. Then stop at
CP-2.

### T04 — close the task

**What.** Progress log entries (one per task) under §8 of this plan; a debug-reference bullet for every error solved
on the way. Nothing else — the director prompt and the memory are the director's.

---

## 7. Stop-and-report points

- **CP-1 — after T02.** Test 01 built. The director audits the HTML and the counters before the other four are run.
  Do not start T03 before CP-1 is signed in this file.
  **CP-1 SIGNED 2026-09-01 (director).** Audited: headless render in house style; 33 `class="fig"`, 10 fail boxes = 9 refusals + 1 law error; tally 24 drawn / 21 pass all six / 8 groups fully passing; refusal token is the engine's own `fallback_reason`; only planned files touched (`git status --short`); `--render-only` byte-identical. T03 may start.
- **CP-2 — after T03.** All five sheets built. The director audits and closes.
  **CP-2 SIGNED 2026-09-01 (director).** Audited: five sheets, `class="fig"` = 33 / 132 / 55 / 220 / 110 = plate counts; fail boxes 10 / 89 / 14 / 150 / 33 = refused + law errors per test; headless renders of tests 01, 04 and 05 in house style (size rows as panes, refusal boxes carry the engine token); density cross-check 160/160 non-Courtyard plates at 9 and 12 refused by rule; only planned files touched. Closed.

---

## 8. Progress log

(executor appends one entry per task: `#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test
status / Notes)

#### T01 — make `01` and `02` importable without running them — completed 2026-09-01

**Artifacts.**
- `scripts/eu21/01_cut_group_plans.py` — module-level loading (old `:127-149`) moved into `load_universe()`
  returning `geoms, rows, bygroup, perfloor, storeys`; `MIN_DRAW_TO_SHOW_SCHEME` (old `:159`, with its comment)
  moved to module level, ahead of `load_universe`; selection loop (old `:151-218`) moved into `main()`, starting
  with `geoms, rows, bygroup, perfloor, storeys = load_universe()`; ends with `if __name__ == "__main__": main()`.
  No logic changed — the loop body was reindented one level, nothing else.
- `scripts/eu21/02_one_core_per_plate.py` — loop body (`:846-902`) became `def apply_law(r):` (first line
  `if not r.get("dwellings"): return r`, last line `return r`, its own `print` kept); `def main():` added
  (`rows = json.load(open(SRC))`, `for r in rows: apply_law(r)`, the `json.dump` + `print`); ends with
  `if __name__ == "__main__": main()`.

**Test status.** Both import smoke tests (`importlib.util.spec_from_file_location`) printed the expected symbol
lists / `callable()` checks instantly, with no gpkg/JSON read triggered — confirms importing executes only
definitions. `git diff --stat`: `scripts/eu21/01_cut_group_plans.py | 195 +++++----` ·
`scripts/eu21/02_one_core_per_plate.py | 777 ++++++++++++++++++++++++++++++++--` · `2 files changed, 857
insertions(+), 115 deletions(-)`. Neither script was run.

**Deviations.** None from the plan's instructions. Note for the audit: both files were already uncommitted/dirty
against `HEAD` (`88964203`) before this task started (git status at session start already showed both `M`), so the
`--stat` totals above include that pre-existing owner diff, not only T01's edit. T01's own edit to `02` is small
(net +9 lines: the two new `def` lines, `continue`→`return r`, the trailing `return r`, and the `__main__` guard);
to `01` it is the loop-body reindent plus the two new `def` lines and the guard — verified by re-reading the file
after edit, no other lines touched.

**Notes.** None.

#### T02 — `04_group_tests.py`, and test 01 end to end — completed 2026-09-01

**Artifacts.**
- `scripts/eu21/04_group_tests.py` (new) — imports `01`/`02` via `importlib.util.spec_from_file_location`; copies
  `FILLS`, `_bounds`, `_path`, `_centroid`, `drawplan`, `TITLE`, `DSHORT`, `CLOSE` verbatim from `03`; selection
  (`select_own`, `select_size`), engine call + `D-EU-64` law (`build_plate`), checks C1–C7 (`run_checks`), JSON
  writer, HTML builder (`build_html`). CLI: `--test {1,2,3,4,5,all}`, `--render-only`, `--limit N`.
- `openubem/outputs/eu_evidence/EU-21/rules_tests/test_01.json` (new, 59832 bytes, 33 plates).
- `docs/docs_ACTIVE/europeanLocations/rules/tests/archive/TEST_01_three_per_group_2026-09-01.html` (new, 94430 bytes).

**Test status.**
- Smoke (`--test 1 --limit 1`): 11 lines (one per group) — 8 `PASS`, 3 `REFUSED` (`L_SHAPE`, `U_OR_T_SHAPE`,
  `COMPLEX_MULTI_WING`, all `L_SHAPE_DECOMPOSITION_FAILED`).
- Full (`--test 1`, 33 plates). Verdict counter: `PASS 21 · REFUSED 9 · FAIL 2 · ERROR 1`. Token counter:
  `L_SHAPE_DECOMPOSITION_FAILED ×9 · LAW_GEOSException ×1` (SLAB `way/435943258`, a `TopologyException` inside
  `apply_law`'s post-pass on this real plate — a finding, left as `verdict ERROR`, not fixed, per rule 7).
  Per-group verdicts: COURTYARD {PASS 2, FAIL 1} · SLIVER {PASS 3} · SQUARE {PASS 3} · RECTANGLE {PASS 2,
  REFUSED 1} · CORRIDOR_RECTANGLE {PASS 2, REFUSED 1} · SLAB {PASS 1, ERROR 1, FAIL 1} · TRIANGLE {PASS 3} ·
  TRAPEZOID {PASS 3} · L_SHAPE {REFUSED 2, PASS 1} · U_OR_T_SHAPE {REFUSED 2, PASS 1} · COMPLEX_MULTI_WING
  {REFUSED 3}. Wall time per plate: min 0.051 s, median 0.114 s, max 5.963 s (CORRIDOR_RECTANGLE
  `way/435927693`, refused at n=8, engine tries every scheme before refusing). `grep -c 'class="fig"'` = 33,
  equal to the plate count. `--render-only` reproduces byte-identical HTML (94430 bytes) from the JSON alone.

**Deviations.** Two implementation choices the plan left to normal judgement, neither a rule change: (a) numeric
display precision for check "show" values where §5 gives no exact format beyond its own C1/C7 examples (C1/C7 one
decimal percent; C4/C6 two-decimal m²/m; C2/C3/C5 integers) — consistent throughout, not stated character-for-
character in §5; (b) `--limit` truncates the already-selected list (the selection algorithm itself always runs
with the true N/M, per §"How — selection") rather than shrinking N/M before selecting. Also worth recording: the
built HTML head has no `<title>` tag, because `css = FROZEN.read_text().splitlines()[2:122]` (03:8, copied
verbatim per the plan) excludes the frozen file's own `<title>` line (file index 1), so the
`css.replace("<title>Dwelling Plans Redrawn</title>", ...)` swap in 03:643 is a no-op — confirmed this is not new
to `04`: `RULES_dwelling_layout_groups_2026-09-01.html` (03's own output) has zero `<title>` tags either.
Reproduced faithfully per the plan's "Head exactly as 03:640-645 builds it" instruction; not fixed, since `03` is
off-limits (rule 2) and the observed behavior matches the existing reference document.

**Notes.** Non-fatal shapely `RuntimeWarning`s ("divide by zero encountered in buffer", "invalid value encountered
in buffer") appear on stderr during the full `--test 1` run, on certain real degenerate plates; the run completes
and produces full, correct output regardless. They originate inside imported engine/law buffer operations (`01`/
`02`/`openubem/geometry/`), not in `04_group_tests.py`; not chased, per rule 7 (do not fix a failing plate) and
rule 2 (the engine is the thing under test; `01`, `02`, `openubem/geometry/` are off-limits). No entry was added
to `debugs/DEBUG_REFERENCES_european_locations.md`: nothing crashed during T01 or T02 — the `LAW_GEOSException`
and every `REFUSED`/`FAIL` plate are the test's findings, not bugs solved on the way.

**CP-1.** Test 01 built as above. Awaiting the director's audit of the HTML and counters before T03 starts.

#### T03 — tests 03, 02, 05, 04 — completed 2026-09-01

**Artifacts.**
- `openubem/outputs/eu_evidence/EU-21/rules_tests/test_02.json` (224190-byte HTML companion, see below), `test_03.json`,
  `test_04.json`, `test_05.json` (new).
- `docs/docs_ACTIVE/europeanLocations/rules/tests/archive/TEST_02_floor_sizes_x3_2026-09-01.html`,
  `TEST_03_five_per_group_2026-09-01.html`, `TEST_04_floor_sizes_x5_2026-09-01.html`,
  `TEST_05_ten_per_group_2026-09-01.html` (new). All five sheets planned in §1 now exist.

Run order was 3 · 2 · 5 · 4, per the plan. Every run finished with exit code 0 in well under 5 minutes (max 40 s,
test 4), so none needed a background run and none needed a `--render-only` rebuild (HTML was produced directly by
each `--test N` run, untouched afterward).

**Test status.**
- **Test 03** (55 plates, 10 s). Verdict: `PASS 38 · REFUSED 11 · FAIL 3 · ERROR 3`. Token:
  `L_SHAPE_DECOMPOSITION_FAILED ×9 · LAW_GEOSException ×3 · PARTITION_AUDIT_FAILED ×2`. Per group: COURTYARD
  {PASS 3, FAIL 2} · SLIVER {PASS 5} · SQUARE {PASS 4, FAIL 1} · RECTANGLE {PASS 3, ERROR 1, REFUSED 1} ·
  CORRIDOR_RECTANGLE {PASS 4, ERROR 1} · SLAB {PASS 2, REFUSED 2, ERROR 1} · TRIANGLE {PASS 4, REFUSED 1} ·
  TRAPEZOID {PASS 5} · L_SHAPE {PASS 4, REFUSED 1} · U_OR_T_SHAPE {REFUSED 3, PASS 2} · COMPLEX_MULTI_WING
  {REFUSED 3, PASS 2}. Wall time/plate: min 0.044 s, median 0.137 s, max 0.762 s. `grep -c 'class="fig"'` = 55 =
  plate count. HTML size 150819 bytes.
- **Test 02** (132 plates, 26 s). Verdict: `REFUSED 85 · PASS 33 · FAIL 10 · ERROR 4`. Token:
  `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8 ×61 · L_SHAPE_DECOMPOSITION_FAILED ×17 · PARTITION_AUDIT_FAILED ×6 ·
  LAW_GEOSException ×4 · INTERIOR_RING_COURTYARD_UNFOLD_FAILED ×1`. Per group: COURTYARD {PASS 6, FAIL 4,
  REFUSED 2} · SLIVER {REFUSED 6, PASS 5, ERROR 1} · SQUARE {REFUSED 7, PASS 4, ERROR 1} · RECTANGLE {REFUSED 7,
  PASS 4, FAIL 1} · CORRIDOR_RECTANGLE {REFUSED 9, PASS 2, FAIL 1} · SLAB {REFUSED 9, PASS 3} · TRIANGLE
  {REFUSED 8, PASS 2, ERROR 1, FAIL 1} · TRAPEZOID {REFUSED 6, PASS 5, FAIL 1} · L_SHAPE {REFUSED 12} ·
  U_OR_T_SHAPE {REFUSED 9, FAIL 2, ERROR 1} · COMPLEX_MULTI_WING {REFUSED 10, PASS 2}. Wall time/plate: min
  0.000 s, median 0.071 s, max 7.297 s. `grep -c 'class="fig"'` = 132 = plate count. HTML size 224190 bytes.
  Cross-check (§ How to test): non-Courtyard plates at n=9/12 = 60 = `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8`
  count restricted to those 60 plates = 60/60, exact. Courtyard at n=9/12 = 6 plates: 5 drew by
  `courtyard_gallery_ring` (3 PASS, 2 FAIL); 1 (`28782`'s sibling `30127`, n=9) was `REFUSED` carrying the shared
  `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` token rather than a courtyard-specific one — flagged, not fixed,
  per rule 7 (§ Notes).
- **Test 05** (110 plates, 19 s). Verdict: `PASS 65 · REFUSED 22 · FAIL 12 · ERROR 11`. Token:
  `L_SHAPE_DECOMPOSITION_FAILED ×20 · LAW_GEOSException ×11 · INTERIOR_RING_COURTYARD_UNFOLD_FAILED ×1 ·
  PARTITION_AUDIT_FAILED ×1`. Per group: COURTYARD {PASS 7, ERROR 1, REFUSED 1, FAIL 1} · SLIVER {PASS 7, FAIL 2,
  ERROR 1} · SQUARE {PASS 7, ERROR 2, FAIL 1} · RECTANGLE {PASS 8, ERROR 2} · CORRIDOR_RECTANGLE {PASS 6, FAIL 2,
  REFUSED 1, ERROR 1} · SLAB {PASS 5, REFUSED 3, ERROR 1, FAIL 1} · TRIANGLE {PASS 10} · TRAPEZOID {PASS 9,
  FAIL 1} · L_SHAPE {REFUSED 5, ERROR 2, PASS 2, FAIL 1} · U_OR_T_SHAPE {REFUSED 5, PASS 3, FAIL 2} ·
  COMPLEX_MULTI_WING {REFUSED 7, ERROR 1, FAIL 1, PASS 1}. Wall time/plate: min 0.018 s, median 0.132 s, max
  0.927 s. `grep -c 'class="fig"'` = 110 = plate count. HTML size 266584 bytes.
- **Test 04** (220 plates, 40 s). Verdict: `REFUSED 137 · PASS 50 · FAIL 20 · ERROR 13`. Token:
  `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8 ×101 · L_SHAPE_DECOMPOSITION_FAILED ×28 · LAW_GEOSException ×13 ·
  PARTITION_AUDIT_FAILED ×6 · INTERIOR_RING_COURTYARD_UNFOLD_FAILED ×1 · NARROW_FOOTPRINT_LT_8M ×1`. Per group:
  COURTYARD {FAIL 10, PASS 6, REFUSED 2, ERROR 2} · SLIVER {REFUSED 11, PASS 5, FAIL 2, ERROR 2} · SQUARE
  {REFUSED 11, PASS 7, ERROR 1, FAIL 1} · RECTANGLE {REFUSED 11, PASS 7, FAIL 1, ERROR 1} · CORRIDOR_RECTANGLE
  {REFUSED 14, ERROR 3, PASS 2, FAIL 1} · SLAB {REFUSED 13, PASS 5, ERROR 2} · TRIANGLE {REFUSED 12, PASS 6,
  ERROR 1, FAIL 1} · TRAPEZOID {REFUSED 10, PASS 9, FAIL 1} · L_SHAPE {REFUSED 20} · U_OR_T_SHAPE {REFUSED 16,
  FAIL 3, ERROR 1} · COMPLEX_MULTI_WING {REFUSED 17, PASS 3}. Wall time/plate: min 0.000 s, median 0.071 s, max
  7.223 s. `grep -c 'class="fig"'` = 220 = plate count. HTML size 349802 bytes. Cross-check: non-Courtyard plates
  at n=9/12 = 100 = `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` count restricted to those 100 plates = 100/100,
  exact. Courtyard at n=9/12 = 10 plates: 9 drew by `courtyard_gallery_ring` (6 PASS, 3 FAIL/ERROR incl. one
  `LAW_GEOSException`); 1 (building `30127`, n=9 — the same building as in test 02) was `REFUSED` with the same
  shared `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` token, consistent across both tests.

**Deviations.** None from the plan's instructions. No `--render-only` reruns were needed (nothing changed the HTML
after each direct `--test N` build). No background runs were needed (all four finished in ≤ 40 s, far under the
5-minute background threshold).

**Notes.** 🔴 Finding, not fixed (rule 7): in both tests 02 and 04, one specific COURTYARD building (`30127`, drawn
at n=9) is refused with the shared `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` token instead of drawing via
`courtyard_gallery_ring` or carrying a courtyard-specific token — contrary to the plan's §1 statement that
Courtyard "may draw at 9 and 12" without the density cap. Every other Courtyard n=9/12 plate (5 of 6 in test 02,
9 of 10 in test 04) does draw by `courtyard_gallery_ring`, so the exception is building-specific, not systemic;
reported here per rule 10, not resolved. No unhandled tracebacks appeared in any of the four run logs — every
`ERROR` verdict is a caught `LAW_GEOSException`, exactly as designed in T02; the same non-fatal shapely
`RuntimeWarning`s noted in T02 recurred on stderr and are not chased, for the same reasons. No new entry was added
to `debugs/DEBUG_REFERENCES_european_locations.md`: nothing crashed during T03 — every `REFUSED`/`FAIL`/`ERROR`
plate is the test's finding, not a bug solved on the way.

**CP-2.** All five sheets built as above. Awaiting the director's audit and close.

#### T04 — close the task — completed 2026-09-01 (director-written; nothing executable was left)

**Artifacts.** None new. Progress-log entries T01–T03 above are the executor's.
**Deviations.** Written by the director rather than a fourth executor dispatch: the only content owed was a debug-reference bullet per error *solved*, and none was solved — every `REFUSED` / `FAIL` / `ERROR` plate is a finding of the test, left untouched under §2 rule 7. One `[OPEN]` bullet for the `apply_law()` `TopologyException` (32 of 550 plates) is registered in `debugs/DEBUG_REFERENCES_european_locations.md` by the director.
**Test status.** CP-2 signed (§7).
**Notes.** Findings carried to the director prompt §5 for the owner to number (`D-EU-65` / `FINDING 225` still free).

# MEASUREMENT — T20: bounding OPEN-18 and OPEN-20

**Date:** 2026-08-19 · **Task:** T20 of `PLAN_twenty-items-2026-08-19.md`. Two items, one task, each
given a bound rather than a fresh measurement — per the plan's own instruction, no new runs, no
proposals for new cities.

## (a) OPEN-18 — Q3, the √S vertical-form distortion

### What is unreachable, stated precisely and re-confirmed by citation at HEAD

Q3's mechanism is `layout_assigner.scale_baseline_idf()` — the same function T14/T15/T18 examined
this pass — scaling a prototype's plan vertices by `√area_scale_ratio` while height is preserved
(Z coordinates untouched, `scale_baseline_idf`, `layout_assigner.py:1023-1027`). The "obvious first
candidate" fix, `match_storeys()`'s `Zone.Multiplier` mechanism, is **confirmed still structurally
unable to reach Q3's population**, by direct re-citation of its own docstring at HEAD
(`layout_assigner.py:546-549`):

> `n_real < n_proto: "fallback_shorter". D3(b) (band deletion) was measured in A3 and rejected — it
> requires per-archetype HVAC/interzone surgery, out of scope for this plan. D5 fallback: caller keeps
> today's single-scalar-plate behaviour...`

Q3's population is buildings **smaller** than their assigned prototype (`n_real < n_proto`, S well
under 1 — median `MidriseApartment` S = 0.054, register), which is exactly the branch this docstring
says returns `fallback_shorter` and stays on "today's single-scalar-plate behaviour" — i.e. the
prototype's full storey count and full zone set are kept, only uniformly shrunk in plan. Band deletion
(the mechanism that would actually remove zones for the shorter case) is **explicitly rejected as
out of scope**, unchanged since it was last measured. `match_storeys()` only ever expresses
`n_real > n_proto`; it was never going to reach the shorter case, and nothing in this pass's reading
of the code shows that boundary has moved.

### The residual distortion, on small buildings in cold cells

**Not reliably quantifiable from artifacts currently on disk, for the same structural reason found
independently by T15/T18 this pass**: `layout_assign` is the only mode this distortion can be
measured on (Q3's own mechanism is `layout_assign`-specific — `auto` and the other three modes never
call `scale_baseline_idf()`, they build custom zone geometry directly from the real footprint), and
no `layout_assign` artifact on disk today is both (1) HEAD-consistent and (2) parseable for EUI by
the production method. §3/§4 of `extra/MEASUREMENT_open-03_vintage-at-head.md` traces this exactly:
every fresh `layout_assign` rebuild in this arc (including today's) used `trim_outputs=True`, which
strips the zone-level `Output:Variable` the parser's `layout_assign` zone-integrity gate requires,
and the only pre-existing generations with parseable numbers (`t17`–`t20_layout_assign_eui.csv`) carry
independently-confirmed archetype-label drift (T15, this pass) that makes them unsafe to trust for a
size-stratified, cold-cell-specific distortion measurement without re-verifying every row's archetype
first — out of scope for this task.

**What would quantify it:** a `layout_assign` rebuild of a size-stratified sample (small buildings,
S well under 1, matched by archetype) in the coldest cells (`nyc_rural`/`nyc_centre`, the register's
own climate proxy for "cold"), built with `trim_outputs=False`, joined against `auto`-mode run-4
results for the same buildings by `osm_id`. This is the same artifact §6 of the T18 report names,
reused here for a different slice of the same underlying gap.

## (b) OPEN-20 — wider validation matrix, what the current design does and does not support

### The current matrix, re-confirmed against run 4 (F4)

Twelve cells, three cities × four urban-form rings: `{austin, la, nyc} × {centre, rural, suburban,
urban}`. 8,160 buildings (F4), independently re-confirmed by this pass's own T13 script (`.err` scan
totalled exactly 8,160 across the 12 `sim_out` directories). Three climate zones represented at the
city level: Austin (ASHRAE 2A, hot-humid), NYC (ASHRAE 4A, mixed-humid), LA (ASHRAE 3B,
cooling-dominated marine). This is unchanged in shape since the item was opened 2026-06-17.

### What it supports

An external-validity claim of the form: *"results generalise across the urban-form gradient (four
density/context rings) within each of three represented US climate zones, for the archetype mix and
building-stock composition present in these three specific metro areas."* Every published fleet
statistic (F1's `153.8231 kWh/m²`) is a pooled statistic over exactly this population — its precision
within this population is not in question; its reach beyond it is what OPEN-20 bounds.

### What it does NOT support

- **No climate zones outside 2A/3B/4A are represented at all** — nothing here bears on cold-climate
  zones (5–8), hot-dry zones (2B/3B-desert), or any non-US climate classification.
- **No claim about building-stock composition elsewhere.** The archetype mix, vintage distribution,
  and construction practices sampled are specific to these three US metros; a European, or even a
  different US metro's, building stock is not represented by extension.
- **The urban-form rings are defined once, per city, not validated as a general typology.** Whether
  "rural"/"suburban"/"urban"/"centre" as constructed here transfers as a meaningful category boundary
  to a city not in the sample is untested.
- **OPEN-19 bounds this further for LA specifically**, and by the same climate-insensitive-prototype
  mechanism plausibly for Austin too (§2 of `extra/MEASUREMENT_open-19_title24-scoping.md`): the
  underlying simulation model itself does not yet vary construction/HVAC parameters by climate zone,
  so even within the three represented cities, the *physical* basis for cross-climate generalisation
  is currently weaker than the geographic sampling alone would suggest — the matrix samples three
  climates, but the model does not yet fully differentiate its response to them.

No new runs and no proposal for additional cities are made by this task, per its own instruction.

## Artifacts

None new — this task cites the companion T18/T15 reports and F4; no additional script was needed.

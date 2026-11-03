# Deep-Research Prompt L10 — LARGE & COMPLEX BUILDING LAYOUT (hospitals, large hotels, deep-plan / high-rise — department & multi-core zoning)

> SCOPE GUARD — READ FIRST. This prompt covers the archetypes a simple corridor (`L06`/`L08`) or single
> core/perimeter (`L09`) cannot represent: **hospitals, large hotels, deep-plan and high-rise buildings**
> whose floor plates are too large/deep/functionally-mixed for one core+perimeter ring or one corridor.
> Deliver the functional/department zoning conventions, multi-core plans, and deep-floorplate interior
> subdivision. Do NOT re-derive corridor rules (`L06`) or App-G core/perimeter (`L03`) — extend them.
> See `00_README_layoutgenerator_prompt_set.md` for shared facts.

---

## What this document is

The complex-building playbook. A hospital floor is a set of *departments* (surgery, patient wards,
diagnostics, labs) each with its own program; a large hotel floor mixes guest-room wings with lobby/
ballroom/back-of-house; a very deep or high-rise plate has interior zones beyond one perimeter ring. The
user flagged these explicitly ("hospitals or larger hotels we can search for them"). The manager needs to
know whether OpenUBEM should attempt genuine department zoning or apply a *defensible simplification*
(e.g. deep-plan → concentric core + perimeter band + intermediate zone, or hospital → one dominant space
type per zone) that stays within the DOE-prototype loads it already has.

## Role

Healthcare / hospitality / high-rise BEM zoning research analyst. Ground the department taxonomy in the
DOE Hospital / Outpatient / LargeHotel prototype documentation (their as-modeled department zones),
healthcare design standards (FGI Guidelines, Neufert healthcare, Time-Saver), and high-rise/deep-plan BEM
zoning practice. Distinguish what is *architecturally* real (many departments) from what is *thermally
necessary* for UBEM (a tractable zone count) — OpenUBEM needs the latter.

## Why this matters (so you scope correctly)

These archetypes are few in number but huge in floor area and energy, so a crude single-zone treatment
biases city EUI. But full department zoning is unbounded complexity and has no OSM data to place
departments. The manager needs a *middle path*: the minimal, defensible zone scheme (grounded in the DOE
prototype's own zoning) that captures the deep-plan core/perimeter split and the dominant program mix,
without inventing department locations OpenUBEM cannot know.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — As-modeled complex-prototype zoning

| Prototype | Departments / zone groups (as modeled by DOE) | Thermal zones per floor | Deep-plan handling (concentric zones?) | Source |
|---|---|---|---|---|
| Hospital |  |  |  |  |
| Outpatient |  |  |  |  |
| LargeHotel |  |  |  |  |
| LargeOffice (deep plate) |  |  |  |  |
| TallBuilding / high-rise |  |  |  |  |

### Table 2 — Deep-floorplate subdivision (beyond one perimeter ring)

| Plate depth condition | Recommended zoning | Number of concentric bands / interior zones | Source |
|---|---|---|---|
| Depth ≤ 2× perimeter (15 ft each side) | core + perimeter (App-G) |  |  |
| Depth 2–4× perimeter | ? |  |  |
| Very deep (>4× perimeter) | ? |  |  |
| Atrium / lightwell present | ? |  |  |

### Table 3 — Placing departments without location data

| Question | Defensible OpenUBEM approach | Source |
|---|---|---|
| Can OSM tell us where a hospital's surgery vs. wards are? (No?) — so what's the fallback? |  |  |
| Should complex buildings use area-weighted mixed space type per zone instead of located departments? |  |  |
| Does the DOE prototype itself place departments, or use representative floors? |  |  |
| Is a "dominant program + core/perimeter" simplification defensible for UBEM? |  |  |

### Table 4 — Fit to OpenUBEM

| Question | Answer + source |
|---|---|
| Minimum zones/floor for a hospital to not bias EUI, without inventing department locations? |  |
| Should high-rise (TallBuilding, currently forced per-floor) get core/perimeter/deep-plan zoning? |  |
| Do large hotels reuse the `L08` guest-room-wing method for room floors + a distinct podium treatment? |  |
| Where is single-zone-per-floor an acceptable fallback for these archetypes? |  |

---

## Part C — Synthesis (the complex-building branch spec)

Give: (1) the **minimal defensible zone scheme per complex archetype** — grounded in the DOE prototype's
own zoning, not invented departments; (2) the **deep-plate subdivision rule** (how many concentric zones
by depth) with cited thresholds or GAP; (3) an explicit position on **located departments vs. mixed/
dominant space type** given OpenUBEM has no interior data; (4) the fallback to single-zone-per-floor and
when it is acceptable. Every threshold cited or flagged GAP.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C branch spec.
3. Cite DOE prototype / healthcare standard / BEM practice per rule.
4. **"Confidence and caveats":** which complex archetype's tractable zoning is least evidenced.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Recommend a *bounded, tractable* zone scheme** — no unbounded department enumeration OpenUBEM can't
  place.
- **Give the deep-plate concentric-zone rule** with cited depth thresholds (zero-fitted-parameters).
- **State explicitly where single-zone-per-floor remains the honest fallback.**
- **No fabricated precision;** flag GAPs. **Stay on topic** — large/complex buildings only; simple
  corridor is `L06`/`L08`, simple core/perimeter `L09`.

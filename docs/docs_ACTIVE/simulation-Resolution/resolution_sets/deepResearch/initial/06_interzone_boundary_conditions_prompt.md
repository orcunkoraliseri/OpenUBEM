# Deep-Research Prompt 06 — INTER-ZONE BOUNDARY CONDITIONS & thermal coupling (across all resolution modes)

> SCOPE GUARD — READ FIRST. This is an **EnergyPlus surface-boundary** task spanning all three modes.
> The deliverable is the correct **Outside Boundary Condition** for every internal surface that
> appears or disappears as resolution changes — inter-floor slabs, core↔perimeter walls,
> perimeter↔perimeter walls, party walls — plus whether zones are **thermally coupled or adiabatic**.
> It is NOT about loads (Prompt 04/08) or geometry cutting (Prompt 03). If you are writing about
> anything other than **a surface boundary condition, its construction, and the source**, stop and
> return to the tables. See `00_README_resolution_prompt_set.md` for modes, roster, conventions.

---

## What this document is

A fill-in-the-blanks request resolving the surface bookkeeping that changes with resolution. As you go
building → floor → zone, new internal surfaces appear (floors between storeys, walls between
core/perimeter). Each must be assigned an EnergyPlus boundary condition (`Adiabatic`, `Surface`
interzone, `Outdoors`, `Ground`). Getting this wrong silently mis-distributes energy. Treat each cell
as a question; fill with a sourced value or a GAP.

## Role

Building-energy-modelling research analyst. Trace every rule to: the **EnergyPlus Input-Output
Reference** (`BuildingSurface:Detailed` Outside Boundary Condition options; `Construction:InternalSource`;
surface matching / `intersect_match`; `ZoneMixing` / `AirflowNetwork` for inter-zone air), the
**DOE/PNNL prototype** conventions (how they set interzone vs adiabatic surfaces), and **EnergyPlus
Engineering Reference** on interzone heat transfer. SI + IP where relevant.

## Why this matters (so you scope correctly)

`Adiabatic` = zero heat flow (assumes the neighbour zone is identical temperature) — cheap, hides
inter-zone transfer. `Surface` interzone = full conduction (+ optional radiation/air) between two
matched zones — physical, costlier, requires matched vertices. The choice for inter-floor slabs,
core↔perimeter partitions, and party walls determines whether perimeter heating bleeds into the core,
and whether the middle of a tower is correctly mild. OpenUBEM also already runs `intersect_match` and
has had **inter-floor vertex-mismatch fatals** — so the boundary scheme must be robust to real
geometry. We need the sourced convention.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Boundary condition per internal surface type

| Internal surface | Appears in mode(s) | Recommended boundary condition | Construction | Source |
|---|---|---|---|---|
| Floor/ceiling between stacked floors | floor, zone | (adiabatic vs interzone `Surface`) | | |
| Core ↔ perimeter vertical partition | zone | | | |
| Perimeter ↔ perimeter vertical partition | zone | | | |
| Party wall to attached neighbour | all (urban) | | | |
| Ground floor underside | floor, zone | `Ground` / slab | | |
| Top floor roof | floor, zone | `Outdoors` | | |
| Single-zone whole-building omitted inter-floors | building | (InternalMass — see Prompt 01) | | |

### Table 2 — Adiabatic vs interzone decision (the core trade)

| Surface | If Adiabatic — physical assumption + when valid | If interzone — what it captures | DOE prototype choice | Recommended |
|---|---|---|---|---|
| Inter-floor slab | | | | |
| Core↔perimeter wall | | | | |
| Party wall | | | | |

### Table 3 — Inter-zone AIR exchange (not just conduction)

| Mechanism | Model it? | EnergyPlus object | When it matters | Source |
|---|---|---|---|---|
| Open-plan air mixing core↔perimeter | | `ZoneMixing` / `ZoneCrossMixing` | | |
| Stairwell / atrium stack between floors | | `AirflowNetwork` | | |
| Recommendation for UBEM scale (likely ignore — confirm) | | | | |

### Table 4 — Robustness to real geometry

| Issue | Note | Mitigation | Source |
|---|---|---|---|
| Matched vs unmatched interzone surfaces (vertex counts) | OpenUBEM has hit inter-floor vertex-mismatch fatals | (adiabatic avoids matching?) | |
| `intersect_match` behaviour on stacked real footprints | | | |
| When to prefer adiabatic purely for numerical robustness at scale | | | |

---

## Part C — Synthesis (rule block)

Give a **single boundary-condition rule block** OpenUBEM can code: the boundary condition for each
internal surface type in each mode, the adiabatic-vs-interzone decision with rationale, and the
inter-zone-air recommendation. Note explicitly where choosing **adiabatic for robustness/cost** is a
defensible UBEM convention vs where interzone transfer materially changes results.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C rule block.
3. Cite the EnergyPlus boundary-condition docs, prototype conventions, and any accuracy source.
4. **"Confidence and caveats":** the one surface whose treatment matters most.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **One explicit boundary condition per internal surface type per mode.**
- **Resolve adiabatic-vs-interzone** for inter-floor slabs and core↔perimeter walls.
- **Give a clear inter-zone-air recommendation** (model or ignore at UBEM scale).
- **Address numerical robustness** (vertex matching) given OpenUBEM's real footprints.
- **No fabricated precision;** flag GAPs with a defensible default.
- **Stay on topic.** If it is not a surface boundary condition or coupling, cut it.

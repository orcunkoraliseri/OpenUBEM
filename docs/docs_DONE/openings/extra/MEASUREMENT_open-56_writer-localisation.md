# MEASUREMENT — OPEN-56: localise the writer

> T02 of `implemenation/previous/PLAN_twenty-items-2026-08-19.md`. No fix made. Read-only investigation of
> code already installed in `.venv` plus run-4 `.err` artifacts.

## Premise check — the plan's premise is FALSE at HEAD, and it is worth reporting why

T02's **What** states OPEN-56's evidence mark is *"mechanism measured; writer not yet localised"*.
That is the tag in the register's top summary table (`INVESTIGATION_open-items-register.md:748`).
But the same register's own `### OPEN-56` §-section, further down the same file
(`:7316-7375`, "Amended 2026-08-18 (night) (W01–W05...)"), **already localises the writer**:
*"W05 — the writer is localised. Not our code. No `openubem/` module sets floor or ceiling vertex
order; the order comes from `geomeppy/geom/polygons.py:573-611`"* (`:7354-7357`). The top-line tag
was never updated after W05 was appended — it is a stale summary, not a live finding. **Per hard
rule 1, this is reported rather than silently worked around.**

T02 is still useful despite the stale tag: rule 11 requires re-deriving rather than quoting, and
the re-derivation below finds W05's own conclusion **incomplete** — its practical implication ("not
our code," read as "input orientation doesn't matter") does not hold up. The corrected localisation
below sharpens W05, it does not just restate it.

## What was re-derived

### 1. W05's citation is accurate but its conclusion needs one more step

`geomeppy/geom/polygons.py:573-590` (`normalize_coords`) calls `set_entry_direction`
(`:592-611`), which is meant to invert a surface's vertex order if it doesn't match the IDF's
`GlobalGeometryRules` entry direction (our IDFs: `Counterclockwise`). **Empirically, for
`entry_direction="counterclockwise"`, this check never fires — it is a no-op**, verified directly
against the installed package (`geomeppy==0.12.2`, `.venv/Lib/site-packages/geomeppy`):

```
>>> cw_floor = Polygon3D([(0,0,0),(0,1,0),(1,1,0),(1,0,0)])
>>> out = cw_floor.outside_point('counterclockwise')
>>> cw_floor.is_clockwise(out)
False
>>> set_entry_direction(cw_floor, out) == cw_floor vertices   # unchanged
True

>>> ccw_floor = Polygon3D([(0,0,0),(1,0,0),(1,1,0),(0,1,0)])
>>> out = ccw_floor.outside_point('counterclockwise')
>>> ccw_floor.is_clockwise(out)
False                                                          # still False
>>> set_entry_direction(ccw_floor, out) == ccw_floor vertices  # unchanged again
True

>>> out2 = ccw_floor.outside_point('clockwise')                # opposite request
>>> ccw_floor.is_clockwise(out2)
True                                                            # DOES fire
```

**Cause, cited:** `outside_point()` (`geomeppy/geom/polygons.py:349-364`) constructs its test point
as `self.vertices[0] + self.normal_vector` for the counterclockwise branch (`:361`) — i.e. it
derives the "outside" reference point from the surface's **own, not-yet-corrected** normal vector
(`normal_vector`, `:207-272` in the `Polygon3D`/`Polygon` classes, Newell's method over the
surface's current vertex order). `is_clockwise(viewpoint)` (`:311-323`) then computes
`sign = dot(vertices[0] - viewpoint, normal_vector)`. Substituting the CCW-branch viewpoint:
`vertices[0] - (vertices[0] + normal_vector) = -normal_vector`, so
`sign = dot(-normal_vector, normal_vector) = -|normal_vector|² < 0` for **every** polygon,
**regardless of its actual winding** — `is_clockwise()` returns `False` unconditionally on the CCW
branch, so `invert_orientation()` is never reached. This is a **library defect in `geomeppy`
0.12.2's counterclockwise branch**, not a floor/ceiling-specific rule and not anything `openubem/`
controls. (The clockwise-request branch, tested above, correctly detects and flips — the bug is
asymmetric.)

### 2. Because the "corrector" is a no-op, the winding written to the IDF is whatever `geomeppy.Block` computes directly from the input footprint — and THAT does trace back through openubem

`idf.add_block()` (`geomeppy/idf.py:247`) constructs a `Block` (`geomeppy/builder.py:28`) from the
raw `coordinates` argument. `Block.footprint` (`builder.py:100-110`) wraps those coordinates,
unmodified, into a `Polygon3D`. From it:

- `Block.floors` (`builder.py:173-184`): `self.footprint.invert_orientation() + Vector3D(0,0,fh)`
  — **deliberately inverted** from the input footprint.
- `Block.ceilings` (`builder.py:186-198`) and `Block.roofs` (`builder.py:200-213`): `self.footprint
  + Vector3D(0,0,ch)` — **not inverted**, kept exactly as given.

So `Block`'s design assumes callers hand it a footprint in one specific convention (floors get
inverted from it, ceilings/roofs don't) and produces the opposite pairing if that assumption is
wrong. **The symptom in every `eplusout.err` is both warnings together** — `Floor is upside down!`
**and** `Roof/Ceiling is upside down!` on the same building — which is exactly what happens if the
footprint fed to `add_block` has the orientation opposite to what `Block` assumes: both derived
surfaces come out backward together, not just one.

### 3. The footprint fed to `add_block`, for the adopted `auto` mode, is never oriented at all

`openubem/geometry/zoning.py:52` (`build_zones`): `coords = list(footprint_poly.exterior.coords)[:-1]`
— passed straight through to the zone dict's `coords_m`, and from there into `idf.add_block(...)`
in `openubem/idf/surfaces.py` unmodified. `footprint_poly` is `poly_local`, produced by
`translate_to_origin` (`openubem/geometry/footprint.py:52-55`, an affine translate — does not
touch ring orientation) from a polygon that passed through `simplify_footprint`
(`openubem/geometry/footprint.py:24-40`, `shapely.simplify`/`convex_hull`/`minimum_rotated_rectangle`
— none reorder a ring's winding). **`openubem/idf/builder.py:464-465` does apply an explicit
`shapely.geometry.polygon.orient(poly_local, sign=1.0)`, but only when `self.resolution_mode !=
"auto"`.** The adopted fleet baseline uses `auto` (F1, OPEN-01). So for every building in the
adopted mode, `poly_local`'s winding is whatever the source footprint geometry already has —
uncorrected.

**Measured directly**, 20 random buildings from `nyc_urban`'s `01_buildings.gpkg` plus the specific
building used for the control below: **0 / 20 have a CCW exterior ring** (`shapely`'s
`.exterior.is_ccw`, standard math x-y convention) — **100 % are clockwise**, matching the 100 %
defect rate exactly. `Block.ceilings`/`Block.roofs` therefore receive a **clockwise** footprint
unmodified and `Block.floors` receives its **inverted (counterclockwise)** — the opposite pairing
from what geomeppy's own convention needs, on every building, and `normalize_coords` cannot correct
either one (§1).

### Answering the task's three questions directly

1. **Which function writes those vertices, at which line, in which order?**
   `geomeppy.builder.Block.floors` (`builder.py:173-184`, inverted) and
   `Block.ceilings`/`Block.roofs` (`builder.py:186-213`, not inverted) — both **third-party**,
   inside the pinned `geomeppy==0.12.2` dependency, not `openubem/`.
2. **Is the winding inverted at emission or inherited from the footprint polygon upstream?**
   **Both, and they compound.** It is inherited (the raw ring orientation of the source footprint,
   confirmed 0/20 CCW, is passed through unmodified for `auto` mode — `zoning.py:52`,
   `footprint.py:52-55`, `builder.py:464-465`), and it is also a property of emission (`Block`'s
   fixed invert/no-invert pairing assumes one specific input convention and gets the other). Fixing
   either end independently would work; fixing neither is why the defect is universal.
3. **`shapely.geometry.polygon.orient` — is it in the path?** Yes, imported and used at
   `openubem/idf/builder.py:15,465`, but gated off (`:464`) for the one mode (`auto`) that is
   adopted for the published fleet EUI.

## How-to-test: prediction on a second, independent building — and a full fleet re-check

**Prediction:** every building in every run-4 cell carries both warnings, because the mechanism
(source-footprint winding, uncorrected for `auto` mode, plus geomeppy's broken CCW corrector) has
no building-specific branch.

- Second building, different cell from any previously checked (`nyc_urban / relation_17949119`,
  never cited in OPEN-56's prior record): `eplusout.err` carries `GetVertices: Floor is upside
  down!` (line 17) and `GetVertices: Roof/Ceiling is upside down!` (line 19) — **prediction
  confirmed.**
- Full re-check, all twelve run-4 cells, `grep -l "Floor is upside down" */sim_out/*/eplusout.err`:
  **8,160 / 8,160 — 100.00 %**, one match per building directory, no exceptions, matching the
  register's prior run-2/run-3 counts exactly on run 4 as well.

| cell | buildings | with warning |
|---|---:|---:|
| austin_centre | 413 | 413 |
| austin_rural | 245 | 245 |
| austin_suburban | 437 | 437 |
| austin_urban | 425 | 425 |
| la_centre | 226 | 226 |
| la_rural | 149 | 149 |
| la_suburban | 1,343 | 1,343 |
| la_urban | 618 | 618 |
| nyc_centre | 738 | 738 |
| nyc_rural | 198 | 198 |
| nyc_suburban | 1,589 | 1,589 |
| nyc_urban | 1,779 | 1,779 |
| **total** | **8,160** | **8,160** |

A mechanism that explains one building and predicts nothing would fail this control; this one
predicted correctly on a fresh building and reproduces exactly on the full fleet.

## What this changes for the remedy ruling

The register frames the choice as *"write `Zone.Volume` explicitly, or fix the winding upstream."*
This measurement adds a fact relevant to costing the second option: **"fix the winding upstream"
cannot be done by patching `openubem/` alone in the way OPEN-56's own excluded detector
(`openubem/idf/surfaces.py:223` `_coreperim_has_inverted_winding`, excluded at `:671-681`) implies —
the exclusion comment's reasoning ("EnergyPlus convention always uses negative signed-area for
floor surfaces") is about 2-D signed area, a different question from the 3-D winding defect here,
and remains not adjudicated by this task.** Two remedy shapes are now visible, neither applied
here: (a) call `orient(poly_local, sign=-1.0)` (or the correct sign — not verified here) for `auto`
mode too, matching what already happens for non-`auto` modes at `builder.py:465`; or (b) write
`Zone.Volume` explicitly, bypassing the winding question altogether, as the register already names.
Choosing between them, and confirming the correct `sign` for (a), is a remedy decision and is
explicitly out of scope for this task.

## Output

This document. No `.csv` was produced — this task returned code citations and a pass/fail control,
not a table.

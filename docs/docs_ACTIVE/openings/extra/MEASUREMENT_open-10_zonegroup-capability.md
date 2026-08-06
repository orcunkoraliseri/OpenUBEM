# MEASUREMENT — OPEN-10: Can a `ZoneGroup` list multiplier express exact storey matching at every `n_real`?

> **Task:** N11, `PLAN_no-compute-queue-2.md` §6. **Type:** measurement only — no IDF built, no
> simulation run, no `eppy` write. **HEAD read at:** `bca92d0a6cdc33923bea8424f1b86ab0f94d82d9`
> (2026-08-05, per `git rev-parse HEAD`).

## Verdict

**Yes** — for the two archetypes this item is actually about (`ApartmentMidRise`, `ApartmentHighRise`),
writing the `ZoneGroup`'s own `Zone List Multiplier` field directly (instead of layering a residual
`Zone.Multiplier` on top of its pre-existing baked-in value, which is what the shipped code does) would
express **every** `n_real ≥ 3` exactly, not only `{10, 18, 26, …}` (HighRise) / even `n_real ≥ 4`
(MidRise) — because the IDD imposes no divisibility constraint on that field, only a positive-integer
minimum, and the current gap is created entirely by the code's choice to *compound* rather than
*overwrite*. This does **not** extend to the 7 other `fallback_not_expressible` archetypes (ambiguous or
absent middle band), nor to `n_real < n_proto` (shortening) — those are structural limitations unrelated
to which multiplier field is edited.

---

## 1. The `ZoneGroup` IDD block, verbatim

**File:** `C:\EnergyPlusV23-1-0\Energy+.idd` (confirmed present on this machine; resolved by
`openubem/config.py:16` — `ENERGYPLUS_PATH` default `C:\EnergyPlusV23-1-0`, `.exists()` check passed).

**Lines 10002–10018:**

```
ZoneGroup,
       \memo Adds a multiplier to a ZoneList. This can be used to reduce the amount of input
       \memo necessary for simulating repetitive structures, such as the identical floors of a
       \memo multi-story building.
       \min-fields 2
  A1 , \field Name
       \note Name of the Zone Group
       \required-field
       \type alpha
  A2,  \field Zone List Name
       \required-field
       \type object-list
       \object-list ZoneListNames
  N1;  \field Zone List Multiplier
       \type integer
       \default 1
       \minimum 1
```

Field `N1` ("Zone List Multiplier") is **`type integer`, `default 1`, `minimum 1` — no `\maximum`, no
divisibility or step note of any kind.** It applies one integer multiplier to the whole named
`ZoneList` (defined at `ZoneList,` lines 9643–9672: an extensible list of `Zone` name references, "may
be used elsewhere in the input to apply a parameter to all zones in the list").

For comparison, the field the shipped mechanism actually edits — `Zone`'s own `Multiplier` field, IDD
lines 9576–9579:

```
  N6 , \field Multiplier
       \type integer
       \minimum 1
       \default 1
```

**Identical type and constraint** (`integer`, `minimum 1`, `default 1`, no maximum) to `ZoneGroup`'s
`N1`. The schema draws no distinction in expressive power between the two fields — both accept any
positive integer. Whatever restricts the set of reachable `n_real` values today is not written into
either field's definition.

## 2. The delivered mechanism, and what it actually edits

**File:** `openubem/geometry/layout_assigner.py` (HEAD at commit `69373f9`, 2026-07-27 — unchanged
since; `git log -1` confirms).

- `compute_band_map()` (`layout_assigner.py:383-536`) clusters a prototype's `Zone` objects into
  Z-elevation bands and, per its R01 amendment (`:391-426`), **reads** `ZoneList`/`ZoneGroup` membership
  to compute each band's `storeys_in_band` (the ZoneGroup's own baked-in list multiplier, defaulting to 1
  when no `ZoneGroup` touches that band — `:456-481`). It never writes anything.
- `match_storeys(idf, n_real, band_map)` (`:539-653`) is the only code that **mutates** the IDF, and it
  does so exclusively by setting `z_obj.Multiplier` (`Zone`'s own field, `:649`) on the zones of one
  target band — **never `ZoneGroup`'s `Zone_List_Multiplier`.** Verified: the string
  `Zone_List_Multiplier` appears in this file only as a *read* (`:459`, inside `compute_band_map`), never
  as an assignment target.
- For the taller-than-prototype case with exactly one middle band (`n_proto == 3`, the G/M/T shape),
  the code solves for a **residual** (`:616-634`):

  ```
  list_multiplier = target_band["storeys_in_band"]       # the ZoneGroup's baked-in value (1, 2, or 8)
  non_middle_storeys = sum(b["storeys_in_band"] for b in bands if b is not target_band)  # bottom+top
  raw = n_real - non_middle_storeys
  # written only if raw >= list_multiplier AND raw % list_multiplier == 0:
  residual_multiplier = raw / list_multiplier
  z_obj.Multiplier = residual_multiplier   # compounds with the ZoneGroup's existing list_multiplier
  ```

  This is the source of the restricted reachable set: EnergyPlus **compounds** the two multipliers
  (`Zone.Multiplier` × `ZoneGroup`'s list multiplier), and the code preserves the pre-existing
  `ZoneGroup` value rather than overwriting it, so `n_real` must land on a residue of `list_multiplier`.

### Which archetypes actually carry a `ZoneGroup` (verified by direct file read, not the docstring's claim)

Per the docstring (`layout_assigner.py:395-399`): "Exactly 2 of the pinned library's 25 files carry a
real `ZoneGroup`." Independently confirmed by grep on `BASELINE_IDF_DIR`
(`C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231`, resolved by
`openubem/config.py:49-54`, HEAD at commit `3a925f9`):

| Prototype file | `ZoneList`/`ZoneGroup` lines | List Multiplier | Band shape |
|---|---|---|---|
| `ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf` | 2524–2541 (`ZoneList,` 2524; `ZoneGroup,` 2538, `Zone List Multiplier` = `8`) | **8** | G (1) / M (ZoneGroup×8) / T (1) — 3 bands, zone-name prefixes `G `/`M `/`T ` confirmed by grep |
| `ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` | 2066–2081 (`ZONELIST,` 2066; `ZONEGROUP,` 2078, `Zone List Multiplier` = `2`) | **2** | Same G/M/T 3-band shape, confirmed by grep |

No other file in the 25-file library matches `ZoneGroup`/`ZONEGROUP` (grep on the whole directory
returned only these two hits' object blocks).

## 3. `n_real` expressibility table

`non_middle_storeys = 2` for both archetypes (bottom band + top band, each `storeys_in_band = 1`, no
`ZoneGroup` on either). `n_proto = 3` (identity case at `n_real = 3`; `n_real < 3` is `fallback_shorter`
— band deletion, out of scope for either mechanism, unaffected by which multiplier field is used).

| `n_real` | Shipped mechanism — `ApartmentMidRise` (L=2) | Shipped mechanism — `ApartmentHighRise` (L=8) | Proposed mechanism — direct `ZoneGroup` overwrite (either archetype) |
|---:|---|---|---|
| 1 | not expressible (`fallback_shorter`) | not expressible (`fallback_shorter`) | not expressible (`fallback_shorter` — unrelated to multiplier field) |
| 2 | not expressible (`fallback_shorter`) | not expressible (`fallback_shorter`) | not expressible (`fallback_shorter`) |
| 3 | `identity` (n_real==n_proto, no multiplier involved) | `identity` | `identity` |
| 4 | **applied**, residual=1 → no field write ((4−2)/2=1) | not expressible ((4−2)/8=0.25) | **applied**, write `N1=2` exactly |
| 5 | not expressible ((5−2)/2=1.5) | not expressible ((5−2)/8=0.375) | **applied**, write `N1=3` exactly |
| 7 | not expressible ((7−2)/2=2.5) | not expressible ((7−2)/8=0.625) | **applied**, write `N1=5` exactly |
| 10 | **applied**, multiplier=4 ((10−2)/2=4) | **applied**, residual=1 → no field write ((10−2)/8=1) | **applied**, write `N1=8` exactly |
| 18 | **applied**, multiplier=8 | **applied**, multiplier=2 | **applied**, write `N1=16` exactly |
| 26 | **applied**, multiplier=12 | **applied**, multiplier=3 | **applied**, write `N1=24` exactly |
| 51 | not expressible ((51−2)/2=24.5) | not expressible ((51−2)/8=6.125) | **applied**, write `N1=49` exactly |

**Reading:** the shipped mechanism reaches only `n_real ∈ {4,6,8,10,…}` for MidRise and
`n_real ∈ {10,18,26,…}` for HighRise (both confirmed against the register's stated ranges). The proposed
mechanism — overwrite `ZoneGroup`'s own `N1` field to `n_real − 2` directly, discarding rather than
compounding the baked-in 2 or 8 — reaches **every integer `n_real ≥ 3`**, for both archetypes
identically, because it is no longer solving a compounded-multiplier divisibility equation.

**Scope limit, stated plainly:** this gain applies only to the population that already has a
`ZoneGroup` object to overwrite — the 2 apartment archetypes. It does **not** help the 7 archetypes
currently `fallback_not_expressible` for a different reason (`Hospital`, `LargeOffice`, `TallBuilding`,
`SuperTallBuilding`, `College`, `LargeHotel`, `Laboratory` — `layout_assigner.py:557-563`: either no
middle band or more than one distinct middle band, an ambiguity about *which* band to edit, not a
granularity limit on the field's value). Writing a `ZoneGroup` multiplier there would first require
*constructing* a new `ZoneList`+`ZoneGroup` from scratch and resolving which band it targets — a materially
larger change than "editing the field," and a design decision this measurement does not make.

## 4. Where "90 buildings" comes from, and whether it is re-derivable

**Source, quoted verbatim:** `docs/docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/PLAN_storey-matching_REMAINder.md:1302-1315`
(HEAD at commit `bca92d0`, 2026-08-05):

> "**6. R10's reach change (CP-D condition (b)).** **90 buildings changed status fleet-wide** (66
> `MidriseApartment` + 24 `HighriseApartment`), **all `applied → fallback_not_expressible`**... Full
> crosstab (7,442 buildings evaluated = 8,160 − 718 with no `ARCHETYPE_IDF_MAP` entry...):
> ```
> new_status                applied  fallback_not_expressible  fallback_shorter  identity
> old_status
> applied                       503                        90                 0         0
> ...
> ```"

So: **90 = 66 + 24**, the count of real fleet buildings whose status *flipped* from `applied` to
`fallback_not_expressible` specifically **because** R10 (E-LA-36, the residual-multiplier fix) started
enforcing the divisibility constraint that a simpler absolute-write formula did not. This is exactly the
population that the table in §3 shows would move back to `applied` under a direct-`ZoneGroup`-overwrite
mechanism (every `MidriseApartment`/`HighriseApartment` building whose `n_real` is odd, or not on the
HighRise 8-residue ladder, respectively). The register's "**90 buildings + future**" reach figure is
therefore this crosstab cell — "+ future" is the register's own forward-looking annotation for buildings
added to the fleet later, not a citable count in any document.

**Re-derivability: NOT re-derived in this task, and I did not attempt to.** Reproducing the 90 requires
executing `match_storeys()`/`compute_band_map()` against every one of the 7,442 real
`(archetype_id, num_floors)` fleet pairs (a full fleet-wide code pass, per the source document's own
method note at `:1291-1300`, "executed against every one of the... fleet-wide `applied`-status
buildings' real pair"). §2 of the governing plan forbids exactly this class of work in N11 ("Build
nothing... Reading the IDD and the source is the whole task") and the plan's global rule 3 forbids "any
CPU-bound work" more broadly ("No fleet pass. No cell pass... If a task looks like it needs a pipeline
run, you have misread it: STOP and say so"). I am treating a fleet-wide pass over 7,442 buildings as
exactly that, even though it involves no EnergyPlus and would write no file. **The number is documented,
with a path:line, but is not currently re-derivable within this task's no-compute constraint.**

**Smallest experiment that would settle it:** re-run the same non-mutating audit — load
`04_simulation_manifest.parquet` (or the Stage-2 classifier output) for all twelve cells, join to
`ARCHETYPE_IDF_MAP`, and call the current `compute_band_map()`/`match_storeys()` pair once per building
for the two apartment archetypes only (a few thousand pure-Python calls, no EnergyPlus, no cluster, no
file writes) — and recompute the crosstab. This is CPU-light enough to run on a local machine in well
under a minute; it is excluded here only because this plan's rules classify any fleet-scale pipeline
code execution as out of scope for a measurement task, not because it is expensive.

## 5. Reopening flag

R04 is closed at option (a) (per project memory and register §8 "What is closed and must not be
reopened by mistake"). OPEN-10 is recorded, correctly, as a **deliberate reopening** of one piece of
that closure — not a continuation, and not something this measurement argues for or against. This report
states what the schema and code permit; it does not recommend building the alternative mechanism.

---

## How-to-test results

**(a) `ZoneGroup` IDD block quoted verbatim with file path and line numbers — PASS.** §1 above, `C:\EnergyPlusV23-1-0\Energy+.idd:10002-10018`.

**(b) `n_real` expressibility table complete for all ten listed values, two mechanisms side by side — PASS.** §3 above; three columns given (both shipped-mechanism archetypes distinguished, since they behave differently) rather than two, because the shipped mechanism's reach differs between MidRise (L=2) and HighRise (L=8) — collapsing them into one "shipped" column would have hidden that they hit different residue sets.

**(c) Verdict is one of the three allowed words, one sentence, at the top — PASS.** "Yes" — see Verdict section, first line.

# What we chose vs. what we inherited

**Date:** 2026-09-17
**Source plan:** `docs/docs_ACTIVE/TechTransfer/implementation/PLAN_techtransfer-block1-2026-09-17.md` (D02)
**Purpose:** for each model setting below, say plainly whether OpenUBEM decided it on purpose
(**chosen**), whether it follows from building physics with no choice to make (**physics**), or
whether it is simply whatever the tool or the source data does by default, with nobody having
decided it (**inherited**). Every row below carries a file:line or a document citation; no row is
guessed or listed without one.

---

## 1. Ground temperature — inherited

**Value.** Every EnergyPlus run in OpenUBEM uses the program's default ground temperature, 18 °C
for every month, because no `Site:GroundTemperature:BuildingSurface` object is ever written.

**Citation.** No `Site:GroundTemperature*` object is emitted anywhere in `openubem/` —
`grep -rin "GroundTemperature" openubem/ --include=*.py` returns zero hits (plan §5, fact 1).

**Tag.** Inherited: this is EnergyPlus's silent default, not a value anyone typed in.

**What it would take to move it out of "inherited."** Write `Site:GroundTemperature:BuildingSurface`
explicitly at 18 °C so the value is visible in every IDF instead of implicit — this does not change
any simulated result, it only makes the existing default readable (plan §4, decision D1).

**Ground temperature is now chosen, not inherited.** OpenUBEM writes
`Site:GroundTemperature:BuildingSurface` explicitly, 18.0 degC for all twelve months, once per IDF
(`openubem/idf/ground.py`, called from `BuildingIDF.__init__`, `openubem/idf/builder.py:288`). Before
this change no such object was ever written anywhere in the repo, so EnergyPlus silently applied its
own 18 degC default; the change makes that number visible and testable, it does not alter it.

**Proof nothing moved.** 19 buildings, 456 building x end-use pairs, compared before and after: max
absolute difference 0.0 kWh, max relative difference 0.0 on every single pair (plan D2/A03/D12).

**What was rejected.** An "undisturbed soil temperature" replacement was considered and turned down:
under a heated building the soil next to the slab sits near indoor temperature, so an undisturbed
profile would make the model worse, not better (D1). `Site:GroundTemperature:FCfactorMethod` was also
not added in this block, since EnergyPlus would derive that series from the weather file and writing
it explicitly would move results; it is census-only here, and adopting it is a separate, still-open
decision (D3).

**Census (A01, mode=layout_assign, 20 buildings sampled, 10 archetypes, 10 per mode).** Object counts:
`Construction:FfactorGroundFloor`=56, `Construction:CfactorUndergroundWall`=0,
`Site:GroundTemperature:BuildingSurface`=0 (pre-change), `Site:GroundTemperature:FCfactorMethod`=9,
`Site:GroundTemperature:Shallow`=3, `Site:GroundTemperature:Deep`=3, `Foundation:Kiva`=0, plus 75
`GroundFCfactorMethod` boundary-condition surfaces across 10 buildings.

**Tag: chosen, with an inherited neighbor.** The borrowed prototype library already carries its own
ground model, and the new chosen object does not touch or harmonize it — two ground models now coexist
in the `layout_assign` path. Reconciling them is pending decision D3, a user decision, not settled here.

---

## 2. STD2022 internal loads (OPEN-03) — inherited, open, unresolved

**What the item is.** `layout_assign` and `auto` disagree on internal loads, and the disagreement is
about which **source** of load densities each mode reads, not about building code **vintage** — both
modes are vintage-blind. Quoting the current register wording directly rather than restating it from
memory:

> "The gap is a load-**source** disagreement, not a load-**vintage** one: `auto` reads one fixed pair
> per archetype from `doe_prototype_loads.json` (no vintage key), `layout_assign` uses the DOE
> prototype baseline IDF's own densities for any archetype with a mapped `STD2022` baseline. **Both
> modes are equally vintage-blind.**"

**Citation.** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md:121` (OPEN-03 row).
The item is confirmed still open and live as of the same document's line 111 ("OPEN-03 ... stay live").

**Tag.** Inherited: which source of load densities a building gets depends on which resolution mode
built it, not on a documented choice about which source is more correct. This is recorded here as an
open, unresolved item — this document does not attempt to resolve it (per plan instruction).

**What it would take to move it out of "inherited."** A ruling on which load-density source
(`doe_prototype_loads.json` vs. the DOE prototype baseline IDF's own `STD2022` densities) is preferred,
and why — not attempted in this document.

---

## 3. Nominal (footprint) vs. simulated floor area — chosen

**What the two quantities are.** A building's footprint area times its number of floors ("nominal" or
footprint-derived area) is not the same quantity as the floor area EnergyPlus actually simulates
(summed per-zone floor area, multiplier-aware, read back from the run's own `.eio` file).

**Which one the model uses.** The model prefers the simulated area and only falls back to the nominal
one when the simulated value cannot be read: `resolve_simulated_floor_area()` returns the
multiplier-aware area parsed from `eplusout.eio` when it parses cleanly and is positive
(`provenance="eio_simulated"`), and only falls back to `footprint_area * num_floors`
(`provenance="footprint_fallback"`) when the `.eio` is missing, unparseable, or gives a non-positive
area — `openubem/results/parser.py:496-525`.

**Citation.** `openubem/results/parser.py:496-525` (`resolve_simulated_floor_area`, docstring: "Return
(floor_area_m2, provenance) per ruling 6"). The ruling itself: "RULED 2026-08-13 (ruling 6) — THE
REMEDY IS: DIVIDE BY THE SIMULATED AREA" —
`docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md:1080`.

**Tag.** Chosen: this is a user ruling (OPEN-01, ruling 6), not a default anyone fell into. The choice
was to divide energy by the *simulated* area whenever it is available, and fall back to the nominal
footprint-based area only when it is not.

**What it would take to move it further.** Nothing owed — this is already a documented, cited
decision. The only open edge is that every row still carries a `floor_area_provenance` flag so a
reader can tell, per building, which of the two areas was actually used
(`openubem/results/parser.py:922`).

---

## What is not harmonized

- **Two different ground boundary-condition models coexist across resolution modes.** The OSM-built
  path writes ground floors as plain `"ground"` (`openubem/idf/surfaces.py:527`, comment at
  `openubem/idf/surfaces.py:990`), while the `layout_assign` path skips surfaces whose boundary
  condition is `GroundFCfactorMethod` and leaves them on the prototype's native construction
  (`openubem/geometry/envelope_patcher.py`, the `obc == "groundfcfactormethod": continue` branch).
  Nobody has reconciled these into one ground model; adopting `Site:GroundTemperature:FCfactorMethod`
  fleet-wide is a separate, un-taken decision (plan §4, decision D3).
- **STD2022 internal loads (row 2 above) are inherited and unresolved** — which load-density source a
  building gets depends on its resolution mode, not on a ruling about which source is correct.

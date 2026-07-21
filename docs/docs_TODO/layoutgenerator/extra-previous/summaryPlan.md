# LayoutGenerator — plan summary

## What the arc is

Build `layoutGenerator.py` so non-rectangular footprints (L/U/T/O-courtyard/cross/rotated) get room-level interior zoning (corridor + packed room modules) instead of silently degrading to one-zone-per-floor. Every dimension is DOE/ASHRAE-cited (zero fitted params). Opt-in `zone` mode only — `auto`/fleet runs are untouched.

## The plan, phase by phase

**Phase 0 — Scaffolding + classifier ✅ done**
- T01 — module skeleton + pinned `MODULE_SPECS` (corridor/depth/bay dims per archetype).
- T02 — `classify_footprint()` → compact/slab/L/U/T/cross/O/ribbon/irregular via shape-metric ladder.

**Phase 1 — Corridor-packing engine (MidriseApartment) ✅ done → CP-1 MET**
- T03 — double-loaded bar packer (`_pack_bar`): corridor spine + N/S/E/W unit rows.
- T04 — wing decomposition for L/U/T/cross (orthogonal cuts from reflex corners).
- T05 — donut splitter for O/courtyard (tic-tac-toe cut → hole-free wings; kills the courtyard E+ Fatal).
- T06 — dispatch wiring: `zone` mode → new `room_layout` strategy; `auto` unchanged.

**Phase 2 — Loads + conservation ✅ done**
- T07 — per-space-type loads table (Apartment vs Corridor: corridor EPD=0, occ=0).
- T08 — space-type-weighted normalization so zone-mode building totals equal floor/building mode exactly.

**Phase 3 — Interior surfaces + synthetic sim ✅ done → CP-2 MET**
- T09 — interior boundary conditions (corridor↔unit = Surface, unit↔unit = Adiabatic, courtyard-inner = Outdoors).
- T10 / T10a — synthetic E+ 0-Fatal smoke on all shapes + a live-footprint reroute safety net.

**Phase 4 — Validation ✅ done → CP-3 MET**
- T11 — reproduce the DOE MidriseApartment standard (area/loads/EUI within thresholds).
- T12 / T12-FIX — LIVE_SMOKE on real OSM apartments. First pass failed (real footprints aren't exactly orthogonal → sliver zones → Fatals); fixed by dropping degenerate cells + honest degrade. Now 0 Fatal, 100% gen-success.

**Phase 5 — Expansion + sim + comparison 🟡 partly done → CP-4 = user sign-off, NOT reached**
- T13a — SmallHotel + LargeHotel via the same engine ✅ (but production degrades hotels on complex shapes to per-floor; room-level only on simple/bar).
- T13b — Offices (core/perimeter family) — ❌ deferred, no engine exists.
- T13c — Schools (classroom-wing) — ❌ deferred, no engine exists.
- T14 / T14-HOTELFIX — cluster pilot (zone vs floor vs building EUI) ✅ fired & harvested; hotels recovered via a classifier fix.
- T15 — DOE-vs-generated comparison report + plots — ⬜ not started.

**Visuals**
- T16 / T16b — the MidriseApartment layout grid + continuous corridor spine ✅.
- T17 / T17b / T17c — per-archetype grids (SmallHotel, LargeHotel) with individual rooms drawn ✅.
- T18 — hotel room-level preview on all shapes (force_complex, viz-only) ✅.

## The two open items that block "design all DOE buildings"

1. T18-DIAG (just closed this session as the clean-zoning fix) — the corridor-width slivers you flagged. Fixed — Approach A corridor-first. That's the state I confirmed in the figures.
2. T13b / T13c — offices and schools have no geometry engine at all. They always degrade. To show their DOE layout variations, we have to design and build those two packers from scratch. This is the real content of "implement all variations for all DOE buildings."

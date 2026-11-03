# G2 — Lodging corridor

> **Layout family:** units+corridor (LargeHotel adds a ground podium) · **Template applies:** ✅ **yes** ·
> **Locked step:** S4 (pending) — apply the corridor law + resolve the LargeHotel podium/tower split.
> Backing design: `../Design_layoutgenerator.md` §5.1 (Family A), groups §3.1 (G2), corridor law §4.

## Members (2 IDFs)

| IDF filename | OpenUBEM archetype | Family | DOE zones (as-modeled) | Status |
|---|---|---|---|---|
| `ASHRAE901_HotelSmall_STD2022_Buffalo_NECB17_Z7A_v221.idf` | SmallHotel | units+corridor | **67** total · 10/guest-flr (8 GR + corr + BOH) | ⚠️ preview only |
| `ASHRAE901_HotelLarge_STD2022_Buffalo_NECB17_Z7A_v221.idf` | LargeHotel | units+corridor (+podium) | **22** (representative-floor) · 7/guest-flr (E/W GR + corr + mech) | ⚠️ preview only |

**Why grouped together:** both are guest-room corridor buildings — same double-loaded spine as apartments
but with a **smaller room module** (guest room, not dwelling unit). LargeHotel is confirmed (§10) as
units+corridor with a **podium ground floor + banquet top**, validating the podium/tower split. They sit in
their own group (not with apartments) because their module dims and the podium differ.

## Kit-of-parts (zero-fitted)

| Archetype | corridor width | room depth | bay pitch | room area | circ % | source |
|---|---|---|---|---|---|---|
| SmallHotel | 1.83 m (6 ft) | 7.32 m (24 ft) | 3.66 m (12 ft) | 26.79 m² | ~11% | Deru 2011 §3.1.13 + L06 |
| LargeHotel | 2.44 m (8 ft) | 7.32 m | 4.11 m (13.5 ft) | 30.09 m² | ~20% (incl. podium) | PNNL 2020 Large Hotel + L08 |

> ⚠️ **OPEN — dimension conflict to ratify before hotels productionize (Design §5.1, open decision #2).**
> L07 Table 2 lists both hotels as a 4.27 m × 7.62 m (14×25 ft) module with an 8 ft corridor; the committed
> `MODULE_SPECS` uses the values above (1.83/7.32/3.66 and 2.44/7.32/4.11). Committed values ship; the
> conflict needs a one-line user confirmation.

## Recipe + shape behaviour

Same Approach A corridor-first recipe as G1, with the guest-room module. LargeHotel additionally splits a
**ground podium** (core+perimeter / open-plan) from the **guest-room tower** (units+corridor).

| Shape | behaviour |
|---|---|
| Compact / slab | double-loaded guest-room bar, short ends open to facade |
| L / U / T / cross / O | corridor law applies (one network, facade-reaching); **but see status** |
| Ribbon / irregular | single-loaded or degrade |

## Alternatives to render (A = DOE default)

- **A** double-loaded corridor — production default.
- **B** single-loaded corridor.
- **C** atrium / central (large hotel).

## Reference figure

`layoutgrid_LargeHotel.png` — SC-audited PASS, in this folder + `../outputs/`. Carries an **honest PREVIEW
footer** ("production degrades hotels on L/U/T/O/cross to per-floor pending E+ validation").

## Status caveat (correctness > coverage)

**DECISION (user 2026-07-04, revisable): LargeHotel = rectangular/square footprints only.** It is already
highly complex (like Hospital), so we keep the DOE structure and **do not attempt complex-shape layout
generation** for it; complex shapes degrade to per-floor. SmallHotel may still explore complex shapes at S4.

Hotels are otherwise **geometry preview only**. The small guest-room module fragments complex shapes into
fully-interior corridor cells that fail HVAC autosizing, so production currently **degrades hotels on
L/U/T/O/cross to per-floor**. Promoting SmallHotel to production room-level is the S4 design task.

**Hotel dimensions RESOLVED (user 2026-07-04):** use the committed `MODULE_SPECS` values above
(1.83/7.32/3.66 and 2.44/7.32/4.11) — the L07 4.27×7.62 alternative is dropped.

## Provenance

Design §3.1 (G2), §5.1 (Family A, hotel dims + conflict flag), §4 (corridor law), §10 (LargeHotel podium
confirmed, SmallHotel 67 / LargeHotel 22 zones).

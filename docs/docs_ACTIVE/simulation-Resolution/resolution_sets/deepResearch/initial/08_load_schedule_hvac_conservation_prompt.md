# Deep-Research Prompt 08 — LOAD / SCHEDULE / HVAC distribution & CONSERVATION across resolution

> SCOPE GUARD — READ FIRST. This is a **conservation-of-quantities** task. The deliverable is the
> rule set ensuring that when a building is split into N zones (1 → num_floors → ~5×num_floors), the
> **total internal loads, ventilation, and HVAC capacity stay invariant** — no double-counting, no
> loss — and that per-zone schedules and diversity are applied correctly. It is NOT about the numeric
> densities themselves (Prompt 04). If you are writing about anything other than **how a building-total
> quantity is partitioned across zones and conserved, and the source**, stop and return to the tables.
> See `00_README_resolution_prompt_set.md` for modes, roster, conventions.

---

## What this document is

A fill-in-the-blanks request on the partition arithmetic of resolution. OpenUBEM assigns loads,
schedules, ventilation, and per-zone HVAC by looping over zones (builder.py). When the zone count
changes with `resolution_mode`, the **building-total** lighting/equipment/occupancy/OA/HVAC must be
identical so that only the *spatial distribution* changes, not the total energy — otherwise modes are
not comparable and EUI shifts artefactually. Treat each cell as a question; fill with a sourced rule.

## Role

Building-energy-modelling research analyst. Trace every rule to: the **EnergyPlus I/O Reference**
(`People`, `Lights`, `ElectricEquipment` with `Watts/Area` vs `Watts/Zone` vs absolute;
`DesignSpecification:OutdoorAir` Sum vs Maximum; `Sizing:Zone`), the **DOE/PNNL prototype**
documentation (per-zone vs whole-building load specification + **occupancy diversity factors**), and
**ASHRAE 62.1-2019** (multiple-zone OA `Vot` calculation — why summing per-zone OA ≠ system OA). SI.

## Why this matters (so you scope correctly)

If loads are specified `Watts/Area`, total scales with zone floor area — splitting a floor into
core+perimeter preserves total automatically. But `Watts/Zone` (absolute per-zone) would multiply
incorrectly when zone count changes. Ventilation is worse: ASHRAE 62.1 multiple-zone systems do not
let you simply sum per-zone OA (the `Vot` system-level calc applies ventilation efficiency). HVAC
autosizing per zone vs per system also changes with zoning. We need the rules that keep totals
invariant across modes and flag where they legitimately differ.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Internal-load specification basis (conservation under splitting)

| Quantity | Recommended E+ basis | Conserved under zone-splitting? | Gotcha | Source |
|---|---|---|---|---|
| Lighting | `Watts/Area` | yes (scales with area) | | |
| Equipment | `Watts/Area` | | | |
| Occupancy | `People/Area` | | | |
| Any absolute/`Watts/Zone` loads (elevators, IT) | | (must be assigned to ONE zone, not replicated) | | |

> Identify any load a prototype specifies **per building** (e.g. elevators, central servers) that must
> be placed in exactly one zone and NOT multiplied across split zones.

### Table 2 — Ventilation / outdoor-air under multiple zones

| Item | Rule | Source (62.1 / E+) |
|---|---|---|
| Per-zone OA basis (`Flow/Person` + `Flow/Area`) | | |
| Multiple-zone system OA — sum vs `Vot` (ventilation efficiency) | | |
| Does splitting into core/perimeter change *system* OA? | | |
| OpenUBEM recommendation (zonal PTAC today — per-zone OA; confirm) | | |

### Table 3 — Schedules & occupancy diversity

| Item | Rule | Source |
|---|---|---|
| Same archetype schedule applied to all zones of a building? | | |
| Occupancy diversity factor (does splitting change effective diversity)? | | |
| Should core and perimeter share one schedule or differ? | | |

### Table 4 — HVAC capacity & autosizing under resolution

| Item | Rule | Source |
|---|---|---|
| Per-zone autosizing (`Sizing:Zone`) — capacity = sum of zones ≈ building total? | | |
| Does core/perimeter splitting change total installed capacity vs single zone? | | |
| Fan/pump power conservation when zone/terminal count changes | | |
| Part-load / diversity effect of more zones on plant sizing | | |

### Table 5 — Conservation test matrix (the invariant)

| Quantity | building (1 zone) | floor (N) | zone (~5N) | Must be equal? |
|---|---|---|---|---|
| Total lighting energy | | | | yes |
| Total equipment energy | | | | yes |
| Total occupancy | | | | yes |
| Total design OA | | | | (yes, modulo Vot) |
| EUI denominator (footprint × N) | | | | yes (identical) |

---

## Part C — Synthesis (rule block)

Give the **conservation rule set**: which E+ basis to use for each quantity so totals are invariant
under splitting, the ventilation handling (per-zone vs system Vot), the diversity policy, and a list
of **per-building loads that must NOT be replicated**. State the expected residual difference (if any)
between modes for the *same* building, so the manager can distinguish a real resolution effect from a
bookkeeping bug.

## Output format (follow exactly)

1. **Lead with Tables 1–5 fully populated.**
2. Then Part C rule set + expected residual.
3. Cite E+ load/OA objects, 62.1 multi-zone, prototype load basis.
4. **"Confidence and caveats":** the most likely double-count/loss pitfall.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **State the conservation invariant explicitly** (totals equal across modes; only distribution changes).
- **Resolve ventilation** (sum vs Vot) for multiple-zone splitting.
- **Flag any per-building load that must live in one zone only.**
- **Address HVAC capacity/fan/pump conservation.**
- **No fabricated precision;** flag GAPs with a defensible default.
- **Stay on topic.** If it is not about partitioning/conserving a building total, cut it.

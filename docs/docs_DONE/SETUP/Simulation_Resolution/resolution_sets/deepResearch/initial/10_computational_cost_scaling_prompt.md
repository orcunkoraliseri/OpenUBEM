# Deep-Research Prompt 10 — COMPUTATIONAL COST & SCALING at city scale per resolution mode

> SCOPE GUARD — READ FIRST. This is an **engineering cost-model** task. The deliverable is the
> **EnergyPlus runtime, memory, and storage** scaling with zone count, so OpenUBEM can predict the
> cost of running each resolution mode across thousands of buildings and decide when `zone` level is
> tractable. It is NOT about accuracy (Prompt 09) or physics. If you are writing about anything other
> than **how cost scales with zones/buildings and how to manage it, with a source or measurement
> method**, stop and return to the tables. See `00_README_resolution_prompt_set.md` for modes, roster,
> conventions.

---

## What this document is

A fill-in-the-blanks request modelling the compute cost of the resolution switch. OpenUBEM runs one
EnergyPlus process per building, fleets of 8,000+ buildings, in parallel (loky pool / cluster
`sbatch --array`). Zone count per building is ~1 / num_floors / ~5×num_floors across modes; the fleet
zone total is ~8k / ~20k / ~98k. We need the runtime/memory scaling law and a tractability verdict.
Treat each cell as a question; fill with a sourced figure or a stated measurement method.

## Role

Building-energy-modelling performance analyst. Trace claims to: the **EnergyPlus Engineering Reference
/ performance notes** (how solver cost scales with surfaces/zones — heat-balance per zone, view-factor
/ solar-distribution cost, warmup iterations), **published EnergyPlus benchmarking / UBEM scaling
papers**, and **EnergyPlus runtime characteristics** (per-zone vs per-surface cost, `Zone Multiplier`
savings). Where no published number exists, give a **measurement protocol** OpenUBEM can run (time a
representative building per mode) rather than a guess.

## Why this matters (so you scope correctly)

`zone` mode is ~12× the fleet zone count of `building` mode. If EnergyPlus runtime scales ~linearly
with zones, a city run that takes hours at `auto` could take a day-plus at forced `zone`. We need:
the scaling exponent (is it linear in zones? worse, due to solar distribution / interzone view
factors?), the memory footprint, the disk/output growth, and the levers (Zone Multiplier, output
trimming, `FullInteriorAndExterior` vs `FullExterior` solar distribution, parallelism) that keep it
tractable.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — EnergyPlus cost scaling with model size

| Cost driver | Scales with | Approx exponent / relation | Source |
|---|---|---|---|
| Heat-balance solve | # zones | | |
| Solar distribution / shadowing | # surfaces (and `Solar Distribution` setting) | | |
| Interzone view factors / matching | # interzone surfaces | | |
| Warmup convergence | # zones / thermal mass | | |
| Output writing | # output variables × timesteps × zones | | |

### Table 2 — Per-building cost per mode (representative MidriseApartment, 6 floors)

| Mode | Zones | Surfaces (approx) | Relative runtime | Relative memory | Measurement note |
|---|---|---|---|---|---|
| `building` | 1 | | 1× (ref) | | |
| `floor` | 6 | | | | |
| `zone` | ~30 | | | | |

> If no published figure, specify the **exact measurement**: run this one building in each mode, log
> `Elapsed time` from the `.end` / `eplusout.end` file, report the ratios.

### Table 3 — Fleet-scale projection (8,000+ buildings)

| Mode | Fleet zone total (OpenUBEM estimate) | Projected wall-clock at fixed parallelism | Storage (IDF + output) | Tractable? |
|---|---|---|---|---|
| `building` | ~8k | | | |
| `floor` | ~20k | | | |
| `zone` | ~98k | | | |

### Table 4 — Cost-control levers

| Lever | Saving | Accuracy cost | Source |
|---|---|---|---|
| `Zone Multiplier` (representative floors) | | (see Prompt 05) | |
| `Solar Distribution` = `FullExterior` vs `FullInteriorAndExterior` | | | |
| Trimming output variables / reporting frequency | | | |
| Reduced timesteps per hour (4 vs 6) | | | |
| Parallelism (loky pool / cluster array) — already used | | | |
| Skipping `zone` mode for low-rise where it adds little (hybrid) | | | |

---

## Part C — Synthesis (tractability verdict)

Give: (1) the **scaling law** (runtime ≈ f(zones)) with its exponent and dominant driver; (2) a
**tractability verdict** per mode at OpenUBEM's fleet scale (is forced `zone` a few-hour job, an
overnight job, or a cluster-only job?); and (3) the **recommended cost-control configuration** for a
city-scale `zone` run (which levers, in what order), plus a measurement protocol to calibrate the
estimate on OpenUBEM's own hardware.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated** (Table 2 may use a measurement protocol in lieu of cites).
2. Then Part C scaling law + tractability verdict + recommended config.
3. Cite E+ performance docs / benchmarking papers; where you estimate, show the method.
4. **"Confidence and caveats":** whether scaling is linear or super-linear in zones, and the risk.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Give a scaling relation** (linear / super-linear in zones) with its dominant driver.
- **Project fleet wall-clock** for each mode at OpenUBEM's scale.
- **Rank the cost-control levers.**
- **Provide a measurement protocol** where published numbers are absent (no guessing).
- **No fabricated precision;** flag GAPs. **Stay on topic** — cost/scaling only.

# Deep-Research Prompt 12 — SHADING & SOLAR CONTEXT interaction with resolution

> SCOPE GUARD — READ FIRST. This is a **solar/shading-bookkeeping** task. The deliverable is how
> **neighbour shading and self-shading** interact with zone count and building height across the
> resolution modes — i.e. whether a single full-height zone, stacked floors, or core/perimeter zones
> receive the **same external shading** correctly, and how `Solar Distribution` settings interact. It
> is NOT about window placement (Prompt 07) or accuracy synthesis (Prompt 09). If you are writing
> about anything other than **how shading/solar geometry is applied per resolution and the source**,
> stop and return to the tables. See `00_README_resolution_prompt_set.md` for modes, roster,
> conventions.

---

## What this document is

A fill-in-the-blanks request on shading × resolution. OpenUBEM already builds **real neighbour
buildings as shading surfaces** (within a shading-sphere radius) and the building self-shades via its
real footprint. As resolution changes, the receiving surfaces change (one tall wall vs per-floor walls
vs perimeter walls). We need to confirm shading is applied consistently and to flag where coarse
resolution mis-handles height-dependent shading. Treat each cell as a question.

## Role

Building-energy-modelling research analyst. Trace every rule to: the **EnergyPlus I/O Reference**
(`Shading:Building:Detailed`, `Shading:Site`, `Building` Solar Distribution field;
`ShadowCalculation`), the **EnergyPlus Engineering Reference** (shadowing algorithm, solar
distribution to interior surfaces), and **UBEM shading literature** (mutual-shading effects at
district scale). SI.

## Why this matters (so you scope correctly)

Neighbour shading is height-dependent: lower floors of a building are shaded by neighbours while upper
floors see sky. A **single full-height zone** receives shading on one tall wall and averages it — it
cannot represent "shaded base, sunny top." **Per-floor / core-perimeter** zones can. So shading is a
place where resolution genuinely changes solar gains. We also need to confirm `Solar Distribution`
(`FullExterior` vs `FullInteriorAndExterior`) behaves correctly with the core/perimeter geometry and
that shading-surface cost (Prompt 10) is acceptable.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Shading application per resolution

| Mode | Receiving surfaces | Can represent height-varying neighbour shading? | Bias if not | Source |
|---|---|---|---|---|
| `building` (1 zone, full height) | one tall wall per orientation | (no — averaged) | | |
| `floor` (1 zone/floor) | per-floor walls | (yes) | | |
| `zone` (core/perimeter) | perimeter walls per floor | (yes) | | |

### Table 2 — Solar Distribution setting interaction

| Setting | Behaviour | Works with core/perimeter? | Cost | Source |
|---|---|---|---|---|
| `MinimalShadowing` | | | | |
| `FullExterior` | | | | |
| `FullInteriorAndExterior` | | (interior solar to core?) | | |
| Recommended for OpenUBEM at each resolution | | | | |

### Table 3 — Self-shading & mutual shading at district scale

| Effect | Resolution dependence | Magnitude (if published) | Source |
|---|---|---|---|
| Self-shading from own massing (L/U shapes) | | | |
| Mutual shading from neighbours (dense urban) | | | |
| Importance vs resolution for cooling-dominated cities (LA/Austin) | | | |

### Table 4 — Practical confirmations

| Item | Confirm | Source |
|---|---|---|
| OpenUBEM's shading surfaces apply to all zones of a building (not just one) | | |
| Shading-sphere radius adequacy across resolutions | | |
| `ShadowCalculation` frequency/method recommendation at fleet scale | | |

---

## Part C — Synthesis

State (1) at which resolutions height-varying neighbour shading is captured vs lost and the **bias of
losing it** (likely cooling under-/over-estimate at the base in dense cells); (2) the recommended
`Solar Distribution` per mode; and (3) any confirmation/fix needed in OpenUBEM's shading application so
all zones of a building receive the correct shading.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C synthesis.
3. Cite E+ shading/solar-distribution docs and ≥1 district-shading study.
4. **"Confidence and caveats":** where coarse resolution most distorts solar (dense, tall, sunny cities).
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **State the bias** of single-zone averaging of height-varying shading.
- **Recommend a `Solar Distribution` setting per mode**, confirming core/perimeter compatibility.
- **Confirm shading applies to all zones**, not one.
- **No fabricated precision;** flag GAPs. **Stay on topic** — shading/solar geometry only.

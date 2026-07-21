# Deep-Research Prompt L12 — MIXED-USE & VERTICAL HETEROGENEITY (ground-floor retail podiums, per-floor program change)

> SCOPE GUARD — READ FIRST. This prompt handles the fact that a building's program can **change by
> floor** — a residential tower over a retail/parking podium, an office over ground-floor shops, a hotel
> with ballroom/lobby floors below guest-room floors. Deliver: how the field models vertical program
> heterogeneity in UBEM, and how `layoutGenerator.py` should vary the layout floor-to-floor within one
> building. Do NOT re-derive per-archetype layouts (that's `L08`–`L10`) — this is about *stacking
> different layouts vertically*. See `00_README_layoutgenerator_prompt_set.md` for shared facts.

---

## What this document is

The vertical-stacking reference. OpenUBEM assigns **one archetype per building** and stacks identical
floors. But real mixed-use buildings have a different program on the ground floor (retail podium) than
above (residential/office). The manager needs to know whether OpenUBEM should attempt per-floor program
variation at all (does OSM even support it?), and if so, the minimal defensible scheme — e.g. a
ground-floor override for `building=commercial` tags under a residential tower.

## Role

Mixed-use / UBEM archetype research analyst. Ground the treatment in UBEM literature on mixed-use
buildings and vertical zoning, OSM tagging practice for mixed-use (`building=residential` +
`shop`/`amenity` on ground floor; `building:part`), and the DOE prototype practice (do any prototypes
model a distinct ground floor?). Be honest about the data limits — OpenUBEM may have no reliable per-floor
program signal.

## Why this matters (so you scope correctly)

Ground-floor retail has very different loads (high LPD/EPD, different schedule) than the apartments above,
and it is the most common mixed-use pattern in dense stock. But inferring it requires data OpenUBEM may
not have. This prompt decides whether vertical heterogeneity is in-scope for the first layoutGenerator
(likely a documented deferral) or handled by a simple, cited ground-floor rule.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Vertical heterogeneity patterns

| Pattern | Prevalence | Program by floor | Data signal available (OSM?) | Source |
|---|---|---|---|---|
| Residential over retail podium |  |  |  |  |
| Office over ground-floor retail |  |  |  |  |
| Hotel: podium (lobby/ballroom) + tower (rooms) |  |  |  |  |
| Uniform (single use all floors) |  |  |  |  |

### Table 2 — How the field models it

| Approach | Description | UBEM tool using it | Fits OpenUBEM (one-archetype-per-building) model? | Source |
|---|---|---|---|---|
| Ignore — single archetype all floors |  |  |  |  |
| Ground-floor override rule |  |  |  |  |
| Per-floor archetype from `building:part` |  |  |  |  |
| Vertical mix fraction (area-weighted) |  |  |  |  |

### Table 3 — Fit to OpenUBEM

| Question | Answer + source |
|---|---|
| Does OSM reliably signal ground-floor use under a residential tower? |  |
| Is a "ground-floor = retail if `shop`/`amenity` present, else same as building" rule defensible? |  |
| Should the first layoutGenerator defer vertical heterogeneity (document it) or include a simple rule? |  |
| Does per-floor layout change break the identical-floor-stack + zone-multiplier optimization? |  |

---

## Part C — Synthesis (the vertical-scope decision)

Give: (1) a clear **in-scope / defer recommendation** for vertical heterogeneity in the first
layoutGenerator, with rationale; (2) if in-scope, the **minimal cited ground-floor rule**; (3) the data
honesty statement — what OSM can and cannot tell us; (4) the impact on the zone-multiplier/identical-floor
optimization. Keep this tight — this is a low-priority scoping prompt.

## Output format (follow exactly)

1. **Lead with Tables 1–3 fully populated.**
2. Then Part C scope decision.
3. Cite UBEM/OSM-practice source per claim.
4. **"Confidence and caveats":** the data-availability uncertainty.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Give a definite in-scope-or-defer recommendation** — do not leave it open.
- **Be explicit about OSM data limits** — no assuming a signal that isn't there.
- **No fabricated precision;** flag GAPs. **Stay on topic** — vertical program stacking only, not
  per-archetype layouts (`L08`–`L10`).

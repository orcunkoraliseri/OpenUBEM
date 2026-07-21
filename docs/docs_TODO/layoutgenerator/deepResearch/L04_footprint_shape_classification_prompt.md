# Deep-Research Prompt L04 — FOOTPRINT SHAPE CLASSIFICATION & MORPHOLOGICAL TYPOLOGY (detecting L / U / T / O from the polygon)

> SCOPE GUARD — READ FIRST. This prompt answers **how to look at a raw OSM footprint polygon and decide
> which shape class it is** — so `layoutGenerator.py` can route each building to the right layout strategy
> (rectangle → core/perimeter; L/U/T → decompose-into-wings; O → courtyard-corridor; ribbon → single
> spine; blob → fallback). Deliver the **typology** (the named shape classes UBEM/urban-morphology uses)
> and the **detection metrics** (compactness, rectangularity, convexity, skeleton-branch count, etc.) that
> distinguish them. Do NOT specify the slicing algorithms that act *after* classification (that's `L05`)
> and do NOT define the per-class room program (that's `L06`–`L10`). See
> `00_README_layoutgenerator_prompt_set.md` for shared facts.

---

## What this document is

The routing-key reference: a footprint must be *classified* before it can be laid out. OpenUBEM currently
makes an implicit binary distinction only — "core forms cleanly" vs. "doesn't" (narrow) and "has interior
ring" vs. "doesn't" (courtyard) — with no named typology. The manager needs the field's established
building-footprint shape taxonomy and the geometric metrics that assign a polygon to a class, so
`layoutGenerator.py` can dispatch deterministically. This is the "which branch of the generator runs"
decision.

## Role

Urban-morphology / GIS shape-analysis research analyst. Ground the typology in the building-morphology and
urban-form literature (e.g. Steadman's building-form taxonomy; the "pavilion / court / slab / point"
morphological families; urban-morphometrics work — Fleischmann/momepy, Schirmer & Axhausen building-shape
metrics) and the GIS shape-descriptor literature (compactness / Polsby-Popper, rectangularity, convexity/
solidity, elongation, form-factor, fractal dimension). Ground the skeleton/branch-based detection in the
computational-geometry literature. Map every metric to a concrete `shapely` / `momepy` computation where
possible.

## Why this matters (so you scope correctly)

Misclassification cascades: call an L-shape "compact" and the core buffer produces a weird sliver core;
miss a courtyard and geomeppy fatals. A robust, published set of shape descriptors with defensible
thresholds (zero-fitted-parameters) is what lets the generator branch safely. This prompt gives the
manager the named classes, the metrics, and — critically — the *threshold values* the field uses, or a
flagged GAP where OpenUBEM must decide one.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — The footprint shape typology

| Shape class | Definition | Prevalence in urban stock (cite if known) | Right layout strategy (preview) | Source |
|---|---|---|---|---|
| Compact rectangle / bar |  |  | core/perimeter |  |
| L-shape |  |  | decompose → 2 wings |  |
| U-shape |  |  | decompose → 3 wings / court-corridor |  |
| T / cross / plus |  |  | decompose → wings from junction |  |
| O-shape / courtyard (interior ring) |  |  | perimeter ring corridor |  |
| Slab / elongated bar |  |  | single-spine corridor |  |
| Thin ribbon (narrow, no core) |  |  | single-zone-per-floor fallback |  |
| Irregular / concave blob |  |  | fallback |  |
| Point / tower (small compact) |  |  | core/perimeter or single |  |

### Table 2 — Shape-descriptor metrics that separate the classes

| Metric | Definition / formula | What class it detects | Typical threshold value (cite or GAP) | `shapely`/`momepy` computation |
|---|---|---|---|---|
| Rectangularity (area / min-rot-bbox area) |  |  |  |  |
| Convexity / solidity (area / convex-hull area) |  |  |  |  |
| Compactness (Polsby-Popper, 4πA/P²) |  |  |  |  |
| Elongation / aspect ratio (bbox) |  |  |  |  |
| Has interior ring (`polygon.interiors`) |  | O-shape |  | `list(poly.interiors)` |
| Straight-skeleton branch count |  | L/U/T/cross |  |  |
| Min inscribed-circle / erosion radius vs. perimeter depth |  | narrow |  |  |
| Number of significant corners (simplified vertices) |  |  |  |  |

### Table 3 — Decision logic (how metrics combine into a class)

Propose (from the literature) the *ordered* decision rules. Fill the threshold or mark GAP.

| Order | Test | If true → class | Threshold + source |
|---|---|---|---|
| 1 | interior ring present? |  |  |
| 2 | erosion by 4.57 m empties / core < 10 m²? |  |  |
| 3 | rectangularity ≥ τ and convexity ≥ τ? |  |  |
| 4 | skeleton has N branches / concave corners? |  |  |
| 5 | elongation ≥ τ? |  |  |
| default | (else) |  |  |

### Table 4 — Fit to OpenUBEM

| Question | Answer + source |
|---|---|
| Do OpenUBEM's two implicit tests (core<10 m², has-interior-ring) correspond to named morphological classes? |  |
| Is there a published, threshold-defensible rectangularity/convexity cutoff to call a footprint "compact enough for core/perimeter"? |  |
| Can `momepy` / `shapely` compute all needed metrics without a fitted model (zero-fitted-parameters)? |  |
| Should very small/thin footprints be classified out of room-level entirely (and just single-zoned)? |  |

---

## Part C — Synthesis (the classifier spec)

Give: (1) the **recommended shape typology** OpenUBEM should adopt (the minimal set of classes that map
1:1 to layout strategies); (2) the **ordered decision rule** with each threshold either cited or flagged
"GAP — needs manager decision" + closest defensible default; (3) confirmation that every metric is
computable in `shapely`/`momepy` with no fitted parameters; (4) the class whose detection is least robust
(most likely to misroute) and what disambiguates it.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C classifier spec.
3. Cite a morphology source for each class and a GIS/geometry source for each metric.
4. **"Confidence and caveats":** which threshold is least grounded and most in need of a manager call.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Every class must map to exactly one layout strategy** (no ambiguous routing).
- **Every threshold is either cited or explicitly flagged GAP** — no silent invented cutoffs
  (zero-fitted-parameters).
- **All metrics expressible in `shapely`/`momepy`** — flag any needing a trained model.
- **No fabricated precision;** flag GAPs. **Stay on topic** — shape *classification/detection* only, not
  the slicing algorithms (`L05`) or room programs (`L06`+).

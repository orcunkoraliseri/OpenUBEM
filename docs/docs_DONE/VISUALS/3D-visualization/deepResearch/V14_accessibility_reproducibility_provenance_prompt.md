# Deep-Research Prompt V14 — ACCESSIBILITY, REPRODUCIBILITY & PROVENANCE (faithful, trustworthy views)

> SCOPE GUARD — READ FIRST. This prompt is where the **faithful-to-model hard constraint gets operationalized**:
> provenance surfacing (which resolution mode a building was simulated at, which inputs were imputed/
> low-confidence — ties to the `input/imputation/` and `simulation-Resolution/` arcs), reproducible builds,
> export/share, and validating the 3D view does not misrepresent the model. It covers the **accessibility
> principle** (colour-blind-safe, contrast, keyboard nav) but defers the concrete palette/colormap
> specification to `V09` — do not re-derive colormaps here. NOT deployment mechanics (that is `V13`). See
> `00_README_3dviz_prompt_set.md` for shared facts, roster, conventions.

> RESEARCH BUDGET — KEEP IT BOUNDED. Run this cheaply, in a SINGLE pass. Hard caps: **≤6 web searches and
> ≤10 page fetches, total.** After that pass, fill the required tables + Part C and STOP — do not iterate
> toward "comprehensive." Deliverable is the tables + Part C only: no preamble, no literature review beyond
> what the cells and synthesis need. Any cell you cannot fill within budget = mark it `GAP`; do not spend
> extra searches chasing one cell. **Do NOT spawn sub-agents or invoke skills to do this research** — run
> the searches yourself with plain web-search/fetch only; delegating to agents or skills multiplies token
> spend. If run by a Sonnet employee: model Sonnet, effort medium.

---

## What this document is

The trust layer for the viewer. OpenUBEM's pipeline already has real, documented uncertainty a static PNG
never has to disclose: buildings simulated at different **resolution modes** (`building`/`floor`/`zone`/
`auto` — interior detail varies), inputs that were **imputed** rather than observed (the `input/imputation/`
arc's confidence tiers), and archetype classifications that carry their own confidence. A 3D viewer that
paints all of this with equal visual certainty — a beautifully rendered building next to another that is
90% imputed guesswork, indistinguishable on screen — actively misleads the user, which is precisely what the
faithful-to-model constraint forbids. This prompt designs how the viewer surfaces that provenance, stays
reproducible build-to-build, and is validated against the actual model rather than just "looking right."

## Role

Data-provenance / visualization-ethics / reproducible-research analyst. Ground provenance-surfacing
patterns in recognized practice: **uncertainty visualization literature** (e.g. established techniques for
encoding confidence alongside a primary value — hatching, transparency, border treatment, a separate
confidence layer), **FAIR/reproducibility principles** applied to generated artifacts (deterministic build
identity, versioning, checksums), **WCAG 2.1** for contrast/keyboard-navigation accessibility, and **CVD
(colour-vision-deficiency) accessibility** research (cite the same family `V09` uses — Brewer/Harrower,
viridis/cividis — but only at the principle level here). Cross-reference OpenUBEM's own
`input/imputation/` and `simulation-Resolution/` design docs for the actual confidence/mode vocabulary
already defined — do not invent new terms for concepts that already have names in those arcs.

## Why this matters (so you scope correctly)

This prompt is the audit gate for the whole set: every other prompt's recommendation must pass through this
one's provenance and reproducibility rules before the manager can call the viewer trustworthy. It is also
where the two hard constraints most directly collide with "make it look good" — this prompt must resolve
that tension explicitly rather than let coloring/UX prompts quietly ignore it.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Provenance-surfacing

| What must be shown | Source of the fact (OpenUBEM field/doc) | How a viewer exposes it (badge / overlay / filter / border treatment) | Fails silently today? (does the static PNG currently hide this) | Source |
|---|---|---|---|---|
| Resolution mode (`building`/`floor`/`zone`/`auto`) the building was simulated at |  |  |  |  |
| Imputed vs. observed input(s) feeding the building's archetype/parameters |  |  |  |  |
| Archetype-classification confidence (per the misclassification-threshold work) |  |  |  |  |
| Whether an output (EUI/carbon/hourly) is from a completed simulation vs. a fallback/estimate |  |  |  |  |

### Table 2 — Reproducibility

| Question | Answer + source |
|---|---|
| Given the same pipeline inputs and the same code version, does the recommended viewer build produce a byte-identical (or otherwise verifiably identical) artifact? |  |
| What should be embedded in the artifact to make its provenance self-evident (pipeline run ID/commit hash/timestamp, resolution-mode summary)? |  |
| What is the versioning story if the coloring spec (`V09`) or LOD ladder (`V04`) changes between pipeline runs — does an old exported viewer silently become inconsistent with a new one? |  |

### Table 3 — Accessibility checklist

| Concern | Requirement | Source |
|---|---|---|
| Colour-vision deficiency (defer palette specifics to `V09`; state the principle here) |  |  |
| Contrast (WCAG 2.1 AA/AAA target for UI chrome — legend, labels, tooltips) |  |  |
| Keyboard navigation (can a user operate camera/selection/filters without a mouse — at least a documented minimum) |  |  |
| Text labels / non-colour-only encoding (does every colour-encoded value also have a text/label fallback) |  |  |

### Table 4 — Validation that the view is faithful-to-model

| Validation | What it checks | How to perform it (manual spot-check vs. automatable) | Source |
|---|---|---|---|
| Geometry round-trip (does the exported scene's vertices match the source IDF surfaces within tolerance) |  |  |  |
| Value round-trip (does a coloured building's displayed value match `eui_summary.json`/the source file exactly) |  |  |  |
| Provenance round-trip (does a flagged-imputed building actually correspond to a real imputation-tier record) |  |  |  |
| LOD-gate correctness (does a `building`-mode building never display zone-level detail — cross-ref `V04`) |  |  |  |

---

## Part C — Synthesis (the provenance & trust spec)

Give: (1) the **concrete provenance-surfacing design** — exactly which badge/overlay/filter mechanism
exposes resolution mode and imputation confidence, tied to the schema `V05` would carry it in; (2) the
**reproducibility rule** OpenUBEM should adopt (what gets embedded/versioned in every exported artifact);
(3) the **accessibility minimum bar** for MVP (which WCAG/CVD requirements are must-have vs. deferrable);
(4) the **validation procedure** the manager should run before accepting any viewer build as faithful —
stated concretely enough to become checkpoints in a PLAN doc.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C spec.
3. Cite the uncertainty-visualization literature, WCAG 2.1 clauses, and OpenUBEM's own imputation/
   resolution-mode design docs (by file) for every claim.
4. **"Confidence and caveats":** which provenance-surfacing pattern is least evidenced by peer UBEM-tool
   practice (most tools may not do this at all — say so if true).
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Every provenance item in Table 1 must map to a real OpenUBEM/imputation-arc field**, not an invented
  concept — cite the actual design doc.
- **Give a concrete, checkable validation procedure** (Table 4) — this is the enforcement mechanism for the
  faithful-to-model constraint across the whole set.
- **Do not re-derive the colormap/palette spec** — defer to `V09` and only state the accessibility principle.
- **No fabricated precision;** flag GAPs. **Stay on topic** — the *provenance, reproducibility, and
  accessibility-principle* layer only, not the coloring spec (`V09`) or deployment mechanics (`V13`).

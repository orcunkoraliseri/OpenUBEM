# Deep-Research Prompt L13 — GENERATIVE & ML FLOORPLAN SYNTHESIS (the frontier — Graph2Plan, HouseGAN, procedural generators)

> SCOPE GUARD — READ FIRST. This is the **frontier / advanced-tier** prompt. Survey ML and procedural
> *automated floorplan generation* methods — GAN/graph/diffusion floorplan synthesis (HouseGAN,
> Graph2Plan, RPLAN, House-Diffusion) and rule-based procedural building generators — and judge whether
> any is usable by OpenUBEM under its two hard constraints (zero-fitted-parameters, provenance). It is NOT
> the geometric-decomposition toolkit (that's `L05`, which is deterministic geometry, not ML). Frame this
> as "is the heavy machinery worth it, or does deterministic corridor+packing (`L06`) already suffice?"
> See `00_README_layoutgenerator_prompt_set.md` for shared facts.

---

## What this document is

The build-vs-skip appraisal for generative layout. There is a rich CS literature on generating plausible
floorplans from a footprint + a room-adjacency graph. It produces *architecturally* convincing plans —
but OpenUBEM needs *thermally sufficient* zones, must not fit parameters to validation targets, must emit
provenance, and must be reproducible and cheap at city scale (thousands of buildings). This prompt tells
the manager whether these methods clear that bar or are a research distraction relative to the
deterministic `L06` method.

## Role

Generative-geometry / ML-for-architecture research analyst. Ground the survey in the primary papers:
**HouseGAN / HouseGAN++** (Nauata et al.), **Graph2Plan** (Hu et al.), **RPLAN** dataset (Wu et al.),
**House-Diffusion** and recent diffusion-based plan generators, plus **procedural building-interior
generators** (rule/grammar-based, e.g. shape-grammar and the game/CityEngine-style interior generators).
For each, state training-data needs, determinism/reproducibility, license, and whether outputs are
thermal zones or architectural rooms.

## Why this matters (so you scope correctly)

It would be easy to over-engineer this feature with a neural floorplan generator. The manager needs a
clear-eyed verdict: these methods are trained (violating zero-fitted-parameters unless used purely as a
fixed pretrained black box), non-deterministic (a reproducibility problem for a validation baseline),
data-hungry, and produce room-detail beyond thermal need. This prompt should almost certainly conclude
"defer / not for the MVP" — but must justify that with sources, and flag the narrow case (if any) where a
generative method adds real value.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Generative/procedural floorplan method catalogue

| Method | Approach | Input → output | Training data needed | Deterministic / reproducible? | Output = thermal zones or architectural rooms? | Source |
|---|---|---|---|---|---|---|
| HouseGAN / ++ |  |  |  |  |  |  |
| Graph2Plan |  |  |  |  |  |  |
| RPLAN-based |  |  |  |  |  |  |
| House-Diffusion |  |  |  |  |  |  |
| Shape-grammar / procedural |  |  |  |  |  |  |

### Table 2 — Fit to OpenUBEM's two hard constraints

| Method | Zero-fitted-parameters? (pretrained-frozen counts only if published + fixed) | Emits provenance? | Reproducible for a validation baseline? | City-scale cost acceptable? | Verdict (skip / defer / narrow-use) |
|---|---|---|---|---|---|
| HouseGAN |  |  |  |  |  |
| Graph2Plan |  |  |  |  |  |
| House-Diffusion |  |  |  |  |  |
| Procedural/grammar |  |  |  |  |  |

### Table 3 — Value vs. the deterministic L06 method

| Question | Answer + source |
|---|---|
| Do generative plans improve *thermal* accuracy over deterministic corridor+packing, or just visual realism? |  |
| Is there any UBEM/BEM study that used a generative floorplan model for energy simulation? |  |
| Does non-determinism break the ability to reproduce the validation baseline? |  |
| Could a *procedural* (rule-based, deterministic) generator be a middle ground that satisfies the constraints? |  |

---

## Part C — Synthesis (the frontier verdict)

Give: (1) a clear **skip / defer / narrow-use verdict** for generative floorplan ML in OpenUBEM, with the
constraint(s) that drive it; (2) whether any **deterministic procedural** (non-ML) generator offers value
over `L06` without violating constraints; (3) the single narrow case (if any) where a generative method
would be worth revisiting later; (4) confirmation that the deterministic `L06`/`L05` path is the right MVP
and this tier is future work.

## Output format (follow exactly)

1. **Lead with Tables 1–3 fully populated.**
2. Then Part C frontier verdict.
3. Cite the primary paper per method.
4. **"Confidence and caveats":** which method's constraint-fit is least certain.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Judge every method against zero-fitted-parameters, provenance, reproducibility, and city-scale cost.**
- **Distinguish pretrained-frozen from trained-on-our-data** — only the former can even be considered.
- **Give a definite verdict** — this prompt exists to prevent over-engineering.
- **No fabricated precision;** flag GAPs. **Stay on topic** — generative/procedural *floorplan synthesis*
  only, not deterministic geometry (`L05`).

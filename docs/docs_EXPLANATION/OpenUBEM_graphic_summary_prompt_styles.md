# Graphic Summary Prompt Styles — A Reusable Reference

**What this document is:** a portable reference for writing **image-generation prompts** that summarize a completed technical pipeline, feature, or project arc as a single graphic — for pasting into an external image model (Gemini web, or any comparable tool). It documents **three prompt styles**, when to use each, their visual characteristics, and the prompting technique that makes each one work reliably. This document is **project-agnostic** — it happens to live in OpenUBEM's docs because that is where it was first written, but it carries no OpenUBEM-specific content and is meant to be handed to a fresh Claude session on **any other project** as a ready-made style guide. For a concrete worked example built from this reference, see the three prompt files under [`docs/docs_DONE/SETUP/layoutAssigner/general-abstract/`](../docs_DONE/SETUP/layoutAssigner/general-abstract/) (§5 below).

---

## 1. Why this exists

After closing out a feature or an arc, a single well-made graphic communicates "what this thing does" far faster than a page of prose — for a slide, a README header, a paper figure, or just a mental map for the next person who opens the folder. But a good image-generation prompt is not obvious on the first try: it needs an explicit visual style, an explicit orientation, and a precise, ordered list of the real technical steps — vague prompts ("draw a diagram of the pipeline") produce generic, inaccurate results. This document exists so that style and prompting-technique decisions don't have to be re-derived from scratch every time; three tested archetypes cover almost every practical case.

---

## 2. The three styles

| Style | Best for | Visual realism | Text density | Default orientation |
|---|---|---|---|---|
| **Technical Flowchart** (§2.1) | Engineering docs, READMEs, architecture reviews | Flat vector, no realism | High — every step labeled precisely | **Horizontal** (left-to-right) |
| **3D Axonometric Realistic** (§2.2) | Slide covers, external-facing storytelling | Photorealistic 3D render | Low — a handful of short floating labels | Horizontal, multi-vignette |
| **Hybrid — Annotated Axonometric** (§2.3) | A single "hero image" that must also work as a reference figure | Photorealistic 3D render + technical overlay | High — same density as the flowchart, layered onto the render | Horizontal, multi-vignette |

### 2.1 Technical Flowchart

**Purpose:** precision over spectacle. Communicates exact process steps, decision branches, and field/function names to a technical reader. Works well embedded directly in a markdown doc or a slide appendix.

**Visual characteristics:**
- Flat vector shapes only — no photorealism, no 3D, no shading beyond flat fills.
- Muted, professional palette: one or two neutral tones (navy/slate/white) plus a **single accent color** reserved for exception paths and warnings — never used decoratively.
- Rectangles = process steps; diamonds = decisions; dashed borders = exception/fallback paths.
- A visually separated footnote strip for caveats/limitations (thin border, smaller gray text, a divider line) — keeps honesty about limitations from being lost inside the main flow.
- **Default orientation: horizontal (left-to-right)**, one continuous spine, wide landscape canvas. Reserve vertical drops only for a side-branch (e.g. a decision's "no" path), never for the main chain. Vertical top-to-bottom flowcharts are harder to read at a glance and read as "cramped documentation" rather than a clean architecture diagram — prefer horizontal by default unless the step count is so large that horizontal would force illegibly small text.

**Prompting technique:**
- Enumerate every box in the exact order you want them drawn, numbered.
- Give the **exact label text in quotes** for every box, plus a smaller sub-label with the technical detail (field names, formulas, function names) — image models render short quoted strings far more reliably than long paragraphs.
- State the shape per step type explicitly (rectangle / diamond / rounded-input-box).
- State arrow direction explicitly ("connected by rightward arrows").
- Call out anything that must be visually distinct (final box, exception branch, footnote) and say exactly how (bold border, dashed border, accent color, separate divider line).
- End with an explicit orientation instruction and a fallback rule ("shrink box width/font rather than wrapping to a second row").

### 2.2 3D Axonometric Realistic

**Purpose:** tells the *story* of a pipeline viscerally, for an audience that doesn't need (or want) technical density — a title slide, a portfolio piece, a cover image.

**Visual characteristics:**
- Isometric/axonometric camera angle, held **identical across every vignette** in the sequence.
- Photorealistic materials and lighting: soft studio light, gentle shadows, realistic glass/concrete/metal — a neutral pale background, no sky or landscape context competing for attention.
- Composed as a **left-to-right sequence of vignettes**, each on its own small floating ground plane, linked by a thin consistent connector (arrow or ribbon).
- Ghosting/translucency used to show before/after or repetition (a faint dashed outline of an earlier state, translucent stacked repeats of a floor/unit).
- **One consistent accent color** running through every connector and one glowing highlight per vignette — this is what makes five separate vignettes read as one continuous story instead of five unrelated images.
- Minimal text: a handful of short floating labels only, one per vignette. Image models handle a few short words far more reliably than dense paragraphs of rendered text — do not attempt to cram technical detail into this style (that is what §2.3 is for).

**Prompting technique:**
- Describe each vignette as a physical scene: what object sits on the ground plane, what materials, what's ghosted/translucent, what the one short label says.
- Fix the camera, lighting, and palette **once**, at the top of the prompt, and state that every vignette must share them.
- Use spatial/physical metaphors for abstract technical ideas (a scaling grid with corner arrows for "resizing", a snowflake/sun split for "climate handoff", stacked translucent floors for "repetition/multiplier") rather than trying to render abstract concepts as text.
- Explicitly state what to exclude (no extra logos, no watermarks, no people, no background landscape) — image models fill empty space with unwanted detail unless told not to.

### 2.3 Hybrid — Annotated Axonometric (Technical Illustration)

**Purpose:** one image that must do both jobs at once — look good enough for a cover/slide **and** carry enough real technical content to work as a documentation figure or paper illustration. Think a premium car-brochure exploded-engine diagram: photorealistic, but every part is labeled precisely.

**Visual characteristics:**
- Same realistic axonometric rendering base as §2.2 (same camera/lighting/palette discipline).
- A full annotation layer on top: thin leader-lines connecting each rendered element to a small rectangular technical card (white card, thin border, small clean text) — treat annotations as **physical set-dressing** (cards, engraved plaques, leader-lines), not flat overlay text, so they sit believably inside the 3D scene.
- Decision points can be rendered as a physical object (e.g. an engraved glass/acrylic diamond plaque) rather than an abstract diamond shape — this is what keeps the hybrid feeling like one coherent illustration instead of a diagram pasted onto a photo.
- Caveats/limitations get their own visually distinct plaque (different material — e.g. matte dark slate vs. the bright accent cards used for the main flow) so they read as a deliberate footnote, not a missed detail.
- Same single consistent accent color rule as §2.2, extended to the leader-lines and card borders.

**Prompting technique:**
- Write it as a fusion of §2.1 and §2.2: the vignette structure and material/lighting discipline of the axonometric style, plus the exact numbered step list and **verbatim quoted technical strings** of the flowchart style.
- Explicitly instruct the model not to paraphrase or shorten the quoted technical strings — this style lives or dies on whether the dense text survives generation legibly.
- Call out the caveat plaque's different material explicitly, the same way §2.1 separates its footnote strip.

---

## 3. Universal prompting principles (apply to all three styles)

1. **State the style and orientation once, up front, unambiguously** — never assume the model will infer either from context.
2. **Enumerate real steps in strict order**, numbered, sourced from the actual pipeline/spec — never invent a step to fill space, and never let the model reorder or merge steps.
3. **Quote exact text** whenever text must appear in the image — short quoted strings render reliably; long unquoted paraphrases do not.
4. **Fix the visual "constants" once** (camera angle, palette, lighting, accent color) and state explicitly that they must stay consistent across every panel/vignette/box.
5. **Separate caveats/limitations visually** from the main content (footnote strip, dashed border, distinct material) — a summary graphic that quietly omits known limitations is dishonest; give them their own clearly-marked space instead of hiding them.
6. **Say what to exclude** — logos, watermarks, people, background context — explicitly, since image models default to filling empty space.
7. **Give a legibility fallback rule** ("shrink text/boxes rather than wrapping/reordering") so the model has an explicit instruction for when the content doesn't fit the requested layout.

---

## 4. Reusing this in a new project

1. Write down the real pipeline/feature steps in order (aim for 5–10; merge sub-steps if there are more) — pull the exact names/fields/formulas from the actual code or spec, not from memory.
2. Pick a style from §2 based on the audience: technical reader → §2.1; non-technical/cover use → §2.2; a single image that must serve both → §2.3.
3. Copy the matching prompt structure from §2's "Prompting technique" and the worked example in §5, and substitute your own step list, labels, and one accent color.
4. Paste the finished prompt into the image model as-is; iterate on layout/legibility notes only — do not change the step content between iterations.

---

## 5. Worked example — LayoutAssigner (this project)

Three ready-made prompts built exactly to this reference, for the OpenUBEM `layout_assign` resolution-mode pipeline, live at `docs/docs_DONE/SETUP/layoutAssigner/general-abstract/`:

| File | Style |
|---|---|
| `prompt_technical_flowchart.md` | §2.1 — horizontal technical flowchart |
| `prompt_3d_axonometric.md` | §2.2 — 3D axonometric realistic, 5-vignette story |
| `prompt_3d_axonometric_technical.md` | §2.3 — hybrid annotated axonometric |

Open any of the three for a complete, filled-in example of the corresponding style's prompting technique in practice.

---

## 6. Where to go next

| You want… | Read |
|---|---|
| The three ready-made LayoutAssigner prompts | `docs/docs_DONE/SETUP/layoutAssigner/general-abstract/` |
| The OpenUBEM pipeline these prompts describe | `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` §5.1 |
| The LayoutAssigner arc's full technical record | `docs/docs_DONE/SETUP/layoutAssigner/DONE/DONE-implementation_plan.md` |

---

*A style reference, not a spec — nothing here is OpenUBEM-specific; copy it into any project that needs a one-image technical summary. 2026-07-22.*

# PROMPT — Turn the OpenUBEM checklist into ONE simple progress image

> **Purpose.** `docs/PROJECT_CHECKLIST.md` is the full, dense record of a complex multi-arc project.
> This prompt turns it into a **single, at-a-glance infographic** so a manager can grasp *where the
> project stands* in ten seconds — which arcs are done, which are live, which are parked, and what the
> current validated result is. Run it in any image / infographic / HTML-capable AI tool.
>
> **How to use.** Paste everything between the `=== PROMPT START ===` and `=== PROMPT END ===`
> markers into the tool. The prompt already contains a distilled, faithful snapshot of the project
> state (kept in sync with `PROJECT_CHECKLIST.md`), so the tool does **not** need to read the full
> checklist. If you want to refresh the snapshot, update the "PROJECT STATE" block below from the
> checklist first, then re-run.
>
> **Output you want.** One clean, legible, single-page **progress board** (a "status map"), not a
> data dump and not decorative art. Crisp text is essential — see the "Output format" note.

---

## Keeping this prompt faithful (read before running)

- This is a **visualization of an existing record**, not a re-assessment. The tool must render the
  statuses exactly as given below — it must **not invent, upgrade, downgrade, or re-judge** any arc.
- If a value is missing, the tool leaves it blank — never fills a plausible-looking guess.
- Source of truth = `docs/PROJECT_CHECKLIST.md`. This snapshot is dated **2026-07-11**; put that date
  on the image.

---

=== PROMPT START ===

You are an information designer. Produce **one single-page progress infographic** for a research
software project called **OpenUBEM** (an open-source Urban Building Energy Modeling platform). The
audience is the project lead, who is not tracking day-to-day detail and needs to understand *overall
progress at a glance*. Favor clarity and calm over density or decoration.

## What the image must communicate (in priority order)

1. **The project is a 5-stage pipeline, and all 5 stages are built.**
2. **There is one adopted, validated result right now** (the "current baseline") — show its headline
   numbers prominently.
3. **Every workstream ("arc") sits in exactly one of four states** — Done / Active / Parked / Next —
   and the viewer can see the balance at a glance.
4. **What is being worked on next.**

## Layout (suggested — a clean top-to-bottom board)

- **Title band (top):** "OpenUBEM — Project Progress" + subtitle "Snapshot 2026-07-11" + the
  one-liner: *"Open-source Urban Building Energy Modeling — data → enrichment → IDF → EnergyPlus →
  results & carbon."*
- **Pipeline strip:** five connected blocks left-to-right — `1 Data acquisition` → `2 Semantic
  enrichment` → `3 IDF generation` → `4 EnergyPlus simulation` → `5 Results & carbon`. All five
  filled/checked (built). This is the spine of the project.
- **"Current baseline" callout (make it the visual hero):** a boxed panel titled
  **"Adopted model — Phase-E full realism (zero fitted parameters)"** showing:
  - City accuracy vs measured: **NYC −31.9% · LA −6.2% · Austin −30.7%**
  - Shape fit: **R² = 0.888 / 0.920 / 0.720**
  - Scale: **12 city cells · 8,160 buildings · 99.9% EnergyPlus success**
- **Arc board:** the workstreams below, grouped into four columns/lanes by STATUS, each as a small
  card with its letter, short name, and a 4–6 word status note. Color each card by its status.
- **Legend (bottom):** the four status colors + the checklist's own marks
  (`[x]` done · `[~]` in progress · `[ ]` not started · `[!]` blocked/needs decision).

## STATUS color scheme (use exactly these four buckets)

- 🟢 **DONE / LOCKED** — completed and signed off.
- 🔵 **ACTIVE** — being worked now, or awaiting a manager decision to move forward.
- 🟡 **PARKED** — built or partly built, intentionally set aside (opt-in / off / deferred by choice).
- ❌ **CANCELLED** — discontinued and replaced (show greyed / struck-through, kept for context).
- ⚪ **NEXT / NOT STARTED** — designated to execute but not begun.

## PROJECT STATE — render these arcs exactly as listed (do not re-judge)

**🟢 DONE / LOCKED**
- Pipeline build — Steps 1–5 all built + audited.
- R4 / R5 / R6 — cluster offload + full 12-cell validation matrix (8,152 buildings, 100% E+).
- Phase-C combined resim — geometry + real DOE schedules; 12 cells clean.
- Phase-D real-HVAC — metered PTAC HVAC + service loads; basis error eliminated.
- **Phase-E full realism — CURRENT BASELINE** (physical HVAC + DHW/cooking/refrigeration).
- E-R3-3 archetype threshold fix — office/school/hotel classifier cut-points corrected.
- Resolution-mode switch (Arc F) — 4 modes GO (auto / floor / fast_zone / building).
- Interactive 3D web-viz — 12 self-contained browser neighbourhood viewers, signed off.
- Schedule digitization — real DOE schedules replace synthetic.

**🔵 ACTIVE**
- **Arc J — Input-classification framework** — deep-research I01–I03 returned; *awaiting manager
  audit → then write the implementation PLAN.* (Validates OSM-tag → archetype classification.)

**🟡 PARKED**
- Arc G — Input imputation ("OpenUBEM AI") — Phase A+B done; ML tier built-but-OFF by user choice.

**❌ CANCELLED**
- Arc H + I — layoutGenerator (room-level zoning) — **cancelled 2026-07-11, replaced by layoutAssigner.**

**⚪ NEXT / TO EXECUTE**
- **layoutAssigner** — root-level layout-engine redesign, built *instead of* (replacing) the
  cancelled layoutGenerator. Designated 2026-07-11; not yet started (empty scaffold).

## Style constraints

- Simple, modern, flat. Generous whitespace. One accent color family + the four status colors.
- **Legible text is mandatory** — every label must be sharp and readable; no garbled or decorative
  lettering, no fake/placeholder words.
- No invented data, logos, screenshots, or 3D renders. No chart the numbers above don't support.
- One page, portrait or landscape, readable when shrunk to a slide thumbnail.

## Output format

Produce the infographic as a **single self-contained SVG (or one self-contained HTML file with inline
CSS)** so all text stays crisp and editable — then, if the tool can, also export a PNG preview. (If
this tool only generates raster images, produce a clean vector-style infographic and prioritize
readable text over visual effects.)

=== PROMPT END ===

---

## Maintenance note (for the manager, not part of the prompt)

When `PROJECT_CHECKLIST.md` changes materially (an arc closes, a new arc opens, the baseline numbers
move), update the **PROJECT STATE** block and the **Current baseline** numbers above, bump the
snapshot date, and re-run. Everything else in the prompt is stable. Markdown only; binding specs
remain in `docs/docs_main/`. Created 2026-07-11.

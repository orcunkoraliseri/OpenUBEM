# Decision needed: how to package retrofit scenarios in OpenUBEM

**Purpose of this document.** This is a self-contained brief for an external reviewer (Gemini) to read
and answer. It is not an OpenUBEM plan doc and nothing in it is executed until the project owner
(a human) reads the recommendation and explicitly authorizes it. Answer the question in §5 with one
option, or a stated hybrid, and the reasoning behind it.

---

## 1. What OpenUBEM is

OpenUBEM is an Urban Building Energy Model: it takes a real building stock (real footprints, real
building types, real floor areas) for a district or city, builds one EnergyPlus IDF per building from a
prototype library, runs the fleet, and reports energy use per building and aggregated. Its stated
audience is urban planners and policy users who ask "what does this neighbourhood use today?" and then
immediately ask "what if we retrofit it?" — the second question has no answer in OpenUBEM yet. The
published fleet baseline today is **153.95 kWh/m² over 8,139 buildings** (adopted 2026-09-10) — this
number must not move as a side effect of anything decided here.

## 2. What already exists (built, tested, not yet turned on)

A retrofit-measure layer has been built as an unused library: a measure table (JSON, one row per
measure: parameters, applicability gates, a public-standard citation) and an applier module that reads
the table and mutates an IDF in memory. **Four measures exist, three shipped active, one withdrawn on
the record with a written reason:**

| Measure | Status | What it changes | Public source |
|---|---|---|---|
| `lighting_power_density` | active | Lowers installed lighting power density to a target, office archetypes only, never raises a value | ASHRAE 90.1-2022 §9.3.2 |
| `thermostat_setback` | active | Deepens heating/cooling setback schedules by a required delta-T, never narrows an existing deadband | ASHRAE 90.1-2022 §6.4.3.3.2 |
| `infiltration_tightening` | active | Tightens whole-building air leakage to a target, per calculation method, never loosens | ASHRAE 90.1-2019 Addendum t §11.5.3 / §5.4.3.1.1 |
| `envelope_u_upgrade` | **withdrawn** | Wall/roof/floor/window U-value and window SHGC upgrade | ASHRAE 90.1-2019 CZ6 assemblies |

`envelope_u_upgrade` was withdrawn because its shipped targets turned out to be byte-identical to the
code baseline OpenUBEM already applies to one archetype elsewhere in the pipeline — applying it would
either be a guaranteed no-op or leak one archetype's baseline onto another. It is not a candidate for
the campaign discussed here unless a genuinely independent target is sourced later.

**So the real base for this decision is 3 active, independently-gated measures**, each direction-locked
(only ever improves, never regresses, an already-compliant object is reported as such and left
untouched) and each provably idempotent (applying twice = applying once).

**Nothing above is wired to anything.** No campaign, no EnergyPlus run, no result channel, no viewer
change. It is a library that nothing calls, guarded by a default-OFF flag
(`SCENARIO_LAYER_ENABLED` in `openubem/config.py`), by deliberate design — the same pattern already used
for a separate PV-injection feature elsewhere in the codebase. The one thing this design choice does
**not** need to be re-litigated by: everything built so far is packaging-agnostic — the measure table
and the applier are the same artifact under any of the three options in §3.

## 3. The three packaging options

This is the open research-design decision, stated in the source technology-transfer report as a rule
that "must be chosen deliberately" before any campaign is submitted:

**(A) Cumulative ladder.** Each scenario contains the previous one, in a fixed order (e.g. baseline →
+lighting → +lighting+infiltration → +lighting+infiltration+setback). Answers *"how far can the stock go
if we do everything, step by step?"*. With 3 active measures this is baseline + 3 steps = **4 EnergyPlus
runs per building**.

**(B) Isolated single-domain runs.** Each measure is applied alone, against the same baseline, never
combined with another. Answers *"which single measure matters most, independent of the others?"*. With
3 active measures this is baseline + 3 singles = **4 EnergyPlus runs per building** — same run count as
(A), different meaning.

**(C) Full factorial.** Every combination of measures on/off is run separately: 2³ = **8 EnergyPlus runs
per building** (baseline, each single, each pair, all three together). This is the only design that
lets every measure's contribution be computed **order-free** (a Shapley-style attribution: each
measure's average marginal contribution across every possible order it could be added in).

## 4. The evidence that forces a real trade-off, not a free choice

This is measured, not a guess, from the reference project this methodology is being adapted from: in a
cumulative ladder, applying measures in a fixed order **mis-credits their individual contribution by up
to ~7 kWh/m²**, because each measure's apparent savings depend on which measures were already applied
before it (their effects are not additive — e.g. tightening infiltration after lighting is upgraded
saves a different amount than tightening it first, because internal heat gains changed). **A cumulative
ladder's results cannot be converted into an order-free attribution after the fact** — the only way to
get order-free attribution is to have run the isolated and/or combined cases separately, i.e. option
(C), or accept option (B)'s narrower "single measure in isolation" answer instead.

**Compute cost, scaled to OpenUBEM's actual fleet (8,139 buildings):**

| Option | Runs per building | Total EnergyPlus runs | What it can answer |
|---|---|---|---|
| (A) Cumulative ladder | 4 | 32,556 | "How far can the stock go, applying everything in this order?" — cannot rank individual measures fairly |
| (B) Isolated single-domain | 4 | 32,556 | "Which single measure matters most, alone?" — cannot answer combined-upgrade questions |
| (C) Full factorial | 8 | 65,112 | Both of the above, plus every combination, order-free attribution — 2x the compute of (A) or (B) |

All runs are parallelized (never sequential) on either a 32-CPU cluster array or a 20-process local
pool per the project's own compute rules — so the real cost axis is wall-clock-and-cluster-queue time
and any per-run cost, not developer effort; the applier code itself is identical under all three
options.

## 5. The question for you (Gemini)

Given:
- the stated audience (urban planners asking "what if we retrofit this neighbourhood, and with what?"),
- the measured fact that a cumulative ladder cannot be turned into a fair per-measure ranking after the
  fact, while isolated runs cannot answer "what if we combine measures",
- a fleet of 8,139 buildings where the factorial option costs exactly 2x the runs of either simpler
  option (not more, because there are only 3 active measures today, not a larger catalogue),
- and that this decision only needs to be made once, before the first campaign, but should be right the
  first time since compute already spent is not easily redone,

**recommend one option — (A), (B), (C), or a stated hybrid — and justify it on accuracy and
fitness for the stated audience, not on compute cost alone.** State explicitly what question the chosen
design can and cannot answer, and what a policy user reading the eventual output would be able to
trust versus misread.

Do not recommend adding, removing, or renaming any measure, and do not recommend any specific numeric
retrofit target — that is out of scope for this decision. Answer only the packaging-design question
above.

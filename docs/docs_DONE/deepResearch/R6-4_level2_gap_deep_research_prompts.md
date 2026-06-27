# Deep-Research Prompts — R6-4 Level-2 Single-Building Gap

**Purpose:** Inform the manager-of-manager decision on the OpenUBEM Level-2 single-building validation gap
(STOP vs PHASE-1.5 zoning vs SERVICE-LOADS vs REFERENCE-MATCH).
**Target tool:** Gemini (Deep Research mode). Paste one prompt at a time; each is self-contained.
**Authored:** 2026-06-16, by the Phase-C Opus manager session.

---

## How to use this doc

- Each section below is **one complete prompt**. Copy everything inside the fenced block into Gemini.
- The prose above each block is *for you*, not for Gemini — it says what the prompt decides and why.
- Run **A and B first** — together they settle whether STOP is the methodologically standard position.
  Run **C** only if you lean toward building service-load models; **D** only if you lean toward richer zoning.
- When the reports come back, paste them into a fresh OpenUBEM session and I'll reconcile them against V15
  and turn the conclusion into a validation-report paragraph or a PLAN doc.

### Shared context (already baked into each prompt, repeated for your reference)

OpenUBEM is an open-source Urban Building Energy Modeling (UBEM) platform. Phase-1 design choices that are
**binding and not under review**: EnergyPlus with `ZoneHVAC:IdealLoadsAirSystem` (no detailed HVAC plant),
a fixed 3-strategy thermal-zoning table (single-zone / one-zone-per-floor / perimeter-core), and DOE commercial
prototype buildings as the per-archetype reference. A "Level-2" validation round-trips each of 20 archetypes
(one building per archetype) against its DOE prototype and scores annual EUI deviation against a **±5% gate**.
Result: **1/20 PASS, median |deviation| ≈ 45%**. A per-end-use decomposition found that **~42% of the median
gap is the "Other" end-use** (fans, pumps, DHW/service hot water, HVAC parasitics, refrigeration) — loads the
ideal-loads model does not carry — with heating+cooling ≈ 36% and lighting+equipment ≈ 20%. A reporting-level
COP/fuel "basis correction" barely moved the median (45.4% → 44.5%). The neighbourhood/fleet use case
(thousands of buildings) is the actual product; single-building scoring is a diagnostic.

---

## Prompt A — Validation acceptance criteria: single-building vs aggregate

**Decides:** whether the ±5% single-building gate is an appropriate bar at all, and therefore whether
"accept the gap as a documented limitation" (STOP) is the methodologically standard position or a retreat.
This is the highest-value prompt.

```
You are a building-energy-simulation methodologist. I need a rigorous, citation-backed review of how Urban
Building Energy Models (UBEM) are validated, with a sharp distinction between individual-building accuracy and
aggregate/neighbourhood-scale accuracy.

CONTEXT
I maintain an open-source UBEM platform. It uses archetype-based modeling: each building is matched to a DOE
commercial prototype and simulated in EnergyPlus with a simplified (ideal-loads) HVAC representation. The
product use case is neighbourhood/city scale (thousands of buildings). As a diagnostic I also score individual
buildings against their reference prototype on annual EUI, using a +/-5% pass gate. At the single-building
level I see a median absolute deviation of roughly 45%, with only 1 of 20 archetypes passing. I need to know
whether a +/-5% single-building EUI gate is a reasonable acceptance criterion for archetype-based UBEM, or an
inappropriately strict bar that does not reflect how the field validates these models.

QUESTIONS TO ANSWER
1. What are the standard, published acceptance thresholds for calibrated/validated building energy models?
   Give exact numbers for ASHRAE Guideline 14-2014/2023 (monthly and hourly NMBE and CV(RMSE)), IPMVP, and
   FEMP. State precisely what each threshold applies to (a single calibrated building against measured data).
2. How do these differ from how UBEM is validated? Specifically: do UBEM validation studies report accuracy at
   the individual-building level, the aggregate (block/district/city) level, or both? What metrics and
   thresholds do they actually use, and what numeric errors do they report?
3. For archetype-based UBEM specifically, is a single-building annual-EUI deviation in the 30-50% range
   considered normal, expected, and acceptable given that archetypes deliberately discard per-building
   specificity? Find explicit statements or reported error distributions that establish what "normal"
   single-building error looks like.
4. Document the error-cancellation / aggregation effect: by how much does reported error shrink when moving
   from individual buildings to aggregate stock, in published studies? Quantify (e.g., per-building NMBE of X%
   collapsing to aggregate error of Y%). This is the crux of whether a per-building gate is even the right test.
5. Survey how the major open and academic UBEM platforms report validation: City Energy Analyst (CEA), CityBES,
   UMI/umi, TEASER, URBANopt, and any widely cited city-scale studies (e.g., Reinhart, Cerezo Davila, Hong,
   Sokol, Nagpal). For each, state the validation level (building vs aggregate), the metric, and the reported
   error.

SOURCES — prioritize, and be skeptical
- Peer-reviewed journals (Energy and Buildings, Applied Energy, Building and Environment, Sustainable Cities
  and Society), ASHRAE Guideline 14 itself, IBPSA conference papers, and platform documentation.
- Prefer primary sources with actual numbers over secondary summaries. Distinguish a calibrated single-building
  study from an uncalibrated archetype UBEM study — they have very different expectations.
- Where studies disagree, say so and give the range.

OUTPUT
- A thresholds table: standard | metric | numeric value | what it validates against.
- A UBEM-validation table: study/platform | validation level (building vs aggregate) | metric | reported error.
- A direct verdict, in 3-5 sentences with citations, answering: "Is a +/-5% single-building EUI gate an
  appropriate acceptance criterion for archetype-based UBEM, or is aggregate-level accuracy the standard target
  and 30-50% single-building deviation expected?"
- A short "confidence and gaps" note: where the evidence is thin or mixed.
Cite every numeric claim inline.
```

---

## Prompt B — IdealLoadsAirSystem and the "Other"/service-load deficit

**Decides:** whether our central diagnosis is correct — that the 42% "Other" gap is a structural omission of the
ideal-loads model rather than a bug we should fix in zoning or basis correction. Confirms (or refutes) that no
zoning/HVAC change within the ideal-loads framework can close it.

```
You are an EnergyPlus modeling expert. I need a precise, citation-backed answer about what end-uses the
EnergyPlus ideal-loads air system does and does not model, and how UBEM workflows handle the gap.

CONTEXT
My UBEM platform simulates buildings with EnergyPlus using ZoneHVAC:IdealLoadsAirSystem rather than detailed
HVAC equipment. When I compare my ideal-loads results to the DOE commercial prototype buildings (which use
fully detailed HVAC), a large share of the discrepancy lands in an "Other" end-use bucket — fans, pumps,
service/domestic hot water (DHW), refrigeration, and HVAC parasitics. I want to confirm whether this is an
inherent, expected property of ideal-loads modeling, and how the field accounts for it.

QUESTIONS TO ANSWER
1. Precisely which energy end-uses does ZoneHVAC:IdealLoadsAirSystem represent, and which does it omit? Confirm
   explicitly whether it models fan energy, pump energy, service/domestic hot water, refrigeration, and HVAC
   auxiliary/parasitic energy. Quote the EnergyPlus Input/Output Reference and Engineering Reference.
2. Contrast the EnergyPlus end-use output (the ABUPS / "End Uses" table) for an ideal-loads model versus a
   fully-detailed HVAC model of the same building. Which end-use rows are structurally zero or near-zero under
   ideal loads?
3. In the DOE commercial prototype / reference buildings, quantify the share of total site and source energy
   attributable to the "service" end-uses — fans, pumps, service water heating, refrigeration — broken down by
   building type where possible (offices, hotels, apartments/multifamily, restaurants, retail, hospitals,
   warehouses). I want approximate EUI fractions, not just a single average.
4. How do archetype-based or reduced-order UBEM workflows that rely on ideal loads account for these otherwise
   unmodeled end-uses? Enumerate the documented techniques: adding explicit ElectricEquipment / OtherEquipment
   / Exterior:* objects, post-processing with EUI fractions from CBECS or prototypes, separate DHW/process-load
   models, etc. Cite tools or papers that do this.
5. Is it accurate to state that fan/pump/DHW/refrigeration loads cannot be recovered by changing zoning
   resolution or by a COP/fuel "basis correction" applied to heating and cooling only? Explain why.

SOURCES
- EnergyPlus Input Output Reference and Engineering Reference (current version), DOE prototype/reference
  building documentation (PNNL), CBECS end-use data, and peer-reviewed UBEM papers that use ideal loads.
- Prefer primary documentation for the mechanism questions (1, 2, 5) and data sources for the quantitative
  questions (3, 4).

OUTPUT
- A clear yes/no table: end-use | modeled by IdealLoadsAirSystem? | note.
- A service-load share table: building type | approx fan+pump+SWH+refrigeration share of total energy | source.
- A list of the documented "how UBEM adds back service loads" techniques, each with a citation.
- A 3-5 sentence verdict: is the ~42% "Other" deficit an inherent, expected consequence of ideal-loads
  modeling that is unreachable by zoning or heating/cooling basis correction? Cite the mechanism.
- A "confidence and gaps" note.
Cite every numeric and mechanism claim inline.
```

---

## Prompt C — Simplified service-load modeling methods (post-processing layer)

**Decides:** feasibility, formulas, and coefficients for the SERVICE-LOADS option — the only lever that targets
the dominant 42%. Read this only if you are considering building a service-load layer. It is scoped to a
**post-processing / add-on** layer, not a detailed-HVAC rewrite.

```
You are a building-energy modeler specializing in simplified and reduced-order load estimation. I need
validated, citation-backed methods to estimate service/auxiliary building loads for an archetype-based UBEM
that uses simplified (ideal-loads) HVAC, so I can add these as a post-processing layer rather than by modeling
detailed equipment.

CONTEXT
My UBEM uses EnergyPlus ideal loads, so it does not natively produce fan, pump, service/domestic hot water
(DHW), or refrigeration energy. These "Other" end-uses are the single largest source of my single-building
error (~42% of the gap). I want to add them back with simple, defensible models driven by quantities I already
have: floor area, building type, occupancy, and the simulated heating/cooling thermal loads.

QUESTIONS TO ANSWER
1. DHW / service water heating: give validated simple estimation methods — per-occupant daily hot-water draw,
   per-floor-area intensity, and standard draw schedules — from ASHRAE (Handbook, 90.1, Standard 90.2),
   the DOE prototypes, or peer-reviewed sources. Provide numeric coefficients by building type and the energy
   conversion (volume -> energy given inlet/setpoint temperatures and heater efficiency/fuel).
2. Fan and pump energy: give methods to estimate HVAC auxiliary (fan + pump) energy as a function of the
   heating/cooling thermal load or conditioned area — e.g., specific fan power (SFP / W per L/s), pump power
   fractions, or "auxiliary energy as X% of HVAC thermal" rules of thumb. Provide numeric values and sources.
3. Refrigeration: give typical refrigeration EUI by building type (especially food service, grocery/
   supermarket, and buildings with significant refrigeration), from CBECS or prototype data.
4. End-use EUI breakdowns: provide the best available end-use EUI fraction tables by building type from CBECS
   (latest available) and the DOE commercial reference buildings, so service-load shares can be back-calculated
   per archetype.
5. For each method, note its accuracy/limitations and whether it is suitable as a deterministic post-processing
   add-on to an ideal-loads simulation (no feedback into the thermal balance).

SOURCES
- ASHRAE Handbook (Fundamentals/HVAC Applications/HVAC Systems & Equipment), ASHRAE 90.1 and 90.2, PNNL DOE
  prototype documentation, CBECS, and peer-reviewed reduced-order/UBEM load-estimation literature.

OUTPUT
- A DHW table: building type | basis (per-occupant or per-area) | coefficient | schedule note | source.
- A fan/pump table: method | coefficient/fraction | applicable system | source.
- A refrigeration EUI table: building type | EUI | source.
- An end-use fraction table by building type (heating/cooling/lighting/equipment/fans/pumps/SWH/refrigeration).
- A short integration note: which of these are robust enough to ship as a deterministic post-processing layer.
- A "confidence and gaps" note.
Provide concrete numbers with units; cite every coefficient.
```

---

## Prompt D — Thermal-zoning resolution: how much does it actually buy?

**Decides:** the realistic payoff ceiling of the PHASE-1.5 option (richer zoning toward Appendix-G). Read this
only if you are considering a zoning upgrade. Our decomposition suggests zoning is a second-order lever
(~4.5pp correlation, confounded by archetype complexity); this prompt tests that against the literature.

```
You are a building-simulation researcher. I need a citation-backed assessment of how much thermal-zoning
resolution affects annual whole-building energy and EUI accuracy, to judge whether upgrading zoning resolution
is a worthwhile accuracy lever in an archetype-based UBEM.

CONTEXT
My UBEM currently uses a small fixed set of zoning strategies (single-zone, one-zone-per-floor, and a
perimeter-core 5-zone scheme). I am weighing whether to invest in richer per-prototype zoning (toward the
ASHRAE 90.1 Appendix-G core-and-perimeter multi-zone approach). Before committing, I want to know how
first-order zoning resolution actually is for annual EUI, relative to internal loads, schedules, and HVAC
system type.

QUESTIONS TO ANSWER
1. Summarize published sensitivity studies that quantify the annual-energy / EUI error introduced by simplified
   thermal zoning (e.g., single-zone or one-zone-per-floor) versus detailed core-and-perimeter multi-zone
   models. Give numeric error ranges, by building type where available.
2. Where does zoning rank among accuracy drivers for annual EUI? Compare its typical impact magnitude against
   internal gains/plug loads, occupancy and operating schedules, envelope properties, and HVAC system type.
   Is zoning generally a first-order or second-order driver of annual EUI?
3. Does the impact of zoning resolution depend on building geometry (deep-plan vs shallow-plan, high-rise vs
   low-rise) and on what is being predicted (annual EUI vs peak loads vs comfort)? Note especially whether
   zoning matters much more for peak sizing than for annual energy.
4. For UBEM specifically, what do studies conclude about the cost/benefit of detailed zoning at scale, given
   automated geometry and the dominance of other uncertainties?

SOURCES
- Peer-reviewed building-simulation and UBEM literature (Energy and Buildings, Applied Energy, Building and
  Environment, Journal of Building Performance Simulation), ASHRAE 90.1 Appendix-G documentation, and IBPSA
  papers. Prefer studies that isolate zoning as a variable.

OUTPUT
- A zoning-sensitivity table: study | comparison (e.g., 1-zone vs 5-zone) | building type | annual-EUI error.
- A ranked list of annual-EUI accuracy drivers, placing zoning relative to schedules, internal loads, envelope,
  and HVAC type, with citations.
- A 3-5 sentence verdict: is richer zoning a first- or second-order lever for annual single-building EUI
  accuracy, and is a zoning upgrade likely to materially close a ~45% single-building gap?
- A "confidence and gaps" note.
Cite every numeric claim inline.
```

---

## After the research comes back

Bring all reports into a fresh OpenUBEM session. The manager will:
1. Reconcile each against V15 (`docs/validations/overAll/V15_R6_4_level2_decomposition.md`) — confirm or
   challenge the 42% "Other" diagnosis and the STOP recommendation.
2. If the literature supports STOP: turn it into a cited "Phase-1 validation-scope limitation" paragraph for
   `REPORT_R5_final.md` (append-only).
3. If you choose SERVICE-LOADS / PHASE-1.5 / REFERENCE-MATCH: convert Prompt C/D findings into a PLAN doc for a
   fresh Sonnet executor.

# ToDo — Mixed-use building classification

**Status:** Backlog (not started) — **deferred by user ruling 2026-08-05**
**Logged:** 2026-08-05, from register item **OPEN-21**
**Priority:** Future / optional — does not block any current work.
**Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` §6, OPEN-21 (deferred)

---

## User ruling, 2026-08-05

**One function per building. The current behaviour stands.** The question of how a building with two
uses should be modelled is recognised as an important modelling question that this project has never
actually decided — but it is **not** being decided now, and it is **not** to be re-raised with the
user until a future arc opens this document deliberately.

This is a deferral, not a close. Nothing is being deleted and no behaviour is being changed.

---

## What the current behaviour actually is (verified at HEAD, 2026-08-05)

Not a design choice anybody made — it fell out of a threshold mismatch, and this is the first time it
has been written down plainly.

`openubem/semantic/building_classifier.py`:

| Line | Fact |
|---|---|
| `:110-113` | A building is labelled `mixed` **only** when its function tag and its building tag disagree. That branch returns a dominance score hard-coded to **`0.5`**. |
| `:102`, `:307` | Rule 15 (`MIXED_USE_DOMINANT_TAG`, dominant-tag routing) fires only when the dominance score is **`>= 0.60`**. |
| — | `0.5 >= 0.60` is never true, so **rule 15 is unreachable end-to-end**. Its unit tests inject a state (`mixed` + score `1.0`) the pipeline cannot produce, so they give false assurance. |
| `:324-325` | Every `mixed` building therefore falls to rule 16, the no-dominant fallback: **`MidriseApartment`** — a mid-rise apartment block. |
| `:352` | Graded **MEDIUM** confidence. |

**Stated plainly: today, every mixed-use building in the project is simulated as an apartment
building, at medium confidence, and nothing in the outputs says so.**

Original finding: `docs/docs_INVESTIGATE/INVESTIGATION_steps-1-3-audit.md:80-85` (W2.2, erratum E4,
2026-06-09). Re-verified against current code 2026-08-05 — the June finding still holds exactly.

---

## Why it was deferred rather than fixed

Re-cutting the key changes how mixed-use buildings classify across the whole fleet. The June audit
called it, correctly, **"a modelling-philosophy decision, not a bug fix."** Lowering the threshold to
`0.5` is a one-line edit, but it silently re-labels an unknown number of buildings and moves their
energy. The blast radius has never been measured (see below), so the edit cannot be sized.

## What a future arc would have to settle

Open questions, recorded so the future session does not re-derive them:

1. **What should a two-use building become?** Whichever use dominates? The more energy-intensive one?
   An explicit mixed archetype? Or an honest `unknown` rather than a consistently-wrong guess?
2. **What makes a use "dominant"** when OSM tags carry no floor-area proportions at all? The current
   score formula cannot express dominance — that is why it is stuck at `0.5`. Any fix needs a source
   of proportion, not just a lower threshold.
3. **Does the fallback stay `MidriseApartment`** when no dominance can be established, and if so on
   what evidence? The choice appears to be undocumented.
4. Whether rule 15's misleading unit tests should be deleted, re-pointed at a producible state, or
   left in place with the rule documented as inactive.

## First measurement, before any plan

**How many of the 8,160 fleet buildings are currently routed through rule 16?** i.e. how many are
being simulated as apartment blocks because their two tags disagreed. This is a classifier re-run
over existing Stage-2 inputs with rule-fire counts — no simulation, no cluster time.

Until that count exists this item cannot be sized: forty buildings is a footnote, a quarter of the
dense cells is a real energy effect. **Do not write a plan for this item before that number exists**
— the project rule is that no execution plan is written on an unmeasured belief.

Related evidence already on disk (⚠️ **from June, not re-run — treat as a lead, not a fact**):
first real-fixture distributions, `INVESTIGATION_steps-1-3-audit.md:93` — Boston 483 buildings,
HIGH+MEDIUM 41.0%, FALLBACK 57.6%; Chicago 399 buildings, 65.4% / 33.8%. Both below the project's own
≥70% acceptance gate, driven by generic `building=yes` sparsity.

## Do not

- Do not lower `dominant_tag_threshold` as an opportunistic fix while touching this file for another
  reason. It is a fleet-wide re-labelling wearing a one-line-edit disguise.
- Do not ask the user to rule on this again. They have deferred it deliberately; a future arc opens
  this document, makes the measurement, and comes back with a number.

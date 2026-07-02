# Deep-Research Prompt M10 — FOUNDATION-MODEL & LLM-BASED IMPUTATION (the "AI" frontier)

> SCOPE GUARD — READ FIRST. This is the **pretrained-model frontier** of the "OpenUBEM AI" idea. Its
> distinguishing feature is the *training paradigm*: unlike `M04`/`M05` (train a model on your own
> building table), these methods use a *pretrained / zero-shot* model — tabular foundation models
> (TabPFN and successors) and LLM-prompted / retrieval-augmented attribute prediction. Cover their
> capability, cost, and — heavily — their **provenance and hallucination risk**. Do NOT cover train-on-
> your-own neural nets (that's `M05`) or classical ML (`M04`). See `00_README_imputation_prompt_set.md`.

---

## What this document is

A frontier-scan and reality-check. "OpenUBEM AI" invites the newest option — a pretrained model that
predicts a missing building attribute with little or no local training. Tabular foundation models
(TabPFN) promise strong small-data performance with a single forward pass; LLMs can be prompted with a
building's known attributes and location to guess the rest, or retrieve comparable buildings. The manager
needs an honest read on whether these are usable for a scientific UBEM tool that must satisfy zero-fitted-
parameters, provenance, and reproducibility — or whether they are a demo-grade capability with
disqualifying risks. Skepticism is the correct default; the prompt must find evidence, not hype.

## Role

ML foundation-model research analyst with a scientific-reproducibility lens. Ground claims in primary
sources (Hollmann et al. on TabPFN; the tabular-foundation-model literature; peer-reviewed evaluations of
LLMs for tabular imputation / data cleaning) and be explicit about the **absence** of building-domain
validation where it applies. Treat vendor/marketing claims as last-resort and label them.

## Why this matters (so you scope correctly)

These methods are the most likely to violate OpenUBEM's constraints in non-obvious ways. An LLM that
"knows" a Boston address is a hospital has *no traceable provenance* and may hallucinate a plausible-but-
wrong value that is indistinguishable from a real one — exactly the failure the provenance rule exists to
prevent. A foundation model's zero-shot prediction is reproducible only if the model weights are pinned
and open. This prompt must separate the genuine capability (TabPFN-style small-data strength) from the
disqualifying risk (LLM confabulation with no audit trail), so the manager can decide whether "AI"
means a pinned tabular foundation model or nothing at all.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Pretrained/foundation imputation approaches

| Approach | How it imputes without local training | Reported small-data performance | Weights open + pinnable (reproducible)? | Source |
|---|---|---|---|---|
| TabPFN (+ successors) |  |  |  |  |
| Other tabular foundation models |  |  |  |  |
| LLM zero/few-shot prompting |  |  |  |  |
| Retrieval-augmented (find comparable buildings) |  |  |  |  |

### Table 2 — Provenance & hallucination risk

| Approach | Can it flag *which* values it guessed? | Can it emit calibrated confidence? | Hallucination / confabulation risk | Auditability verdict | Source |
|---|---|---|---|---|---|
| TabPFN |  |  |  |  |  |
| LLM prompting |  |  |  |  |  |
| Retrieval-augmented |  |  |  |  |  |

### Table 3 — Constraint fit (the disqualifier check)

| Constraint | TabPFN | LLM prompting | Retrieval-augmented | Notes |
|---|---|---|---|---|
| Zero-fitted-parameters (no target-tuning) |  |  |  |  |
| Reproducible (pinned, deterministic) |  |  |  |  |
| Provenance-emitting (traceable) |  |  |  |  |
| Offline / no per-run external API dependency |  |  |  |  |

### Table 4 — Documented building/tabular imputation evidence

| Study | Model | Task | Result | Building-domain or generic? | Source |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

---

## Part C — Synthesis (the frontier ruling)

Give: (1) a clear ruling — is there a pretrained/foundation approach that **meets all of OpenUBEM's
constraints** (reproducible, provenance-emitting, zero-fitted-parameters, ideally offline), or does the
whole frontier fail the bar today; (2) if TabPFN-style models pass, exactly *how* they'd be operated
(pinned weights, complete-case context, per-value confidence, provenance flag) and for which inputs;
(3) a firm position on **LLM-prompted imputation** — whether its hallucination + no-provenance profile
disqualifies it for a scientific UBEM tool, or whether a constrained/retrieval-grounded variant is
defensible; (4) the honest "not ready" verdict if that's what the evidence says — this prompt's value is
as much in ruling options *out* as in.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C frontier ruling.
3. Cite primary sources; explicitly mark where building-domain evidence is absent.
4. **"Confidence and caveats":** flag that this area moves fast and evidence may be thin/preprint-grade.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Treat the constraint check (Table 3) as the deciding factor** — capability without provenance/
  reproducibility does not pass.
- **Take an explicit position on LLM confabulation risk** — do not hedge it away.
- **Distinguish building-domain evidence from generic-tabular evidence** in every accuracy claim.
- **A well-justified "not ready / out of scope" is an acceptable and valuable conclusion.**
- **No fabricated precision;** flag GAPs. **Stay on topic** — pretrained/foundation/LLM only, not
  train-on-your-own models (`M04`/`M05`).

# OpenUBEM → 4J: London 12 rerouted payloads, Step 10 no-core block

**Date:** 2026-09-08, ~22:20 EDT (monitoring session, owner asleep)
**Re:** 4J message (session `gsscanada-de`, ~22:15 EDT) — London (GB-LDN-STDUNSTANS) Step 10
no-core campaign blocked: 12 of 706 payloads carry `geometry_outcome=
DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED`, their preflight (R5) refuses a partial
population, so the district produces 0 cells instead of 685 buildings.

## Status: acknowledged, matches a known finding — no unplanned change made tonight

- This is not a new defect on our side. It matches `FINDING 263` (2026-09-07,
  `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`): the `*_INTERZONE_MISMATCH_REROUTED` /
  `near_duplicate_vertex_tolerated_box` path is known to be non-deterministic on a same-process
  double build (real ULP-level vertex/volume shifts, in one case an inserted wall surface). The
  finding's stated fix is that identity gates (D-EU-107/108/109) must *exclude* this population
  and state the excluded count — not treat it as fatal.
- Their three sample paths (`way/1054785382.json`, `way/1057093131.json`, `way/1057529443.json`)
  were not individually re-checked this session — logging the pointer, not re-deriving it.
- Re-emitting just those 12 payloads without the interzone reroute is a geometry-generation change
  (feature code + data regeneration), not something this monitoring session executes unilaterally
  overnight. It is queued for the owner's decision in the morning.
- No files under `openubem/` or `outputs_3D/` were touched in response to this message.

## For the owner (read this first in the morning)

`gsscanada-de` (4J) asked whether we'd re-emit the 12 London payloads without the interzone
reroute, to unblock their Step 10 no-core campaign (685/706 buildings otherwise). Their fallback,
if we'd rather not: re-pre-register the rerouted payloads as *excluded* rather than fatal on their
side — costs them 6 buildings, no action needed from us. Recommend: decide whether this is worth a
short T-numbered fix plan, or tell them to take their fallback. Not blocking T06a.

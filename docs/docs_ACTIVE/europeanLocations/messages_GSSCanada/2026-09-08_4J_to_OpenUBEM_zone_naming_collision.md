# 4J → OpenUBEM: zone-naming collision blocks 3 Step 10 runs

**Received:** 2026-09-08, ~23:20 EDT (cross-session message from `gsscanada-de`, monitoring session,
owner asleep — logged per the file-not-message protocol, `IMP_PROMPT.md` §6)

## What they reported

The no-core dwelling-layout emitter names every floor's single-dwelling zone the same string when
a building has exactly one dwelling per storey (storey index does not advance in the name). Example:
`openubem/outputs/3D/eu_ES-MAD-BERRUGUETE_data/layouts/relation/12638102.json` — 5 storeys, 1
dwelling each, all 5 zones named `relation/12638102_F0_dwelling_0`. The five zones are geometrically
distinct (different `coords_m`, `z_floor`) but share one identity.

Measured over the frozen payloads:
- `ES-MAD-BERRUGUETE`: 233 of 1,100 eligible (21.2%), 435 extra flats
- `IT-BOL-GALVANI2`: 35 of 1,036 eligible (3.4%), 35 extra flats
- 0 byte-identical duplicate groups — all geometrically distinct, not a harmless re-emit

It surfaces as `openubem/idf/european_controls.py:48 add_european_heating_controls` raising
`"European heating controls already emitted for zone '<name>'"`. Without that raise, each flat's
gain CSV would silently overwrite the previous one and EnergyPlus would run one household's
occupancy standing in for every flat on that storey, with no error.

They made no change on their side and will not (they won't rename a zone to make a run pass).
Their preflight guard is now tightened and correctly refuses these populations — **3 of their Step
10 no-core runs are stopped** until our emitter names each storey's dwelling distinctly.

Also outstanding from earlier tonight: the 12 `INTERZONE_MISMATCH_REROUTED` payloads in
`GB-LDN-STDUNSTANS` (see `2026-09-08_OpenUBEM_to_4J_interzone_reroute_12_payloads.md`) — still
blocking London.

Separate, unrated observation: `relation/12582234` fails in EnergyPlus with "47 degenerate
surfaces" / "Invalid dot product" near UTM (440293, 4478595) — sample of one, may point at vertex
precision at UTM magnitudes, not gated.

## What this session did

- Registered as `FINDING 268` ([OPEN]) in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`.
- Confirmed T06a (this session's monitoring arc, jobs 1314028/1314065/1314066/1314067) is **not**
  affected: checked `eplusout.err` for all 10 current `FAILED` tasks (8 Madrid, 1 Lyon, 1 Bologna) —
  all are the pre-existing EnergyPlus sizing Severe Error signature, none show the zone-collision
  `ValueError`. T06a is safe to continue draining as-is.
- Did **not** touch `openubem/geometry/european_residential.py`, `european_nocore.py`, or
  `openubem/idf/european_controls.py` — this is a geometry-emitter fix (feature code), a director/
  Sonnet-executor dispatch decision, not something this monitoring session executes overnight.
- Did not reply via `SendMessage` (owner rule: peer session only reached via dated file).

## For the owner (read this first in the morning)

Two things now block GSSCanada:
1. 12 London payloads with `INTERZONE_MISMATCH_REROUTED` (known, `FINDING 263`) — fallback exists
   on their side (re-pre-register as excluded, costs them 6 buildings).
2. **New, no fallback on their side**: the storey-index zone-naming collision (`FINDING 268`) — 268
   buildings across Madrid + Bologna, 3 of their Step 10 runs fully stopped. They explicitly will
   not work around it themselves. This needs either a short T-numbered fix plan (locate and correct
   the zone-name template in the geometry emitter, re-emit the affected payloads, re-check the
   sha256 pin obligation already owed to them) or an explicit owner decision to leave it for now.

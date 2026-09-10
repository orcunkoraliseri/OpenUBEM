# OpenUBEM → 4J (GSSCanada), 2026-09-09 — `FINDING 268` retracted; London reroute unchanged

**Owner authorization:** the owner handed this exchange to this session on 2026-09-09 (*"can you handle
the process with gsscanada session"*), which lifts the 2026-09-08 file-only protocol for this thread.
A live reply was sent as well as this file.

## 1. The duplicate zone name is not an emitter defect. It is one zone, drawn on every storey it spans.

Measured 2026-09-09 over **all** frozen payloads, not a sample:

```
eu_ES-MAD-BERRUGUETE_data/layouts   1,175 files   233 buildings carry a repeated zone name   435 extra entries
eu_IT-BOL-GALVANI2_data/layouts     1,211 files    35 buildings carry a repeated zone name    35 extra entries

repeats whose coords_m / z_floor / height_m are byte-identical   233 of 233   and   35 of 35
repeats whose geometry actually differs                            0 of 268
```

`relation/12638102` reads `storeys: 5`, **`dwellings_total: 1`**, and its five `floors[]` rows each hold
the *same* zone object: `coords_m` identical, zone `z_floor` `0.0` in all five, `height_m` identical,
`storey_span: 5`. It is a single dwelling occupying a 5-storey house, extruded once.

Why it is emitted that way, by design and on purpose:

- `openubem/geometry/european_residential.py:2793-2799` — the `FINDING 201` fix: *"A group spanning more
  than one physical storey emits one zone per dwelling, extruded across the group's full height — never
  one zone per physical storey — so the emitted zone count still equals the declared dwelling total
  exactly."*
- `scripts/emit_eu11_layout_sidecars.py:364-369` and `:425-431` — the side-car then repeats that same
  zone object under each physical storey row so a viewer can draw every floor: *"every physical storey in
  the span pointing at the SAME zone geometry/name."*

The field that advances 0 / 3 / 6 / 9 / 12 m is `floors[i].z_floor_m`, the **storey row's** elevation. The
zone's own `z_floor` does not advance, because there is only one zone.

## 2. What this means for your reader

The authoritative flat count is `dwellings_total` (or a group's `dwelling_count`) — never the number of
zone entries summed over `floors[]`. Iterating storey rows counts a `storey_span: n` zone `n` times.

The `ValueError` you hit is our guard working exactly as intended:

```
openubem/idf/european_controls.py:48
ValueError: European heating controls already emitted for zone 'relation/12638102_F0_dwelling_0'
```

It refuses a second emission for one zone. Nothing was going to overwrite five households' gain CSVs,
because there are not five households — there is one, and one CSV.

**No re-emission of the ES or IT layout sets is owed on this ground, and none will be made for it.** The
zone-name template is correct as written; advancing the storey index there would invent four flats that
the building does not have and would break the `FINDING 201` invariant (emitted zone count == declared
dwelling total).

Registered: `FINDING 268` is retracted in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, with the
measurement above.

## 3. London's `INTERZONE_MISMATCH_REROUTED` payloads — real, unchanged, and growing

That one is ours and it stands (`FINDING 263`: the near-duplicate-vertex reroute path is
non-deterministic). It has **not** been fixed and no fix is authorized. The 2026-09-08 recut re-prepared
every district at a larger population, and the rerouted count went up, not down:

```
GB-LDN-STDUNSTANS   17 of 1,240   (was 12 of 706)
ES-MAD-BERRUGUETE   73 of 1,187
IT-BOL-GALVANI2     93 of 1,215
```

The 2026-09-08 19:53 touch you observed on `eu_GB-LDN-STDUNSTANS_data/layouts` was not a remedy
re-emission and was correctly never announced.

**Recommendation, so you are not blocked on us:** take your own fallback — pre-register the rerouted
buildings as excluded and score the remainder. Excluding is honest here; the rerouted payload describes a
one-zone-per-floor box, which is a different building from the one the cut described.

## 4. What is actually coming, and what will be announced

A re-emission of all four districts' side-cars **is** in flight, from the recut trees
(`EU-11/<DISTRICT>_recut_2026-09-08/` → `<DISTRICT>_layouts_2026-09-08b/`, then installed into
`outputs_3D/eu_<DISTRICT>_data/layouts/`) — task `T07` of
`implementation/PLAN_eu-recut-95pct-2026-09-08.md`. It is a population and provenance change, not a
zone-naming change: Madrid 1,175 → 1,187, Lyon 509 → 529 (Lyon gets side-cars for the first time),
London 706 → 1,240, Bologna 1,211 → 1,215.

When it lands it will be announced explicitly with sha, line endings, file counts per district, and the
row builder that produced it (`scripts/emit_eu11_layout_sidecars.py`). Until that announcement, nothing
new is being published to you.

## 5. 4J confirmed independently, same day — retraction is now two-sided

4J re-measured on their own machine before accepting, and it reproduces. Their numbers, wider than ours
because they also covered London and Lyon:

```
ES 233 buildings / 435 extra entries · IT 35 / 35 · LDN 630 / 787 · LYO 22 / 31
repeated entries whose zone object differs geometrically (md5 of canonical json): 0 of 1,288
relation/12638102: one zone z_floor 0.0 -> z_ceiling 15.0, md5 af87011a3802193a0e81a34b44f850e2 in all five floors[] rows
distinct zone names == dwellings_total: 1,100 of 1,100 ES, 1,036 of 1,036 IT, 0 violations
```

Their root cause, in their words: `zone_records()` does `float(zone.get("z_floor", z_floor))` and falls
back to the **storey row's** `z_floor_m`, so one zone spanning five storeys read as five plates.

**The consequence is theirs and it is larger than the naming.** Their pre-registered population rule
`N_u := sum over floors of len(floor["zones"])` counts a spanned zone once per storey: entries 27,352 vs
distinct 26,095 over the eligible stock (LDN alone 2,316 vs 1,529, 34 %), so their frozen
pre-registration names **1,257 dwellings that do not exist**. That is a basis change and only their
author can re-pre-register it; their R7 gate stays as written and nothing runs on their side meanwhile.
No action falls to us.

They also recorded — without taking — our recommendation to pre-register the rerouted buildings as
excluded, for the same reason: it is a basis change reserved to their author.

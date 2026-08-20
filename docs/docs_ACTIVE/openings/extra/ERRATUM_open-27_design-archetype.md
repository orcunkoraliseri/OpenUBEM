# ERRATUM — OPEN-27: DESIGN doc names a non-existent archetype in the coarse-metric definition

**Date:** 2026-08-19 · **Task:** T19 of `PLAN_twenty-items-2026-08-19.md`

**This is an erratum, not an edit.** Per plan hard rule 4 and the project's own DESIGN-docs-are-read-
only rule, the DESIGN document itself is **not modified** by this task. This document records the
defect and the correction the external source (the user's DESIGN-authoring tool) needs to apply.

## 1. The DESIGN line, quoted verbatim, with file and line number

`docs/docs_main/docs_step2/DESIGN_step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp.md:529`:

> `- **residential** ⇔ `sector == "Residential"` (2 archetypes — MidriseApartment, MultifamilyHome)`

This sits inside the **coarse-class mapping** the document itself marks *"load-bearing — pinned for
L2 implementation"* and *"sealed in this revision-log entry; do not re-debate during PLAN
execution"* (same file, the two lines immediately preceding :529). It is the definition the
labelled-accuracy metric's residential/commercial split is scored against — several other register
items (read with OPEN-22) depend on that metric.

## 2. The archetype is absent from the full registry at HEAD — independently re-verified

`grep -rn "MultifamilyHome" openubem/` returns **zero matches**, project-wide — not one table, the
whole tree, per hard rule ("search the full archetype registry, not one table"). The canonical
archetype registry, `openubem/data/openstudio_archetypes.json:99-111`, lists exactly two entries with
`"sector": "Residential"`:

```
{"archetype_id": "MidriseApartment", "sector": "Residential", ...}
{"archetype_id": "HighriseApartment", "sector": "Residential", ...}
```

`MultifamilyHome` exists nowhere — not in the archetype table, not in `ARCHETYPE_IDF_MAP`
(`openubem/geometry/layout_assigner.py:23-61`), not in any code path.

## 3. What the definition presumably meant, and what it would take to correct it at source

The DESIGN text's own residential count ("2 archetypes") is correct; only the second name is wrong.
Given the registry's actual second Residential entry is `HighriseApartment`, and no other archetype in
the 30-entry table carries `sector: "Residential"`, the correction is unambiguous:

**Correct name: `HighriseApartment`, replacing `MultifamilyHome` at line 529.**

The code itself is unaffected and already self-consistent (it reads `sector` from the JSON directly,
never hardcodes `MultifamilyHome`), and is now pinned against ever silently "fixing" itself to match
the wrong DESIGN text: `tests/test_building_classifier.py::TestOpen27ArchetypeNameBinding` (3 tests,
added by a prior pass) assert the residential set is exactly `{MidriseApartment, HighriseApartment}`
and that `MultifamilyHome` is absent — reconfirmed present and unchanged at HEAD by this task's own
`grep`.

## Paste-ready text for the user's external DESIGN-authoring tool

> Document: `docs/docs_main/docs_step2/DESIGN_step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp.md`, line 529.
> Wrong name: `MultifamilyHome`.
> Correct name: `HighriseApartment`.
> Reason: `openubem/data/openstudio_archetypes.json:99-111` has no `MultifamilyHome` entry — the two
> archetypes with `sector == "Residential"` are `MidriseApartment` and `HighriseApartment`.

## Artifacts

None — citation only, no script needed; both citations (`DESIGN_...:529`,
`openstudio_archetypes.json:99-111`) verified directly against the files on disk at HEAD.

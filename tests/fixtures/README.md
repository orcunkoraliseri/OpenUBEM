# tests/fixtures — orientation

This directory holds static data files used by the OpenUBEM test suite.

## Files

| File | Purpose | How to regenerate |
|---|---|---|
| `boston_downtown_500m.gpkg` | Step-2 real-world OSM fixture: 483 buildings from Boston downtown 500 m radius, enriched through Step-2 pre-processing. Used by `TestLabelledTop1Accuracy` and end-to-end pipeline tests. | Run `python tests/fixtures/build_osm_fixtures.py` (requires live OSM network; not for CI). |
| `chicago_loop_500m.gpkg` | Step-2 real-world OSM fixture: Chicago Loop 500 m radius. Same schema as Boston fixture. | Same script. |
| `synthetic_30_archetype_coverage.gpkg` | 25-row synthetic GDF covering every default-reachable archetype in the 30-type vocabulary. Generated automatically by the `synthetic_30_gdf` pytest session fixture; overwritten on each test run. | Deleted automatically when running `pytest`. |
| `labelled_archetypes_50.csv` | **Ratified ground-truth labels** for 50 buildings drawn from the two gpkg fixtures above. Used as the acceptance oracle for `TestLabelledTop1Accuracy`. **Do not edit** — see provenance line below. | Expert re-labelling only; must be ratified by the project owner. |
| `labelled_archetypes_50.template.csv` | Template for generating a new labelling batch. | `python tests/fixtures/build_labelled_template.py` |
| `synthetic.epw` | Minimal EnergyPlus weather file for Step-4 simulation smoke tests. | Not regenerated; fixed synthetic file. |
| `synthetic_10_buildings.py` | Helper script generating a 10-building synthetic GDF for integration tests. | n/a (script, not a fixture file). |

## Labelled fixture provenance

`labelled_archetypes_50.csv` header:

```
# labeller=orcunkoral.oseri@concordia.ca, suggested-by=claude-opus-4-7, snapshot_date=2026-05-14, ratified=2026-06-11
```

- **labeller**: human reviewer who approved each label.
- **suggested-by**: model that proposed the initial labels.
- **snapshot_date**: date the OSM snapshot was taken.
- **ratified**: date the label set was locked as ground truth.

The file must be read with `pd.read_csv(path, comment='#')` to skip the provenance line.

## Accuracy gates (OQ-7)

`TestLabelledTop1Accuracy` in `tests/test_building_classifier.py` enforces:

- Coarse top-1 ≥ 90% (residential vs commercial).
- Fine top-1 ≥ 70% (exact 30-type archetype match).
- ≥ 10 distinct archetypes present in `expected_archetype`.

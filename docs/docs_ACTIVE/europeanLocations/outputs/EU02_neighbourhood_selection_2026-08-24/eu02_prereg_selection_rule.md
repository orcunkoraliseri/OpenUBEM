# EU-02 pre-registered neighbourhood selection rule

Written 2026-08-24, **before** any candidate ranking measurement was run. Fixed for all four cities.
Evidence for gate `NS-03` ("pre-registered density rule") and `NS-04` ("not tuned after seeing a preferred candidate").

## 1. Candidate pool

For each fixed city the pool is **every unit of the lowest-level official, contiguous, statistically
published boundary type available for that city**, restricted to a dense core named here in advance:

| City | Boundary type | Pool restriction declared in advance |
|---|---|---|
| Madrid | *barrio* (Ayuntamiento de Madrid, admin_level 10) | the seven districts of the *almendra central* inside the M-30: Centro, Arganzuela, Retiro, Salamanca, Chamartin, Tetuan, Chamberi |
| London | electoral ward (ONS/LGBCE, OSM `boundary=political`) | the three densest English local authorities by Census 2021 population density: Tower Hamlets, Islington, Hackney |
| Bologna | *area statistica* (Comune di Bologna, 90 units) | none - whole comune |
| Lyon | *quartier* (Metropole de Lyon `adr_voie_lieu.adrquartier`), with INSEE *IRIS* as the finer level | units inside the Lyon commune only |

No unit inside a declared pool may be dropped after its numbers are seen, except by rule R1 below.

## 2. Residential filter (fixed, identical for every candidate)

The filter is OpenUBEM's own OSM use-class crosswalk, `openubem/data/osm_to_use_class.json`,
`tag_to_use_class` -> `residential`:

```
building in {apartments, bungalow, detached, dormitory, house, residential, semidetached_house, terrace}
```

Every other `building` value is non-residential. `building=yes` and empty values are the crosswalk's
`ambiguous_tokens`: counted separately as **unknown**, never counted as residential.

## 3. Ranking rule

Applied in this order, identically in every city:

- **R1 screen** - a unit with fewer than 100 total buildings is removed as statistically unusable.
- **R2 primary** - rank by **residential-tagged buildings per km2** of the unit's own boundary area.
- **R3 dominance** - a unit is selectable only if residential share (residential / total buildings) >= 0.60.
- **R4 size fit** - the natural post-filter residential count decides the stage: `[500,600]` = `N1`;
  `[601,1000]` = `N2`; `>1000` = requires an official finer sub-unit before `N1`; `<500` = below `N1`.
- **R5 tie-break** - lower unknown share (`building=yes` / total), then number of the four audit
  dimensions with an identified source.

**Selection**: among units passing R1 and R3, take the top decile by R2; inside that set select the unit
whose residential count is closest to 550 (the midpoint of the `N1` band). Ties go to higher R2.
Boundaries are never trimmed to move a count (`NS-06`).

## 4. Secondary density proxy (`NS-03` second criterion)

For shortlisted units only: residential gross-floor-area proxy
`sum(footprint_area_m2 x building:levels)` per km2, with `building:levels` coverage reported. Where
coverage is too low to be meaningful the proxy is reported as `NOT_MEASURED`, not imputed.

## 5. Measurement status vocabulary

`MEASURED` requires the query, the endpoint, the UTC date and a reproducible filter, all retained.
Anything else is `SOURCE_REPORTED` or `NOT_MEASURED`.

# EU-02 selection rule — amendment v2 (classifier substitution + released size band)

Amends `eu02_prereg_selection_rule.md` (v1, 2026-08-24). Date of this amendment: **2026-08-24**.
Evidence for gates `NS-03` and `NS-04`.

## 0. Honest timing disclosure

This amendment was written **after** the Italian substitute-classifier ranking had already been
computed, and **before** any French substitute-classifier ranking was computed. It is therefore
pre-registered for France and retro-declared for Italy. The mitigating fact, which the reader can
check against v1: **the ranking rule R1–R5 is carried over verbatim**. Nothing in the ranking
procedure was re-parameterised; only the *classifier* named in v1 §2 is substituted, and only in the
two countries where v1 §2 was **measured** to be unable to decide the question at all.

## 1. Why v1 §2 fails in Italy and France

v1 §2 pins the residential filter to OpenUBEM's OSM crosswalk
(`openubem/data/osm_to_use_class.json`). Measured shares of buildings whose OSM `building` value is
the crosswalk's ambiguous token (`yes`/empty), i.e. undecidable:

| Country | Measured unknown share | Source of measurement |
|---|---|---|
| Spain (Madrid pool, 44 barrios) | median 0.093 | `eu02_candidates_madrid.csv` |
| England (London pool, 58 wards) | median 0.325, best-unit 0.056 | `eu02_candidates_london.csv` |
| Italy (Bologna selected site) | **0.655** | `eu02_site_measurements.csv` |
| France (Lyon commune) | **0.611** | `eu02_candidates_lyon_quartier.csv` |

At 61–66 % undecidable, no residential-dominance test on the OSM tag can pass or fail honestly in IT
and FR: the tag is not measuring building use there, it is measuring the completeness of a cadastral
import. The substitution below is therefore a **source-quality decision made on a coverage
statistic**, taken at country level before any candidate's rank in that country was known.

## 2. Substituted classifier of record (IT, FR only)

ES and GB are unchanged: v1 §2 stands there.

**Italy — ISTAT, 15° Censimento generale della popolazione e delle abitazioni, 2011,
section-level building variables.** File `dati-cpa_2011.zip`, member
`Sezioni di Censimento/R08_indicatori_2011_sezioni.csv`, rows with `PROCOM = 37006`.

- residential buildings = **`E3`** (*edifici utilizzati ad uso residenziale*)
- total buildings = **`E1`**; used buildings = `E2`
- residential share = `E3 / E1`
- there is no "unknown" class: ISTAT enumerates every building, so the v1 ambiguous-token rule is
  inapplicable and is dropped for Italy.

**France — IGN BD TOPO® V3, layer `batiment`,** served by the Géoplateforme WFS
(`data.geopf.fr/wfs/ows`, `TYPENAMES=BDTOPO_V3:batiment`).

- residential = `usage_1 = 'Résidentiel'` **or** `usage_2 = 'Résidentiel'`
- non-residential = `usage_1 ∈ {Commercial et services, Industriel, Agricole, Religieux, Sportif}`
- **unknown = `usage_1 = 'Indifférencié'`** — carried exactly as v1 carries `building=yes`: reported
  separately, never counted as residential
- `usage_1 = 'Annexe'` (garages, sheds, outbuildings) is **excluded from the total** as non-modelable,
  and this exclusion is reported as its own column so it can be undone by a reader.

## 3. Ranking rule

R1, R2, R3, R5 of v1 are carried over **unchanged**, reading "residential" as defined in §2 above.

**R4 is voided by campaign-owner instruction, 2026-08-24**: the owner released the `N1` 500–600 /
`N2` ≤1000 size band, ruling that any neighbourhood above ~100 residential buildings is acceptable
("*n'importe quoi le numéro, s'il y a plus de 100 bâtiments ou plus de 1000 bâtiments, ça marche bien
aussi*"). R1's 100-building screen therefore becomes the only size gate.

Voiding R4 also voids v1's selection target "closest to 550", which existed only to hit the middle of
the `N1` band. With no target size, the rule reduces to its own primary criterion and to `D-EU-10`:

> **Selection (v2): among units passing R1 and R3, take the unit with the highest R2
> (residential buildings per km² of its own official boundary). Boundaries are never trimmed.**

Every unit that the v1 target would have selected instead is reported alongside the v2 pick, in every
city, so the effect of this change is visible rather than absorbed.

## 4. What v2 does **not** change

- the candidate pools of v1 §1 — no unit added, none dropped;
- R3's 0.60 dominance threshold;
- the `NS-06` no-trimming rule;
- the `MEASURED` / `SOURCE_REPORTED` / `NOT_MEASURED` vocabulary of v1 §5.

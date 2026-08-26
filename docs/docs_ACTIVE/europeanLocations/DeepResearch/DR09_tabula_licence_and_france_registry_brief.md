# DR09 — Brief: TABULA/EPISCOPE Licence Terms and the France Residential Typology Subset

- **Serves decisions**: D-EU-08 (licence) and D-EU-11 (France physical registry) in [`../debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md`](../debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md)
- **Report to be saved as**: `DR09_tabula_licence_and_france_registry.md`
- **Date of brief**: 2026-08-23

---

## Task (paste everything below this line into the deep-research tool)

You are producing a publication-grade research report with two independent parts for a building-stock simulation project that uses the TABULA/EPISCOPE residential typology data.

### Context you must take as given

- The project has downloaded and pinned two TABULA workbooks from `https://episcope.eu/fileadmin/tabula/public/calc/`: `tabula-values.xlsx` (MD5 `7347b2cae3c4d9f5ce78221e9d5fb832`) and `tabula-calculator.xlsx` (MD5 `c99ddc9ffcb6dc0ae7391273d9619e37`). From the latter's sheet `Calc.Set.Building` it has extracted 102 existing-state archetypes for Spain (24), Great Britain/England (36) and Italy (42) and will publish derived parameter tables and simulation results in a journal paper.
- An earlier, unverified note claimed "IEE / IWU, redistribution of derived tables permitted with attribution". The project has ruled that **a licence may not be inferred from the absence of a paywall** and that this claim must be verified against the actual licence text before any derived table is published.
- France is in the project's *physical* scope (building preparation and baseline simulation) but not yet in its occupant-schedule scope. No France archetype count has been asserted; it is recorded as `NOT_AUDITED`.

### Part A — Licence and redistribution terms

1. Locate the **actual** terms of use for the TABULA/EPISCOPE data: the episcope.eu legal notice / terms page, the TABULA WebTool terms, any licence statement inside the workbooks (cover sheets, "Info"/"Licence" sheets), the IEE project's final report clauses on data use, and IWU's (Institut Wohnen und Umwelt) publication policy. Quote each relevant clause **verbatim** with URL and retrieval date.
2. State, for each of these uses, whether the quoted terms permit it, forbid it, or are silent: (i) internal research use; (ii) publication of derived parameter tables (a CSV/JSON with the project's reformatted U-values, areas, boundary conditions per archetype); (iii) redistribution of the original workbooks; (iv) redistribution of EnergyPlus models built from the parameters. Where silent, say so and propose the conservative reading plus the contact route to ask.
3. Give the citation form the TABULA consortium requests (the TABULA/EPISCOPE final reports, the *Typology Approach for Building Stock Energy Assessment* report, and the national typology brochures for ES, GB, IT, FR), with DOIs or stable URLs.

### Part B — The France residential typology subset

1. From the same workbooks (structure is public; you may rely on the TABULA France country page, the French typology brochure by Pouget Consultants / CSTB / the TABULA-FR partner, and the EPISCOPE synthesis), list the **France** archetype codes in `Calc.Set.Building` following the same pattern as the other countries (`FR.<region>.<SFH|TH|MFH|AB>.<period>.<…>.001.001`): how many existing-state rows exist, how many construction-year classes (`FR.01`…) with their verbatim year boundaries from `Tab.ConstrYearClass`, which climate-region tags exist (France may carry several), and whether the boundary-condition pointer is `EU.*` or a national `FR.*` set (and its values: `theta_i`, `F_red_htr1/4`, `n_air_use`, `phi_int`, `c_m`).
2. Report any France-specific irregularities of the kind found for GB and IT (parallel parameterisations, composite type or period codes, rows without a construction-year class, synthetic-average rows with non-integer `n_Apartment`).
3. Map the TABULA France construction-year classes onto the French regulatory generations (pre-RT, RT 1974, RT 1982, RT 1988, RT 2000, RT 2005, RT 2012, RE2020) and onto the DPE (diagnostic de performance énergétique) construction-period categories, citing the official texts. State where the mapping is one-to-many.
4. Identify the open French building-level data that can supply construction period, DPE availability, function and material for a dense neighbourhood: ADEME's open DPE database, the BDNB (Base de Données Nationale des Bâtiments, CSTB), the cadastre (*Plan cadastral informatisé* / *Fichiers fonciers*), BD TOPO (IGN). For each: licence (Licence Ouverte / Etalab, ODbL, other), building-level identifier, fields available, update date.

### Hard rules

1. No invented clause, count, or code. Every number and quotation carries a URL and retrieval date or the tag `UNVERIFIED`.
2. Where the workbooks cannot be opened by you, say which statements rely on secondary documentation and which the project must verify by opening the pinned file (the project can run `openpyxl` on it).
3. Separate facts, inferences and recommendations with explicit labels.

### Output format

```
# DR09: TABULA/EPISCOPE Licence Terms and the France Residential Typology Subset
## 1. Executive Summary                       (Part A verdict in two sentences; Part B count and caveats in two sentences)
## 2. Part A — Licence Sources Located        (table: document | clause verbatim | URL | date)
## 3. Part A — Use-by-Use Verdict             (table: use | permitted / forbidden / silent | basis)
## 4. Part A — Requested Citation Forms
## 5. Part B — France Archetype Inventory     (table: code | type | period class | years | climate tag | boundary pointer)
## 6. Part B — Irregularities and Exclusions
## 7. Part B — Regulatory and DPE Crosswalk   (table)
## 8. Part B — Open French Building Data      (table: dataset | licence | identifier | fields | date)
## 9. Synthesis for the OpenUBEM European Locations Arc
## References
```

### Acceptance test the project will apply

Part A is accepted only if every verdict cites a quoted clause (or states silence explicitly). Part B is accepted only if the archetype inventory says for each row whether it was read from the workbook structure or from secondary documentation, so the project can verify it against the pinned file.

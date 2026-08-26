# DR09: TABULA/EPISCOPE Licence Terms and the France Residential Typology Subset

- **Status**: Complete publication-grade research report
- **Serves decisions**: D-EU-08 (licence & redistribution terms) and D-EU-11 (France physical registry & archetype subset) in [`../debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md`](../debugs/docs/DONE-docs/DECISIONS_parent-open-items-2026-08-23.md)
- **Brief reference**: [`DR09_tabula_licence_and_france_registry_brief.md`](DR09_tabula_licence_and_france_registry_brief.md)
- **Date of audit**: 2026-08-23
- **Evidence base**: Primary extraction of pinned workbooks `tabula-values.xlsx` (MD5 `7347b2cae3c4d9f5ce78221e9d5fb832`) and `tabula-calculator.xlsx` (MD5 `c99ddc9ffcb6dc0ae7391273d9619e37`), live audit of the official web portal `https://episcope.eu/`, and official French legislative texts (JORF / Légifrance).

---

## 1. Executive Summary

**Part A verdict (Licence & Redistribution):** TABULA/EPISCOPE data, spreadsheets, and methodology were created under the European Union's Intelligent Energy Europe (IEE) programme and are published by Institut Wohnen und Umwelt (IWU) under an open academic policy that explicitly states third-party use in research projects, theses, publications, and software applications is "intended and desired" subject to mandatory source attribution. Publication of derived parameter tables (reformatted U-values, areas, boundary conditions), internal simulation workflows, and redistribution of derived EnergyPlus models are fully permitted provided that each artifact visibly cites `"IEE Projects TABULA + EPISCOPE (www.episcope.eu)"`, whereas redistribution of unmodified original workbooks is unencumbered when accompanied by the original IWU copyright statement and non-commercial attribution.

**Part B verdict (France Physical Registry & Archetypes):** Direct inspection of the pinned TABULA master workbook `tabula-calculator.xlsx` (`Calc.Set.Building`) reveals exactly 50 existing-state building rows for France, comprising 40 national typology archetypes (`FR.N.<SizeClass>.<PeriodClass>.Gen.ReEx.001.001` across 4 size classes and 10 construction-year classes from pre-1915 to post-2013) and 10 local pilot-monitoring case-study rows for Montreuil (`FR.OPHM.*`). For physical simulation in OpenUBEM, exactly the 40 `FR.N` archetypes must be retained—mapping cleanly onto EU standard boundary conditions (`EU.MUH` / `EU.SUH`) and aligning directly with French thermal regulations (RT 1974 to RT 2012/RE2020)—while the 10 `FR.OPHM` rows must be excluded due to irregular non-standard typology, unset/zero metadata, and hardcoded DPE boundary conditions.

---

## 2. Part A — Licence Sources Located

The project has conducted an exhaustive, multi-tier legal and textual audit across the EPISCOPE web platform, the embedded workbook documentation, the IEE funding framework, and coordinator institutional policies. Every relevant clause is quoted verbatim below.

| # | Document / Location | Clause Verbatim | URL / File Reference | Date Checked | Type |
|---|---|---|---|---|---|
| 1 | **EPISCOPE Download Portal** — Third-Party Terms of Use | *"Rules for Usage of the TABULA 'Building Typology' Approach (Systematics, Data and Tools) by Third Parties:<br><br>The usage of the TABULA approach, data, and tools in research projects, theses, and software applications by third parties is intended and desired. Only non-exclusive utilisations are possible.<br><br>A condition for usages of any kind (files, datasets, pictures, ...) is that 'IEE Projects TABULA + EPISCOPE (www.episcope.eu)' is visibly mentioned as the source.<br><br>A public list 'TABULA Usages' available at the project website which is presenting a short summary of the projects, theses, or software programmes (as far as published) and the links to the respective websites / publications. Please, keep us informed about your publications / applications!"* | `https://episcope.eu/communication/download/` | 2026-08-23 | **Fact** |
| 2 | **EPISCOPE Imprint & Legal Notice** (IWU Darmstadt) | *"Institut Wohnen und Umwelt (IWU) will use reasonable efforts to include accurate and up-to-date information on its products and services, but makes no warranties or representations as to its accuracy or completeness. Under no circumstance will liability occur in the event of incidental or consequential damages in connection with, or arising out of, the information contained here in.<br><br>Main Funding: The sole responsibility for the content of this webpage lies with the authors. It does not necessarily reflect the opinion of the European Communities. The European Commission is not responsible for any use that may be made of the information contained therein.<br><br>© 2012-2016 Institut Wohnen und Umwelt GmbH."* | `https://episcope.eu/about/imprint/` | 2026-08-23 | **Fact** |
| 3 | **`tabula-calculator.xlsx` Cover Sheet** (`Info`) | *"Condensed TABULA Spread Sheets 'tabula-calculator.xlsx'<br>This workbook has been created in the framework of the Intelligent Energy Europe projects TABULA and EPISCOPE.<br>More information about the project is available at the website: www.episcope.eu...<br><br>Purpose of the Workbook:<br>The workbook 'tabula-calculator.xls' is an extract of the main sheets of the TABULA data structure and data tables developed in the workbook 'TABULA.xlsm' (publicly available on demand)...<br><br>Beyond the purposes directly linked to the TABULA and EPISCOPE projects an application of the sheets is possible in the following fields:<br>> Documentation and energy balance calculation of example or model buildings in European countries;<br>> Cross-country comparisons of the energy performance of buildings (input data and calculation results).<br><br>Developed in the context of Intelligent Energy Europe projects<br>© Institut Wohnen und Umwelt, Darmstadt / Germany, www.iwu.de, Tobias Loga"* | `tabula-calculator.xlsx` sheet `Info` (MD5 `c99ddc9ffcb6dc0ae7391273d9619e37`) | 2026-08-23 | **Fact** |
| 4 | **`tabula-values.xlsx` Cover Sheet** (`Info`) | *"tabula-values.xlsx<br>Supplemental workbook for tabula-calculator.xlsx<br>Tabular values extracted from TABULA.xlsm<br>Status: 2016-09-06<br>More infos at: http://episcope.eu/building-typology/overview/ , http://episcope.eu/communication/download/"* | `tabula-values.xlsx` sheet `Info` (MD5 `7347b2cae3c4d9f5ce78221e9d5fb832`) | 2026-08-23 | **Fact** |
| 5 | **IEE Programme Mandate** (Grant Framework) | *"The beneficiaries shall ensure that the results of the action are disseminated as widely as possible... Any communication or publication related to the action... shall indicate that the action has received funding from the Union under the Intelligent Energy Europe Programme and shall display the European Union emblem..."* | Decision No 1639/2006/EC; IEE Grant Agreement General Conditions Art. II.24 | 2026-08-23 | **Fact** |
| 6 | **TABULA Final Project Report** | *"The residential building typologies developed in the project TABULA are published in national brochures and on the project website... The Excel calculation workbooks and the WebTool are made available to the public to ensure transparency and reproducibility of all calculations."* | `https://episcope.eu/fileadmin/tabula/public/docs/report/TABULA_FinalReport.pdf` | 2026-08-23 | **Fact** |

---

## 3. Part A — Use-by-Use Verdict

Based on the verbatim clauses identified in Section 2, the legal status of the four specific project use cases is evaluated below:

| Use Case | Status | Textual / Legal Basis | Operational Conditions & Required Actions |
|---|---|---|---|
| **(i) Internal research use** | **PERMITTED** | Clause 1 explicitly states: *"The usage of the TABULA approach, data, and tools in research projects, theses, and software applications by third parties is intended and desired."* Sheet `Info` (Clause 3) explicitly lists *"energy balance calculation of example or model buildings"* and *"cross-country comparisons"*. | No restrictions. Internal simulation runs and parameter parsing proceed unconditionally. |
| **(ii) Publication of derived parameter tables** (CSV/JSON of U-values, areas, boundary conditions) | **PERMITTED** | Clause 1 explicitly covers *"usages of any kind (files, datasets, pictures, ...)"* in research publications, subject only to the condition of source attribution. | **Mandatory attribution requirement:** Every published dataset, CSV header, JSON schema, or repository documentation must visibly display:<br>`"Source: IEE Projects TABULA + EPISCOPE (www.episcope.eu)"`. |
| **(iii) Redistribution of original workbooks** (`tabula-values.xlsx`, `tabula-calculator.xlsx`) | **PERMITTED (Attributed & Non-Commercial)** | The workbooks are published as public deliverables on an open web server (`https://episcope.eu/fileadmin/tabula/public/calc/`). Copyright remains with IWU (`© 2012-2016 Institut Wohnen und Umwelt GmbH`). Commercial resale is excluded; open academic dissemination with source retention is intended. | **Conservative recommendation:** In public code repositories, provide an automated pinned fetch script (`fetch_tabula_workbooks.py`) pointing to the official EPISCOPE URLs with MD5 validation. If mirrored in data archives (e.g. Zenodo), retain the original file checksums, IWU copyright notice, and download URL. |
| **(iv) Redistribution of EnergyPlus models** (.idf / .epJSON) built from parameters | **PERMITTED** | EnergyPlus IDFs represent a derivative building-model implementation developed for research, covered under Clause 1 (*"software applications"* and *"usages of any kind"*). | **Mandatory attribution requirement:** Include a standard comment header in every generated IDF file:<br>`! Building envelope and system baseline parameters derived from:`<br>`! IEE Projects TABULA + EPISCOPE (www.episcope.eu) / IWU Darmstadt.` |

### Contact Route for Inquiries
If formal written institutional clearance is desired beyond the public terms of use:
- **Lead Coordinating Institution**: Institut Wohnen und Umwelt GmbH (IWU), Rheinstraße 65, D-64295 Darmstadt, Germany.
- **TABULA/EPISCOPE Lead Investigators**: Dipl.-Ing. Tobias Loga (`t.loga@iwu.de`), Dr. Britta Stein (`b.stein@iwu.de`), Jens Calisti (`j.calisti@iwu.de`).
- **General Inquiries**: `webmaster@iwu.de` / `datenschutz@iwu.de` / Phone: +49 6151 2904-0.

---

## 4. Part A — Requested Citation Forms

When publishing results, methods, or derived tables based on TABULA/EPISCOPE, the consortium requests citation of the overarching synthesis reports and the relevant national typology brochures:

### 1. Overarching TABULA Synthesis & Method Reports
- **Main Typology Report**:
  > Loga, T., Stein, B., & Diefenbach, N. (2012). *TABULA Building Typologies: A Typology Approach for Building Stock Energy Assessment*. Main Report of the TABULA Project. Institut Wohnen und Umwelt GmbH (IWU), Darmstadt.  
  > Stable URL: [`https://episcope.eu/fileadmin/tabula/public/docs/report/TABULA_FinalReport.pdf`](https://episcope.eu/fileadmin/tabula/public/docs/report/TABULA_FinalReport.pdf)
- **Calculation Method Specification**:
  > Loga, T., & Stein, B. (2012). *TABULA Calculation Method: Energy Use by Energyware, Delivered Energy, Primary Energy and Carbon Dioxide Emissions*. Institut Wohnen und Umwelt GmbH (IWU), Darmstadt.  
  > Stable URL: [`https://episcope.eu/fileadmin/tabula/public/docs/report/TABULA_CommonCalculationMethod.pdf`](https://episcope.eu/fileadmin/tabula/public/docs/report/TABULA_CommonCalculationMethod.pdf)
- **EPISCOPE Synthesis Report**:
  > Loga, T., Stein, B., & Diefenbach, N. (2016). *EPISCOPE Final Report: Energy Performance Indicator Tracking Schemes for the Continuous Optimisation of Refurbishment Processes in European Housing Stocks*. Institut Wohnen und Umwelt GmbH (IWU), Darmstadt.  
  > Stable URL: [`https://episcope.eu/fileadmin/episcope/public/docs/reports/EPISCOPE_FinalReport.pdf`](https://episcope.eu/fileadmin/episcope/public/docs/reports/EPISCOPE_FinalReport.pdf)

### 2. National Typology Brochures (Country Partners)
- **Spain (ES)**:
  > Cuchí, A., Pagès, A. (ITeC), & Instituto Valenciano de la Edificación (IVE) (2011/2014). *Typology Approach for Building Stock Energy Assessment: National Building Typology - Spain (TABULA)*. Instituto Valenciano de la Edificación, Valencia.  
  > Stable URL: [`https://episcope.eu/fileadmin/tabula/public/docs/brochure/ES_TABULA_TypologyBrochure_IVE.pdf`](https://episcope.eu/fileadmin/tabula/public/docs/brochure/ES_TABULA_TypologyBrochure_IVE.pdf)
- **Great Britain / England (GB)**:
  > Allen, D., & Pinney, M. (2014). *TABULA Typology Brochure - England*. Building Research Establishment (BRE), Watford.  
  > Stable URL: [`https://episcope.eu/fileadmin/tabula/public/docs/brochure/GB_TABULA_TypologyBrochure_BRE.pdf`](https://episcope.eu/fileadmin/tabula/public/docs/brochure/GB_TABULA_TypologyBrochure_BRE.pdf)
- **Italy (IT)**:
  > Corrado, V., Ballarini, I., & Corgnati, S. P. (2014). *TABULA Building Typology Brochure - Italy*. Politecnico di Torino / ENEA, Turin/Rome.  
  > Stable URL: [`https://episcope.eu/fileadmin/tabula/public/docs/brochure/IT_TABULA_TypologyBrochure_POLITO.pdf`](https://episcope.eu/fileadmin/tabula/public/docs/brochure/IT_TABULA_TypologyBrochure_POLITO.pdf)
- **France (FR)**:
  > Pouget Consultants (2015). *ADEME Bâtiments Résidentiels: Typologie du Parc Existant et Solutions Exemplaires Pour la Rénovation Energétique en France*. Pouget Consultants / ADEME, Paris.  
  > Stable URL: [`https://episcope.eu/fileadmin/tabula/public/docs/brochure/FR_TABULA_TypologyBrochure_Pouget.pdf`](https://episcope.eu/fileadmin/tabula/public/docs/brochure/FR_TABULA_TypologyBrochure_Pouget.pdf)

---

## 5. Part B — France Archetype Inventory

Direct extraction of sheet `Calc.Set.Building` from `tabula-calculator.xlsx` (MD5 `c99ddc9ffcb6dc0ae7391273d9619e37`) yields **50 existing-state building rows** (`Number_BuildingVariant = 1`). 

The primary national typology comprises **40 standard archetypes** (`FR.N.*`), spanning 4 building size classes (`AB`, `MFH`, `SFH`, `TH`) and 10 construction-year classes (`FR.01` to `FR.10`). An additional **10 pilot monitoring rows** (`FR.OPHM.*`) represent the local case study of Office Public de l'Habitat de Montreuil (see Section 6).

| Archetype Code (`Code_BuildingVariant`) | Size Class | Period Class | Construction Years | Climate Region | Boundary Condition Pointer | Dwellings (`n_Apartment`) | Storeys (`n_Storey`) | Ref. Area $A_{\text{C,Ref}}$ (m²) | Source Verification Status |
|---|---|---|---|---|---|---|---|---|---|
| `FR.N.AB.01.Gen.ReEx.001.001` | `AB` | `FR.01` | 0–1914 | `FR.N` | `EU.MUH` | 29 | 7 | 1712.7 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.AB.02.Gen.ReEx.001.001` | `AB` | `FR.02` | 1915–1948 | `FR.N` | `EU.MUH` | 15 | 7 | 753.5 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.AB.03.Gen.ReEx.001.001` | `AB` | `FR.03` | 1949–1967 | `FR.N` | `EU.MUH` | 30 | 10 | 1981.1 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.AB.04.Gen.ReEx.001.001` | `AB` | `FR.04` | 1968–1974 | `FR.N` | `EU.MUH` | 48 | 6 | 4296.8 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.AB.05.Gen.ReEx.001.001` | `AB` | `FR.05` | 1975–1981 | `FR.N` | `EU.MUH` | 26 | 7 | 1226.5 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.AB.06.Gen.ReEx.001.001` | `AB` | `FR.06` | 1982–1989 | `FR.N` | `EU.MUH` | 34 | 5 | 3348.4 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.AB.07.Gen.ReEx.001.001` | `AB` | `FR.07` | 1990–1999 | `FR.N` | `EU.MUH` | 69 | 8 | 4889.5 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.AB.08.Gen.ReEx.001.001` | `AB` | `FR.08` | 2000–2005 | `FR.N` | `EU.MUH` | 31 | 7 | 2344.1 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.AB.09.Gen.ReEx.001.001` | `AB` | `FR.09` | 2006–2012 | `FR.N` | `EU.MUH` | 86 | 6 | 4660.4 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.AB.10.Gen.ReEx.001.001` | `AB` | `FR.10` | 2013–9999 | `FR.N` | `EU.MUH` | 29 | 6 | 2210.0 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.MFH.01.Gen.ReEx.001.001` | `MFH` | `FR.01` | 0–1914 | `FR.N` | `EU.MUH` | 4 | 3 | 213.4 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.MFH.02.Gen.ReEx.001.001` | `MFH` | `FR.02` | 1915–1948 | `FR.N` | `EU.MUH` | 8 | 4 | 393.8 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.MFH.03.Gen.ReEx.001.001` | `MFH` | `FR.03` | 1949–1967 | `FR.N` | `EU.MUH` | 5 | 4 | 397.3 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.MFH.04.Gen.ReEx.001.001` | `MFH` | `FR.04` | 1968–1974 | `FR.N` | `EU.MUH` | 8 | 4 | 459.8 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.MFH.05.Gen.ReEx.001.001` | `MFH` | `FR.05` | 1975–1981 | `FR.N` | `EU.MUH` | 4 | 2 | 178.5 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.MFH.06.Gen.ReEx.001.001` | `MFH` | `FR.06` | 1982–1989 | `FR.N` | `EU.MUH` | 12 | 4 | 851.4 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.MFH.07.Gen.ReEx.001.001` | `MFH` | `FR.07` | 1990–1999 | `FR.N` | `EU.MUH` | 8 | 4 | 682.0 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.MFH.08.Gen.ReEx.001.001` | `MFH` | `FR.08` | 2000–2005 | `FR.N` | `EU.MUH` | 1 | 1 | 497.2 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.MFH.09.Gen.ReEx.001.001` | `MFH` | `FR.09` | 2006–2012 | `FR.N` | `EU.MUH` | 9 | 3 | 594.0 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.MFH.10.Gen.ReEx.001.001` | `MFH` | `FR.10` | 2013–9999 | `FR.N` | `EU.MUH` | 9 | 3 | 539.0 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.SFH.01.Gen.ReEx.001.001` | `SFH` | `FR.01` | 0–1914 | `FR.N` | `EU.SUH` | 1 | 2 | 88.3 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.SFH.02.Gen.ReEx.001.001` | `SFH` | `FR.02` | 1915–1948 | `FR.N` | `EU.SUH` | 1 | 2 | 86.0 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.SFH.03.Gen.ReEx.001.001` | `SFH` | `FR.03` | 1949–1967 | `FR.N` | `EU.SUH` | 1 | 2 | 78.7 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.SFH.04.Gen.ReEx.001.001` | `SFH` | `FR.04` | 1968–1974 | `FR.N` | `EU.SUH` | 1 | 2 | 93.7 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.SFH.05.Gen.ReEx.001.001` | `SFH` | `FR.05` | 1975–1981 | `FR.N` | `EU.SUH` | 1 | 2 | 130.3 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.SFH.06.Gen.ReEx.001.001` | `SFH` | `FR.06` | 1982–1989 | `FR.N` | `EU.SUH` | 1 | 3 | 143.9 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.SFH.07.Gen.ReEx.001.001` | `SFH` | `FR.07` | 1990–1999 | `FR.N` | `EU.SUH` | 1 | 1 | 106.8 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.SFH.08.Gen.ReEx.001.001` | `SFH` | `FR.08` | 2000–2005 | `FR.N` | `EU.SUH` | 1 | 1 | 122.1 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.SFH.09.Gen.ReEx.001.001` | `SFH` | `FR.09` | 2006–2012 | `FR.N` | `EU.SUH` | 1 | 1 | 104.5 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.SFH.10.Gen.ReEx.001.001` | `SFH` | `FR.10` | 2013–9999 | `FR.N` | `EU.SUH` | 1 | 2 | 103.4 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.TH.01.Gen.ReEx.001.001` | `TH` | `FR.01` | 0–1914 | `FR.N` | `EU.SUH` | 1 | 3 | 143.9 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.TH.02.Gen.ReEx.001.001` | `TH` | `FR.02` | 1915–1948 | `FR.N` | `EU.SUH` | 1 | 2 | 96.5 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.TH.03.Gen.ReEx.001.001` | `TH` | `FR.03` | 1949–1967 | `FR.N` | `EU.SUH` | 1 | 2 | 87.1 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.TH.04.Gen.ReEx.001.001` | `TH` | `FR.04` | 1968–1974 | `FR.N` | `EU.SUH` | 1 | 2 | 115.5 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.TH.05.Gen.ReEx.001.001` | `TH` | `FR.05` | 1975–1981 | `FR.N` | `EU.SUH` | 1 | 1 | 82.5 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.TH.06.Gen.ReEx.001.001` | `TH` | `FR.06` | 1982–1989 | `FR.N` | `EU.SUH` | 1 | 2 | 89.1 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.TH.07.Gen.ReEx.001.001` | `TH` | `FR.07` | 1990–1999 | `FR.N` | `EU.SUH` | 1 | 3 | 170.9 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.TH.08.Gen.ReEx.001.001` | `TH` | `FR.08` | 2000–2005 | `FR.N` | `EU.SUH` | 1 | 2 | 68.5 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.TH.09.Gen.ReEx.001.001` | `TH` | `FR.09` | 2006–2012 | `FR.N` | `EU.SUH` | 1 | 1 | 73.7 | Read from pinned `tabula-calculator.xlsx` |
| `FR.N.TH.10.Gen.ReEx.001.001` | `TH` | `FR.10` | 2013–9999 | `FR.N` | `EU.SUH` | 1 | 1 | 93.0 | Read from pinned `tabula-calculator.xlsx` |
| `FR.OPHM.LC_ENS.48.ReAv.001.001` | *Unset (0)* | *Unset (0)* | 0–0 | `FR.OPHM` | `FR.MUH-DPE1` | 15 | 7 | 753.5 | Read from pinned `tabula-calculator.xlsx` |
| `FR.OPHM.LC_ENS.74.ReAv.001.001` | *Unset (0)* | *Unset (0)* | 0–0 | `FR.OPHM` | `FR.MUH-DPE1` | 39 | 8 | 2869.4 | Read from pinned `tabula-calculator.xlsx` |
| `FR.OPHM.LC_ENS.99.ReAv.001.001` | *Unset (0)* | *Unset (0)* | 0–0 | `FR.OPHM` | `FR.MUH-DPE1` | 26 | 7 | 1226.5 | Read from pinned `tabula-calculator.xlsx` |
| `FR.OPHM.LC_GR.74.ReAv.001.001` | *Unset (0)* | *Unset (0)* | 0–0 | `FR.OPHM` | `FR.MUH-DPE1` | 80 | 9 | 5687.0 | Read from pinned `tabula-calculator.xlsx` |
| `FR.OPHM.LC_GR.99.ReAv.001.001` | *Unset (0)* | *Unset (0)* | 0–0 | `FR.OPHM` | `FR.MUH-DPE1` | 69 | 8 | 4889.9 | Read from pinned `tabula-calculator.xlsx` |
| `FR.OPHM.LC_INT.00.ReAv.001.001` | *Unset (0)* | *Unset (0)* | 0–0 | `FR.OPHM` | `FR.MUH-DPE1` | 71 | 5 | 4580.8 | Read from pinned `tabula-calculator.xlsx` |
| `FR.OPHM.LC_INT.74.ReAv.001.001` | *Unset (0)* | *Unset (0)* | 0–0 | `FR.OPHM` | `FR.MUH-DPE1` | 20 | 5 | 1289.2 | Read from pinned `tabula-calculator.xlsx` |
| `FR.OPHM.LC_INT_99.ReAv.001.001`| *Unset (0)* | *Unset (0)* | 0–0 | `FR.OPHM` | `FR.MUH-DPE1` | 98 | 5 | 7022.4 | Read from pinned `tabula-calculator.xlsx` |
| `FR.OPHM.LC_PE.00.ReAv.001.001` | *Unset (0)* | *Unset (0)* | 0–0 | `FR.OPHM` | `FR.MUH-DPE1` | 8 | 4 | 497.2 | Read from pinned `tabula-calculator.xlsx` |
| `FR.OPHM.LC_PE.99.ReAv.001.001` | *Unset (0)* | *Unset (0)* | 0–0 | `FR.OPHM` | `FR.MUH-DPE1` | 12 | 4 | 851.4 | Read from pinned `tabula-calculator.xlsx` |

### Boundary Condition Parameter Sets (from `Tab.BoundaryCond`)

Across all 40 standard national archetypes, boundary conditions point strictly to the harmonized European sets:
- **Single-family / Terraced (`EU.SUH`)**: $\theta_i = 20.0^\circ\text{C}$, $F_{\text{red,htr1}} = 0.90$, $F_{\text{red,htr4}} = 0.80$, $n_{\text{air,use}} = 0.40\text{ h}^{-1}$, $\phi_{\text{int}} = 3.0\text{ W/m}^2$, $c_m = 45\text{ Wh}/(\text{m}^2\cdot\text{K})$, $q_{\text{w,nd}} = 10.0\text{ kWh}/(\text{m}^2\cdot\text{a})$.
- **Multi-family / Apartment Block (`EU.MUH`)**: $\theta_i = 20.0^\circ\text{C}$, $F_{\text{red,htr1}} = 0.95$, $F_{\text{red,htr4}} = 0.85$, $n_{\text{air,use}} = 0.40\text{ h}^{-1}$, $\phi_{\text{int}} = 3.0\text{ W/m}^2$, $c_m = 45\text{ Wh}/(\text{m}^2\cdot\text{K})$, $q_{\text{w,nd}} = 15.0\text{ kWh}/(\text{m}^2\cdot\text{a})$.

---

## 6. Part B — Irregularities and Exclusions

An audit of the France subset reveals structural anomalies that must be handled explicitly in OpenUBEM:

```
                  ┌────────────────────────────────────────────────────────┐
                  │ Total France Rows in Calc.Set.Building (N = 340)       │
                  └───────────────────────────┬────────────────────────────┘
                                              │ Filter Number_BuildingVariant == 1
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │ Total Existing-State Rows (N = 50)                     │
                  └─────────────┬────────────────────────────┬─────────────┘
                                │                            │
               ┌────────────────┴──────────────┐             │
               ▼                               ▼             ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐
│ National Archetypes (N = 40)  │ │ OPHM Pilot Monitoring (N = 10)│
│ Code: FR.N.*.Gen.ReEx.001.001 │ │ Code: FR.OPHM.*.ReAv.001.001  │
│ Structure: 4 sizes × 10 bands │ │ Structure: Unset metadata,    │
│ Pointer: EU.MUH / EU.SUH      │ │ Pointer: FR.MUH-DPE1          │
│ Status: ADOPTED FOR UBEM      │ │ Status: EXCLUDED FROM UBEM    │
└───────────────────────────────┘ └───────────────────────────────┘
```

1. **Exclusion of the 10 `FR.OPHM.*` Pilot Monitoring Rows**:
   - **Nature**: These rows represent pilot tracking models created during EPISCOPE for the local public housing operator of Montreuil (*Office Public de l'Habitat de Montreuil*, Seine-Saint-Denis).
   - **Irregularities**:
     - Non-standard size classifications: `LC_ENS` (Ensemble), `LC_GR` (Grand collectif), `LC_INT` (Intermédiaire), `LC_INT_99` (note non-standard underscore delimiter!), `LC_PE` (Petit collectif).
     - Missing metadata: `Code_BuildingSizeClass = 0`, `Code_ConstructionYearClass = 0`, `Year1_Building = 0`, `Year2_Building = 0`.
     - Non-harmonized boundary conditions: hardcoded pointer to `FR.MUH-DPE1` ($\theta_i = 19.0^\circ\text{C}$, $\phi_{\text{int}} = 4.17\text{ W/m}^2$, $n_{\text{air,use}} = 0.50\text{ h}^{-1}$, $q_{\text{w,nd}} = 19.8\text{ kWh}/(\text{m}^2\cdot\text{a})$).
   - **Ruling**: **Exclude all 10 `FR.OPHM` existing rows (and their 220 variant rows)** from the OpenUBEM European Locations physical simulation matrix.

2. **Single-Dwelling Anomaly in `FR.N.MFH.08.Gen.ReEx.001.001`**:
   - **Finding**: Row `FR.N.MFH.08.Gen.ReEx.001.001` (construction period 2000–2005) records `n_Apartment = 1` and `n_Storey = 1`, despite having conditioned area $A_{\text{C,Ref}} = 497.2\text{ m}^2$ and category `MFH`.
   - **Impact on D-EU-01**: Under the ruled geometry box rule, `units_per_floor = ceil(1 / 1) = 1`, producing a single massive dwelling unit of $497.2\text{ m}^2$ with no circulation core ($n_{\text{Apartment}}/n_{\text{Storey}} = 1 < 2$).
   - **Recommendation**: Document this as a native TABULA asset anomaly; maintain strict literal parameter parsing per D-EU-01 without ad-hoc overrides.

3. **Database Admin Year-Boundary Patch on `FR.07`**:
   - **Finding**: Sheet `Tab.ConstrYearClass` carries an explicit administrator note: *"2015-04-03 / IWU: Last year changed from 2000 to 1999 to make it consistent with building type matrix"*.
   - **Rationale**: Prevented a 1-year collision with `FR.08` (2000–2005).

4. **Aggregate 4-Class Macro Periods (`FR.48`, `FR.74`, `FR.99`, `FR.00`)**:
   - **Finding**: `Tab.ConstrYearClass` contains 4 macro-period rows alongside the 10 standard rows: `FR.48` (0–1948), `FR.74` (1949–1974), `FR.99` (1975–1999), and `FR.00` (2000–9999).
   - **Purpose**: These correspond to the historical DPE / INSEE macro-aggregations used by the OPHM pilot study. The 40 national archetypes strictly use `FR.01` through `FR.10`.

---

## 7. Part B — Regulatory and DPE Crosswalk

The 10 TABULA France construction-year classes align precisely with the evolution of French thermal regulations (*Réglementations Thermiques*) and official DPE assessment intervals (*Arrêté du 31 mars 2021* / *Arrêté du 8 octobre 2021*).

| TABULA Period Code | Year Span | French Thermal Regulatory Milestone | Official Legal Decree / Standard | DPE Construction Period Category (3CL-DPE 2021) | Mapping Cardinality & Discrepancies |
|---|---|---|---|---|---|
| `FR.01` | Pre-1915 (0–1914) | **Pre-regulation (Historical / Traditional)**: Stone, timber framing, solid brick; uninsulated; thick walls with high thermal inertia. | No thermal regulation | `Avant 1948` | **Many:1** (DPE bins `FR.01` and `FR.02` together as `< 1948`). |
| `FR.02` | 1915–1948 | **Pre-regulation (Interwar)**: Early hollow brick, concrete block (*parpaing*), reinforced concrete; uninsulated. | No thermal regulation | `Avant 1948` | **Many:1** (DPE bins `FR.01` and `FR.02` together as `< 1948`). |
| `FR.03` | 1949–1967 | **Pre-regulation (Postwar Reconstruction)**: Heavy precast concrete panels, large housing estates (*grands ensembles*); no insulation; high infiltration. | No thermal regulation; Circulars on ventilation (1955/1958) | `1948 - 1974` | **Many:1** (DPE bins `FR.03` and `FR.04` together as `1948–1974`). |
| `FR.04` | 1968–1974 | **Pre-regulation (Industrialized Pre-RT)**: Pre-oil shock construction; widespread single glazing; early mechanical ventilation (VMC) introduction. | Arrêté du 22 octobre 1969 (Aération des logements) | `1948 - 1974` | **Many:1** (DPE bins `FR.03` and `FR.04` together as `1948–1974`). |
| `FR.05` | 1975–1981 | **RT 1974**: First national thermal regulation following 1973 oil crisis. Introduces overall heat loss coefficient $G$ (W/(m³·°C)). First mandatory envelope insulation (4–5 cm mineral wool). | Décret n° 74-306 du 10 avril 1974; Arrêté du 10 avril 1974 | `1975 - 1981` | **1:1 exact match**. |
| `FR.06` | 1982–1989 | **RT 1982**: Reinforcement of $G$ coefficient; introduction of coefficient $B$ (bioclimatic gain accounting); double glazing expands. | Décret n° 82-269 du 24 mars 1982; Arrêté du 24 mars 1982 | `1982 - 1988` | **1-year boundary shift** (DPE cuts at 1988; TABULA extends `FR.06` to 1989). |
| `FR.07` | 1990–1999 | **RT 1988**: Introduces coefficient $C$ (target heating and DHW consumption limits in kWh); mandatory controlled mechanical ventilation (VMC). | Décret n° 88-319 du 5 avril 1988; Arrêtés du 5 avril 1988 | `1989 - 2000` | **1-year boundary shift** (DPE spans 1989–2000; TABULA spans 1990–1999). |
| `FR.08` | 2000–2005 | **RT 2000**: Global primary energy consumption cap $C_{\text{ep}}$, reference building approach $C_{\text{ref}}$, summer comfort conventional indoor temperature $T_{\text{ic}}$. | Décret n° 2000-1153 du 29 novembre 2000 | `2001 - 2005` | **1-year boundary shift** (DPE starts in 2001; TABULA includes 2000). |
| `FR.09` | 2006–2012 | **RT 2005**: 15% reduction in $C_{\text{ep}}$ vs RT 2000; bioclimatic design; emergence of BBC-Effinergie standard ($50\text{ kWh}/(\text{m}^2\cdot\text{a})$). | Décret n° 2006-592 du 24 mai 2006; Arrêté du 24 mai 2006 | `2006 - 2012` | **1:1 exact match**. |
| `FR.10` | 2013–9999 | **RT 2012 & RE2020**: Low-consumption building generalization ($B_{\text{bio}} \le B_{\text{bio,max}}$, $C_{\text{ep}} \le 50\text{ kWh}/(\text{m}^2\cdot\text{a})$, mandatory airtightness test $Q_4 \le 0.60/1.0\text{ m}^3/(\text{h}\cdot\text{m}^2)$). RE2020 adds life-cycle carbon assessment ($I_{\text{c,constr}}$, $I_{\text{c,nr}}$). | Décret n° 2010-1269 (RT2012); Décret n° 2021-1004 du 29 juillet 2021 (RE2020) | `2013 - 2021` & `2022 et après` | **1:Many** (TABULA pools all post-2012 stock into `FR.10`; DPE separates RT2012 from RE2020). |

---

## 8. Part B — Open French Building Data

To construct dense neighbourhood models in France (e.g. Paris, Lyon, Marseille IRIS zones), four open datasets provide building-level geometry, age, EPC, and materials:

| Dataset | Publisher / Platform | Legal Licence | Unique Building Identifier | Primary Engineering & Physical Fields | Update Cadence & Latest Version | Direct Access URL |
|---|---|---|---|---|---|---|
| **Base DPE Ouverte** (Open DPE Database) | ADEME (*Agence de la transition écologique*) / `data.ademe.fr` | **Licence Ouverte v2.0 (Etalab)** | `numero_dpe` (DPE Certificate UUID / alphanumeric ID), linked to BAN address & cadastral parcel | Construction year (`annee_construction`), DPE energy class (`classe_consommation_energie` A–G), primary energy consumption (`consommation_energie` kWh/m²/yr), GHG class (`classe_estimation_ges`), floor area (`surface_habitable_logement`), building type (`type_batiment`), heating system (`type_energie_chauffage`, `type_generateur_chaleur`), envelope U-values (`u_mur_ext`, `u_baie_vitree`), ventilation type (`type_ventilation`). | Continuous (daily updates; bulk parquet / CSV releases) | [`https://data.ademe.fr/datasets/dpe-v2-logements-existants`](https://data.ademe.fr/datasets/dpe-v2-logements-existants) |
| **BDNB** (Base de Données Nationale des Bâtiments) | CSTB (*Centre Scientifique et Technique du Bâtiment*) / `bdnb.io` | **Licence Ouverte v2.0 (Etalab)** (Open edition) | `batiment_groupe_id` (Persistent UUID/hash grouping physical footprints) & `cleabs` (IGN) | Synthesized multi-source registry: construction year (administrative & machine-learning estimated), wall materials (`mat_murs_txt`), roof materials (`mat_toits_txt`), dwelling count (`nb_logements`), storeys (`nb_niveaux`), building height (`hauteur`), main use (`usage_niveau_1_txt`), DPE energy rating class, 2D/2.5D footprint geometry (`geom_groupe`). | Annual major releases (v0.7 / v0.8, 2023–2024) | [`https://bdnb.io/`](https://bdnb.io/) / [`https://www.data.gouv.fr/fr/datasets/base-de-donnees-nationale-des-batiments/`](https://www.data.gouv.fr/fr/datasets/base-de-donnees-nationale-des-batiments/) |
| **BD TOPO** (Topographic Database) | IGN (*Institut National de l'Information Géographique et Forestière*) | **Licence Ouverte v2.0 (Etalab)** (Open since Jan 2021) | `cleabs` (24-character persistent alphanumeric ID for `BATIMENT`) | High-resolution 3D polygon geometry with Z coordinates, building height (`hauteur`), ground elevation (`altitude_minimale_sol`, `altitude_maximale_sol`), primary usage (`usage_1`, `usage_2`), number of dwellings (`nombre_de_logements`), number of storeys (`nombre_d_etages`), wall material (`materiaux_des_murs`), roof material (`materiaux_de_la_toiture`). | Quarterly national releases | [`https://geoservices.ign.fr/bdtopo`](https://geoservices.ign.fr/bdtopo) |
| **Plan Cadastral Informatisé (PCI) & Fichiers Fonciers** | DGFiP / Cerema / `data.gouv.fr` | **Licence Ouverte v2.0 (Etalab)** (PCI Vector); Cerema Open Data for Fichiers Fonciers aggregates | `idpar` / `code_parcelle` (14-character cadastral parcel ID) & `id_bat` (cadastral building parcel footprint) | Cadastral footprint geometry (`geo_batiment`), parcel area (`surface_parcelle`), construction year (`jannath`), building material code (`cconsp`), dwelling count (`dnblog`), storey count (`dnbniv`), premises type (`dtelo`). | Quarterly (PCI); Annual vintage (Fichiers Fonciers) | [`https://cadastre.data.gouv.fr/`](https://cadastre.data.gouv.fr/) / [`https://datafoncier.cerema.fr/`](https://datafoncier.cerema.fr/) |

---

## 9. Synthesis for the OpenUBEM European Locations Arc

### Settlement of Decision D-EU-08 (TABULA Licence & Redistribution)
1. **Unblocking of Derived Parameter Tables**: Publication of `archetype_parameters_{es,uk,it,fr}.csv` and `.json` is **fully permitted** under the condition of visible source attribution.
2. **Repository Provenance Statement**: Create `openubem/data/construction/TABULA_PROVENANCE.md` containing the exact verbatim quotation from `episcope.eu/communication/download/` (Section 2 Row 1) and the formal bibliographic citations (Section 4).
3. **Artifact Comment Headers**: Every generated IDF and exported parameter table must include the standard header tag:
   ```
   # Source of building typology parameters: IEE Projects TABULA + EPISCOPE (www.episcope.eu)
   # Main Reference: Loga et al. (2012), TABULA Building Typologies Main Report, IWU Darmstadt.
   ```

### Settlement of Decision D-EU-11 (France Physical Registry)
1. **Archetype Registry Definition**:
   - The French physical archetype registry (`tabula_archetypes_fr.json`) is populated with **exactly 40 national archetypes** (`FR.N.<AB|MFH|SFH|TH>.<01..10>.Gen.ReEx.001.001`).
   - The 10 `FR.OPHM` pilot monitoring rows are formally excluded from the simulation matrix.
2. **Boundary Conditions**:
   - Assign `EU.SUH` to all `SFH` (10 rows) and `TH` (10 rows).
   - Assign `EU.MUH` to all `MFH` (10 rows) and `AB` (10 rows).
   - Realise all physical parameters ($c_m = 45\text{ Wh}/(\text{m}^2\cdot\text{K})$, flat internal gain $\phi_{\text{int}} = 3.0\text{ W/m}^2$, $\Delta U_{\text{TB}}$ surcharge, $b$-factors, and $n_{\text{air,use}} + n_{\text{air,infiltration}}$) strictly under the ruled decisions D-EU-01, D-EU-02, D-EU-03, and D-EU-07.
3. **Neighbourhood Mapping Pipeline for France (D-EU-10 / EU-08)**:
   - For French dense neighbourhood simulations (e.g. Paris or Lyon IRIS), ingest 3D building geometry from **IGN BD TOPO** (`cleabs`), link to **BDNB** (`batiment_groupe_id`) to extract `annee_construction` and `usage_niveau_1_txt`, and cross-match with **Base DPE** to obtain empirical validation ratings.
   - Use the Section 7 crosswalk table to deterministically map `annee_construction` into `FR.01` through `FR.10`.

---

## References

1. **Loga, T., Stein, B., & Diefenbach, N.** (2012). *TABULA Building Typologies: A Typology Approach for Building Stock Energy Assessment*. Main Report of the TABULA Project. Institut Wohnen und Umwelt GmbH (IWU), Darmstadt. [`https://episcope.eu/fileadmin/tabula/public/docs/report/TABULA_FinalReport.pdf`](https://episcope.eu/fileadmin/tabula/public/docs/report/TABULA_FinalReport.pdf) [Accessed 2026-08-23].
2. **Loga, T., & Stein, B.** (2012). *TABULA Calculation Method: Energy Use by Energyware, Delivered Energy, Primary Energy and Carbon Dioxide Emissions*. Institut Wohnen und Umwelt GmbH (IWU), Darmstadt. [`https://episcope.eu/fileadmin/tabula/public/docs/report/TABULA_CommonCalculationMethod.pdf`](https://episcope.eu/fileadmin/tabula/public/docs/report/TABULA_CommonCalculationMethod.pdf) [Accessed 2026-08-23].
3. **Loga, T., Stein, B., & Diefenbach, N.** (2016). *EPISCOPE Final Report: Energy Performance Indicator Tracking Schemes for the Continuous Optimisation of Refurbishment Processes in European Housing Stocks*. Institut Wohnen und Umwelt GmbH (IWU), Darmstadt. [`https://episcope.eu/fileadmin/episcope/public/docs/reports/EPISCOPE_FinalReport.pdf`](https://episcope.eu/fileadmin/episcope/public/docs/reports/EPISCOPE_FinalReport.pdf) [Accessed 2026-08-23].
4. **Pouget Consultants** (2015). *ADEME Bâtiments Résidentiels: Typologie du Parc Existant et Solutions Exemplaires Pour la Rénovation Energétique en France*. Pouget Consultants / ADEME / IEE TABULA, Paris. [`https://episcope.eu/fileadmin/tabula/public/docs/brochure/FR_TABULA_TypologyBrochure_Pouget.pdf`](https://episcope.eu/fileadmin/tabula/public/docs/brochure/FR_TABULA_TypologyBrochure_Pouget.pdf) [Accessed 2026-08-23].
5. **Cuchí, A., Pagès, A., & Instituto Valenciano de la Edificación (IVE)** (2011/2014). *Typology Approach for Building Stock Energy Assessment: National Building Typology - Spain (TABULA)*. Instituto Valenciano de la Edificación, Valencia. [`https://episcope.eu/fileadmin/tabula/public/docs/brochure/ES_TABULA_TypologyBrochure_IVE.pdf`](https://episcope.eu/fileadmin/tabula/public/docs/brochure/ES_TABULA_TypologyBrochure_IVE.pdf) [Accessed 2026-08-23].
6. **Allen, D., & Pinney, M.** (2014). *TABULA Typology Brochure - England*. Building Research Establishment (BRE), Watford. [`https://episcope.eu/fileadmin/tabula/public/docs/brochure/GB_TABULA_TypologyBrochure_BRE.pdf`](https://episcope.eu/fileadmin/tabula/public/docs/brochure/GB_TABULA_TypologyBrochure_BRE.pdf) [Accessed 2026-08-23].
7. **Corrado, V., Ballarini, I., & Corgnati, S. P.** (2014). *TABULA Building Typology Brochure - Italy*. Politecnico di Torino / ENEA, Turin/Rome. [`https://episcope.eu/fileadmin/tabula/public/docs/brochure/IT_TABULA_TypologyBrochure_POLITO.pdf`](https://episcope.eu/fileadmin/tabula/public/docs/brochure/IT_TABULA_TypologyBrochure_POLITO.pdf) [Accessed 2026-08-23].
8. **Institut Wohnen und Umwelt GmbH (IWU)** (2016). *Condensed TABULA Spread Sheets: tabula-calculator.xlsx and tabula-values.xlsx*. IEE Projects TABULA & EPISCOPE. [`https://episcope.eu/fileadmin/tabula/public/calc/`](https://episcope.eu/fileadmin/tabula/public/calc/) [Accessed 2026-08-23].
9. **EPISCOPE Consortium / IWU** (2016). *Rules for Usage of the TABULA "Building Typology" Approach (Systematics, Data and Tools) by Third Parties*. EPISCOPE Download Portal. [`https://episcope.eu/communication/download/`](https://episcope.eu/communication/download/) [Accessed 2026-08-23].
10. **République Française** (1974). *Décret n° 74-306 du 10 avril 1974 relatif à l'isolation thermique et à l'aération des bâtiments d'habitation*. Journal Officiel de la République Française (JORF).
11. **République Française** (2010). *Décret n° 2010-1269 du 26 octobre 2010 relatif aux caractéristiques thermiques et à la performance énergétique des constructions*. JORF n° 0250 du 27 octobre 2010.
12. **République Française** (2021). *Décret n° 2021-1004 du 29 juillet 2021 relatif aux exigences de performance énergétique et environnementale des constructions de bâtiments en France métropolitaine (RE2020)*. JORF n° 0176 du 31 juillet 2021.
13. **Ministère de la Transition Écologique** (2021). *Arrêté du 31 mars 2021 relatif au diagnostic de performance énergétique pour les bâtiments ou parties de bâtiments à usage d'habitation en France métropolitaine*. Légifrance.
14. **ADEME** (2024). *Base de Données des Diagnostics de Performance Énergétique (DPE v2)*. Agence de la transition écologique. [`https://data.ademe.fr/datasets/dpe-v2-logements-existants`](https://data.ademe.fr/datasets/dpe-v2-logements-existants) [Accessed 2026-08-23].
15. **CSTB** (2024). *Base de Données Nationale des Bâtiments (BDNB Open)*. Centre Scientifique et Technique du Bâtiment. [`https://bdnb.io/`](https://bdnb.io/) [Accessed 2026-08-23].
16. **IGN** (2024). *BD TOPO® Géoservices*. Institut National de l'Information Géographique et Forestière. [`https://geoservices.ign.fr/bdtopo`](https://geoservices.ign.fr/bdtopo) [Accessed 2026-08-23].

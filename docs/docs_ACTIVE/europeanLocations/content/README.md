# European Locations Figure and Table Asset Register

This directory is the reusable source-of-truth for figures and tables cited by the European-locations MVP and walkthrough. A rendered figure must never be treated as simulation evidence unless its caption names the measured dataset and evidence path.

> [!NOTE]
> **Asset storage exception (Ruling 2026-08-23 Q3-B)**: This directory holds authored document assets (design diagrams, illustrative figures, reference schema, test specifications). Generated pipeline figure outputs from simulation runs must continue to be written flat to `openubem/outputs/`.

| Asset ID | File | Caption / purpose | Status |
|---|---|---|---|
| Figure 1 | `figure_1_1_integration_pipeline.mmd` | OpenUBEM–GSSCanada integration and validation flow | Design source |
| Table 1 | `table_2_1_normative_stack.csv` | European normative stack | Design source |
| Table 2 | `table_2_2_country_crosswalk.csv` | Current ES/GB/IT campaign and future FR crosswalk | Design source |
| Table 3 | `table_3_1_typology_taxonomy.csv` | TABULA residential typology taxonomy | Design source |
| Figure 2 | `figure_3_2_imputation_cascade.svg` and `.mmd` | Four-tier imputation cascade with auditable exits | Design source |
| Figure 3 | `figure_4_1_geometry_pipeline.mmd` | Procedural dwelling-layout pipeline | Design source |
| Figure 4 | `figure_4_2_dwelling_layout_schemes.svg` | Point-block and corridor layout schemes | Design source |
| Table 4 | `table_4_8_geometry_verification_matrix.csv` | Geometry and Grasshopper parity verification tasks | Test specification |
| Table 5 | `table_5_1_sensitivity_sweep.csv` | Five occupant-effect levels | Design source |
| Figure 5 | `figure_6_1_eui_accounting.mmd` | Mutually exclusive EUI accounting paths | Design source |
| Table 6 | `table_7_1_gate_summary.csv` | Abbreviated Step 8 gate summary | Test specification |
| Table 7 | `table_9_7_work_packages.csv` | EU-01 through EU-10 implementation work packages | Work-plan source |
| Table 8 | `table_9_7_sample_group_ladder.csv` | Residential-only sample-group qualification ladder | Work-plan source |
| Table 8a | `table_9_7_neighbourhood_selection.csv` | Dense residential neighbourhood selection and four-panel audit gates | Work-plan source |
| Table 9 | `table_9_2_repository_baseline.csv` | Code-audited repository capability baseline | Audit source |
| Table 10 | `table_9_3_frozen_decisions.csv` | Frozen implementation and campaign decisions | Contract source |
| Table 11 | `table_10_2_execution_profiles.csv` | Speed execution profiles | Runbook source |
| Table 12 | `table_10_3_qualification_ladder.csv` | Four-country physical and ES/GB/IT occupant qualification ladder | Runbook source |
| Figure 6 | `figure_neighbourhood_residential_typologies.png` | Illustrative large residential study domain | Illustrative; not measured evidence |
| Reference Figure | `reference_dense_neighbourhood_4panel_audit.png` | Four-panel neighbourhood audit pattern supplied from the Step 8 resources | Methodological reference |
| Figure 7 | `figure_10_6_dependency_chain.mmd` | Q3 control, G8.0 audit, and Q4 dependency chain | Design source |
| Walkthrough Figure 1 | `walkthrough_figure_1_execution_pipeline.mmd` | Six-phase execution flow | Task-guide source |
| Walkthrough Table 1 | `walkthrough_table_7_2_gate_checklist.csv` | Gate audit task template | Status template |
| Walkthrough Table 2 | `walkthrough_table_8_1_error_triage.csv` | EnergyPlus error triage | Operations source |
| Walkthrough Table 3 | `walkthrough_progress_log.csv` | Append-only progress log schema | Status template |

The Markdown documents contain additional implementation-contract tables that are maintained inline because they are read together with surrounding normative language. Any table promoted to a generated campaign artefact must also be exported here (or linked here) in a machine-readable format.

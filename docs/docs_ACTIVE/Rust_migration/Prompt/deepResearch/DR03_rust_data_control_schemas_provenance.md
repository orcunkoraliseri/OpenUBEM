# DR03 — Rust for Strict Data Control, Physical Units, Provenance & Schema Enforcement in Scientific Python Pipelines

**Feeds:** Plan §0, §2 (G2), §3 (Guardrail 5), Phase 1 (T04–T06), and Owner Decision D-RS-03
**Save output to:** `results/DR03_result.md`

---

## PROMPT

You are a senior data-engineering and Rust type-system architect specialising in scientific data pipelines, schema enforcement across Python/Rust boundaries, Apache Arrow, and supply-chain governance. Produce a rigorous, source-cited technical report.

### Context
OpenUBEM is a multi-stage urban energy pipeline (`Step 1` GIS acquisition → `Step 2` semantic enrichment & imputation → `Step 3` IDF generation → `Step 4` EnergyPlus/`gpusim` → `Step 5` carbon accounting & results). Over the project's history, subtle data-control bugs in untyped Python/`pandas` code caused major rework:
1. **Four restatements of the published U.S. fleet EUI (`153.82 → 153.95 → 172.41 → 171.38 → 154.10 kWh/m²` over 8,139 buildings)** caused by DHW double-counting (`D-IMP-05`), cooking/refrigeration double-counting, missed ABUPS district-heating End Uses rows (`OPEN-61`/`OPEN-64`), and inconsistent floor-area denominators (`OPEN-01`: simulated `.eio` area vs `footprint × floors`).
2. **Live delimiter & schema drift:** `data_quality_flag` uses comma `,` in `openubem/acquisition/footprint_schema.py:126` and `openubem/results/aggregator.py:144-148`, but pipe `|` in `openubem/semantic/provenance.py:23,104-110`. Columns silently turn into `NaN` vs `""` vs `None`, requiring late defensive casts (`simulation/parallel.py:220-225`).
3. **Slow row-wise Python validation:** `footprint_schema.py` uses `gdf.iterrows()` / `gdf.apply(axis=1)`; `provenance.py` parses `{METHOD}_{SOURCE}_{TIER}` strings per cell in Python loops; `idf/compliance.py` relies on dynamic `getattr` + string lowering.
4. **Strict provenance & licence rules:** Every input field must carry an auditable provenance token (`observed`, `imputed`, `standard_default`, or `{METHOD}_{SOURCE}_{TIER}`); every output kWh must originate from EnergyPlus or explicitly stamped `gpusim` (`engine` provenance); every dependency must be compatible with `Apache-2.0 OR MIT`.

### Questions
1. **Making scientific invariants unrepresentable at compile time in Rust.** Show concrete Rust patterns (and crates) for OpenUBEM's domain:
   - Dimensional unit newtypes (`AreaM2`, `EnergyJ`, `EnergyKwh`, `EuiKwhM2`, `GwpKgCo2M2`, `UValueWm2K`, `TempCelsius` vs `TempKelvin`) — compare lightweight manual zero-cost newtypes (`#[repr(transparent)]`) vs `uom` / `dimensioned` / `nutype`. Which gives the best compile-time safety without ergonomic friction at PyO3/Arrow boundaries?
   - Exhaustive `enum` ADTs for the 10 OpenUBEM end-uses + 14 ABUPS district-heating fuels, simulation status (`success`, `success_cached`, `failed_fatal`, `failed_crash`, `failed_timeout`, `not_attempted_invalid_idf`), and provenance lineages (`Observed`, `Imputed { method, source, tier }`, `LegacyImputed`, `StandardDefault`).
   - Preventing double-counting by construction (e.g., typed fuel/end-use ledger structs or typestate builders).
2. **Rust-backed validation at the Python boundary (Pydantic v2 vs `openubem-schema`).** How does `pydantic-core` achieve 5–50× validation speedups, and when should a scientific pipeline use (a) Pydantic v2 Python models, (b) a dedicated Rust `openubem-schema` crate validating Arrow/Parquet batches, or (c) **Pandera / Patito / Polars**? Benchmark validation throughput on tabular building records (10k–100k rows × 30–60 columns) vs `pandas` `.apply()`.
3. **Zero-copy Arrow / GeoArrow / Parquet interchange.** Evaluate `arrow-rs` (`arrow`, `parquet`), `pyo3-arrow` / `arro3`, and `geoarrow-rs` for passing Step 1–5 tables between Python (`pyarrow`, `pandas`, `geopandas`) and Rust without serialization overhead. How do nullable integer columns (`Int64`), string/dictionary provenance columns, and `GeoPackage` vs `GeoParquet` schemas behave across the FFI boundary?
4. **Canonical provenance & flag-token normalization.** Design a zero-allocation / `smallvec` Rust token set for `data_quality_flag` that accepts legacy `,` and `|` inputs, deduplicates deterministically, enforces sorted canonical output, and flags unknown/unregistered tokens fail-closed.
5. **Supply-chain & licence control (`cargo-deny`, `cargo-audit`, `proptest`).** Document best practices for enforcing `Apache-2.0 OR MIT` compatibility, blocking copyleft/unknown transitive crates, pinning `Cargo.lock`, and property-based fuzz testing (`proptest` / `bolero`) on parsers and validators.
6. **Recommendation.** A concrete `openubem-schema` crate design and incremental adoption path in OpenUBEM Steps 1, 2, 4, and 5.

### Required output format
- **Executive summary** (≤10 bullets).
- **Table: Rust data-control & Arrow crates**: crate, URL, version, licence, downloads/activity, role in OpenUBEM, caveats.
- **Table: Validation approaches comparison** (`pandas apply` vs Pydantic v2 vs Polars/Patito vs `openubem-schema` + `pyo3-arrow`): throughput, memory, type guarantees, GeoDataFrame support.
- **Code/type design sketch** (concise idiomatic Rust enum/newtype/Arrow schema patterns, not boilerplate).
- Sections answering Q1–Q6.
- **Gaps & negative results**.

### Rules
- Cite every factual claim (URL / DOI / crate version + date). Mark anything uncited `UNVERIFIED`.
- Exclude GPL/AGPL crates. Check transitive dependencies where relevant (e.g., SQLite, OpenSSL, GEOS).
- Search terms to include: "rust newtype pattern physical units uom nutype", "pyo3-arrow arro3 zero copy", "geoarrow-rs geopandas", "pydantic-core rust validation architecture", "cargo-deny apache mit license enforcement", "proptest rust parser fuzzing".

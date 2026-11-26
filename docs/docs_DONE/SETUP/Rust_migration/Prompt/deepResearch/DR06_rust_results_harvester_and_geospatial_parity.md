# DR06 — Parallel Rust Results Harvester (`eplusout.sql`/`.csv`) & Geospatial Parity (`geo`/`geos` vs `shapely` 2.0)

**Feeds:** Plan §4 (R1, R6), Phase 1 (T05–T06), and Phase 5b (T17)
**Save output to:** `results/DR06_result.md`

---

## PROMPT

You are a systems performance and geospatial engineering researcher specialising in high-throughput SQLite/CSV-to-Parquet ingestion in Rust and computational geometry parity between Python (`shapely` 2.0 / GEOS) and Rust (`geo`, `geos`, `rstar`). Produce a rigorous, source-cited evaluation report.

### Context
Two remaining Python subsystems in OpenUBEM process thousands of files or thousands of building polygons:

1. **Results harvesting (`openubem/results/parser.py`, `european_campaign.py`, `aggregator.py`):**
   - `parser.py`: Opens up to 8,139–40,800 `eplusout.sql` databases sequentially in Python (`sqlite3` + `pd.read_sql_query`), queries `ReportData`/`ReportDataDictionary`/`Time`/`TabularDataWithStrings` (including 14 ABUPS District Heating rows + meter closure checks in `check_building_integrity`), resolves simulated floor area from `eplusout.eio`, and computes hourly IOD and EUI.
   - `european_campaign.py:37-89`: Parses each building's `eplusout.csv` **twice** using Python `csv.DictReader` to sum 4 end-use hourly columns across 8,760 rows and validate non-leap calendar counts.
2. **2D Geospatial cleaning & European layout partitioning (`openubem/acquisition/footprint_schema.py`, `openubem/geometry/european_residential.py`, `european_nocore.py`):**
   - `footprint_schema.py::_resolve_overlaps`: Iterates over rows in Python (`gdf.sindex.query`), computing pairwise `a.union(b).area` and `a.intersection(b).area` to deduplicate IoU > 0.95 polygons.
   - `european_residential.py` (3,061 LOC) + `european_nocore.py` (2,608 LOC): Complex Shapely 2.0 (`GEOS` C library) polygon splitting, `buffer(0)`, `minimum_rotated_rectangle`, sliver repair, and morphological sweeps.

### Questions
1. **Parallel Rust SQLite + CSV harvester (`openubem-results`).**
   - How fast can `rusqlite` (with `SQLITE_OPEN_READ_ONLY`, `bundled` SQLite, `PRAGMA mmap_size`, `rayon` thread-per-file over SSD/NVMe and HPC scratch filesystems) + `csv`/`memchr` + `arrow-rs`/`parquet` harvest 10,000–40,000 `eplusout.sql` (typically 0.5–15 MB each) and `eplusout.csv` files compared to Python `sqlite3` + `pandas`?
   - What are the exact filesystem and memory caveats on macOS APFS, Windows NTFS, and HPC Lustre/GPFS scratch (connection pooling vs open-read-close, `mmap` pitfalls on network filesystems, SQLite `WAL` / read-only URI locks on partial crash files)?
2. **Zero-copy Arrow/Parquet output.** Compare returning a single combined `pyarrow.Table` via `pyo3-arrow` vs streaming directly to `05_results.parquet` from Rust (`parquet::arrow::ArrowWriter`).
3. **Geospatial parity: `shapely` 2.0 (C GEOS) vs Rust `geo` vs Rust `geos` crate.**
   - Since `shapely` 2.0 already runs vectorised GEOS C loops (and `pyogrio` uses GDAL/OGR C++), **when does moving geometry to Rust actually win vs lose?**
   - Compare pure-Rust `geo` (`0.28+`) polygon `BooleanOps` (union/intersection/split), `buffer` / offset (note: does `geo` have full GEOS-grade polygon buffering & `make_valid` yet?), and robustness on degenerate self-intersecting OSM footprints against `shapely` 2.0 / `GEOS`.
   - Check the **licensing trap** of the `geos` Rust crate (wrapper around C/C++ `libgeos`, which is **LGPL-2.1-or-later**): what are the static vs dynamic linking implications for OpenUBEM's `Apache-2.0 OR MIT` licence and `maturin` wheel bundling (`auditwheel`/`delocate`)?
4. **Targeted win for `_resolve_overlaps` & `discover_context`.** Can `rstar` + `geo`/`i_overlay` replace just the Python `iterrows()`/`sindex` loop in `footprint_schema.py` and `geometry/context.py` without touching the 5,669 LOC of `european_*.py`? What precision differences exist vs GEOS?
5. **Recommendation.** Clear go/no-go criteria for `openubem-results` (Phase 1) and `R6` geospatial work (Phase 5b).

### Required output format
- **Executive summary** (≤10 bullets).
- **Table: SQLite/CSV/Parquet Rust crates** (`rusqlite`, `sqlx`, `csv`, `memchr`, `arrow`, `parquet`, `polars`): version, licence, bundled C deps, performance notes.
- **Table: `shapely` 2.0 vs Rust `geo` vs `i_overlay` vs `geos` crate** across: Boolean ops, `buffer`, `is_valid`/`make_valid`, `minimum_rotated_rectangle`, `R-tree`, robustness on degenerate OSM polygons, and `Apache-2.0 OR MIT` wheel-bundling safety.
- Sections answering Q1–Q5.
- **Gaps & negative results**.

### Rules
- Cite every factual claim (URL / DOI / crate release + date). Mark anything uncited `UNVERIFIED`.
- Pay special attention to LGPL/GPL linking rules when distributing binary wheels via `maturin` (`delocate`, `auditwheel`, `delvewheel`).
- Search terms to include: "rusqlite rayon read only benchmark", "rust geo crate buffer make_valid booleanops robustness", "geos crate LGPL wheel bundling auditwheel", "shapely 2.0 vs rust geo performance", "pyo3-arrow parquet streaming rust".

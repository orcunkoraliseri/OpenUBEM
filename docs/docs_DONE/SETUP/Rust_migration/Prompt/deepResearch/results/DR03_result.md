# DR03 Result — Rust for Strict Data Control, Physical Units, Provenance & Schema Enforcement in OpenUBEM

**Feeds:** [`PLAN_rust_migration.md`](../../../PLAN_rust_migration.md) §0, §2 (G2), §3 (Guardrail 5), Phase 1 (T04–T06), and Owner Decision D-RS-03  
**Date:** 2026-11-26  
**Project Licence Policy:** `Apache-2.0 OR MIT` ([`pyproject.toml`](../../../../../../pyproject.toml), [`PLAN_rust_migration.md`](../../../PLAN_rust_migration.md))

---

## Executive Summary

1. **Use `#[repr(transparent)]` manual unit newtypes + `nutype` for validated scalars — avoid `uom` and `dimensioned` at FFI/Arrow boundaries.** `uom` (`0.38.0`, Feb 2026, `Apache-2.0 OR MIT`) causes compile-time bloat and verbose `ISQ<...>` type errors across `serde`, `pyo3`, and `arrow-rs` (`Vec<Length<f64>>` cannot zero-copy wrap into `Float64Array`); `dimensioned` (`0.8.0`, Apr 2022) is effectively stale (4+ years without a release). Thin `#[repr(transparent)]` newtypes (`AreaM2`, `EnergyJ`, `EnergyKwh`, `EuiKwhM2`, `GwpKgCo2M2`, `UValueWm2K`, `TempCelsius`, `TempKelvin`) plus `nutype` (`0.8.0`, `MIT`) for `finite` / non-negative bounds give zero-cost compile-time safety and trivial `bytemuck`/`arrow-rs` buffer interop.
2. **Make OpenUBEM's historical accounting bugs unrepresentable via exhaustive ADTs and typestate ledgers.** Encoding the 10 end-uses, 14 ABUPS district-heating rows (`parser.py:66-81`), explicit `FuelSplit` structs (gas/electric/district), `ResolvedFloorArea` (`EioSimulated` vs `FootprintTimesFloors`), and `SimulationStatus` as closed Rust `enum`s eliminates DHW/cooking/refrigeration double-counting (`D-IMP-05`), missed ABUPS rows (`OPEN-61`/`OPEN-64`), and floor-area denominator mismatches (`OPEN-01`) at compile time.
3. **Skip Python-row Pydantic v2 for 10k–100k building tables; validate columnar Arrow batches in `openubem-schema`.** `pydantic-core` achieves its official 4×–50× (~17× typical) speedups over Pydantic v1 by walking raw UTF-8 JSON/PyObjects in Rust without Python frame overhead, making it ideal for small config/manifest JSON—not 100k × 60-column tables where instantiating Python `BaseModel` rows bottlenecks. Columnar validation over Arrow buffers (`openubem-schema` via `pyo3-arrow`, or Polars/Patito/Pandera) operates at millisecond scale for 100k rows.
4. **Adopt `arrow-rs` (`arrow` `60.2.0`, `parquet` `60.1.0`) + `pyo3-arrow` (`0.21.0`) via the Arrow PyCapsule Interface (`__arrow_c_array__` / `__arrow_c_stream__`).** This passes nullable `Int64`, `Float64`, `Utf8`/`LargeUtf8`, and `DictionaryArray` provenance columns zero-copy between Rust and `pyarrow`/`pandas >= 2.2` (`ArrowDtype`), eliminating `iterrows()`/`apply(axis=1)` in `footprint_schema.py:64,97,127`.
5. **Keep GeoPackage (`.gpkg`) at Python ingress via `pyogrio(..., use_arrow=True)` and standardize internal Step 1–5 interchange on GeoParquet 1.1 + `geoarrow-rs` (`0.9.0`).** `geopandas` relies on Shapely/GEOS (`LGPL-2.1`), so `openubem-schema` should validate attribute/provenance Arrow columns in Rust and pass geometry buffers via `geoarrow` (`Apache-2.0 OR MIT`) without linking `geos-sys`.
6. **Unify `data_quality_flag` in a `smallvec` (`1.16.6`, `MIT OR Apache-2.0`) canonical token set (`D-RS-03`).** Parsing both legacy `,` (`footprint_schema.py:126`, `aggregator.py:144-148`) and `|` (`provenance.py:23`) delimiters into a stack-allocated `SmallVec<[QualityFlag; 8]>`, deduplicating, sorting deterministically, and rejecting unknown tokens fail-closed stops silent delimiter drift.
7. **Enforce `Apache-2.0 OR MIT` supply-chain hygiene via `cargo-deny` + `cargo-audit` (`0.23.0`) + `proptest` (`1.12.0`).** `deny.toml` must block `GPL-*`, `AGPL-*`, `LGPL-*` (preventing `geos-sys`), and `OpenSSL` (`openssl-sys`), while quarantining `libsqlite3-sys` (`Unlicense`/SQLite blessing) strictly to `openubem-results` rather than `openubem-schema`.
8. **Roll out incrementally behind `OPENUBEM_RUST_BACKEND = "off" | "shadow" | "on"`.** Start with pure-Rust `openubem-schema` (zero `pyo3` deps) + `crates/openubem-py`, shadow-validating Step 1 (`footprint_schema.py`), Step 2 (`provenance.py`), Step 4 (`parallel.py`), and Step 5 (`parser.py`/`carbon.py`/`aggregator.py`) with 0 unexplained mismatches before flipping `"on"`.

---

## Table 1: Rust Data-Control & Arrow Crates

*(Versions, licences, and activity verified via crates.io / docs.rs / GitHub search as of late 2026; exact crates.io download counters not directly returned by search snippets are marked `UNVERIFIED`.)*

| Crate | URL | Version | Licence | Downloads / Activity | Role in OpenUBEM | Caveats |
|---|---|---|---|---|---|---|
| `arrow` (`arrow-rs`) | [crates.io/crates/arrow](https://crates.io/crates/arrow) | `60.2.0` | `Apache-2.0` | Active (rapid SemVer cadence in `apache/arrow-rs`); exact count `UNVERIFIED` | Columnar memory format (`Int64Array`, `Float64Array`, `StringArray`, `DictionaryArray`) for Step 1–5 tables | `pa.Table.from_pandas` often emits `LargeUtf8` (64-bit offsets) vs `Utf8` (32-bit); Rust must handle both or normalize via cast |
| `parquet` (`arrow-rs`) | [crates.io/crates/parquet](https://crates.io/crates/parquet) | `60.1.0` | `Apache-2.0` | Active (synchronized with `arrow-rs`); exact count `UNVERIFIED` | Direct Parquet/GeoParquet reading & writing in `openubem-schema` / `openubem-results` | Requires `zstd`/`snappy` feature selection; check transitive compression crate licences |
| `pyo3` | [crates.io/crates/pyo3](https://crates.io/crates/pyo3) | `0.30.1` | `MIT OR Apache-2.0` | Active ecosystem standard; exact count `UNVERIFIED` | Python C-API FFI bindings strictly isolated inside `crates/openubem-py` | `abi3-py310` wheels constrain some newer Python APIs; never depend on `pyo3` in core `openubem-schema` |
| `pyo3-arrow` | [crates.io/crates/pyo3-arrow](https://crates.io/crates/pyo3-arrow) | `0.21.0` | `MIT OR Apache-2.0` | Active (`kylebarron/arro3` monorepo); exact count `UNVERIFIED` | Zero-copy Arrow PyCapsule FFI (`PyArray`, `PyTable`, `PyRecordBatchReader`) between Rust and `pyarrow`/`pandas` | Tracks `arrow-rs` major versions closely; expects Arrow-backed or PyCapsule-exporting objects |
| `geoarrow` | [crates.io/crates/geoarrow](https://crates.io/crates/geoarrow) | `0.9.0` | `MIT OR Apache-2.0` | Active (`geoarrow/geoarrow-rs`); exact count `UNVERIFIED` | Pure-Rust GeoArrow geometry array layouts (`PolygonArray`) without GEOS | Converting back to Shapely-backed `GeoDataFrame` incurs Python geometry instantiation cost unless staying in Arrow |
| `geoparquet` | [crates.io/crates/geoparquet](https://crates.io/crates/geoparquet) | `0.9.0` | `MIT OR Apache-2.0` | Active (`geoarrow/geoarrow-rs`); exact count `UNVERIFIED` | GeoParquet 1.0/1.1 `geo` footer metadata + PROJJSON CRS + bbox handling | GeoPackage (`.gpkg`) is not supported natively here; keep `.gpkg` ingress in Python `pyogrio` |
| `nutype` | [crates.io/crates/nutype](https://crates.io/crates/nutype) | `0.8.0` | `MIT` | Millions of all-time downloads (>2M recent) | Macro-enforced scalar invariants (`finite`, `greater_or_equal = 0.0`, normalized strings) deriving `Eq`/`Ord` on `f64` | Proc-macro compile cost; does not prevent dimensional cross-unit arithmetic alone (pair with distinct unit structs) |
| `uom` | [crates.io/crates/uom](https://crates.io/crates/uom) | `0.38.0` | `Apache-2.0 OR MIT` | Active (Feb 2026 release); exact count `UNVERIFIED` | **Evaluated & rejected for schema boundary**: SI dimensional analysis (`ISQ<...>`) | Heavy macro compile times, unreadable nested type errors, and `Vec<Length<f64>>` cannot zero-copy wrap into `Float64Array` |
| `dimensioned` | [crates.io/crates/dimensioned](https://crates.io/crates/dimensioned) | `0.8.0` | `MIT OR Apache-2.0` | **Stale** (last release Apr 2022) | **Rejected**: compile-time dimensional analysis | Inactive 4+ years; less ergonomic than manual `#[repr(transparent)]` newtypes |
| `smallvec` | [crates.io/crates/smallvec](https://crates.io/crates/smallvec) | `1.16.6` | `MIT OR Apache-2.0` | ~1.5B all-time / >406M recent downloads | Stack-allocated `SmallVec<[QualityFlag; 8]>` for zero-heap `data_quality_flag` token normalization | Spills to heap only if a building exceeds inline capacity (`>8` flags); `2.0.0` still in pre-release |
| `serde` | [crates.io/crates/serde](https://crates.io/crates/serde) | `1.0.229` | `MIT OR Apache-2.0` | Active Rust standard; exact count `UNVERIFIED` | JSON schema manifests, `01_buildings_clean.schema.json`, `gpusim_provenance.json` | Pair with `#[serde(deny_unknown_fields)]` for fail-closed manifest parsing |
| `thiserror` | [crates.io/crates/thiserror](https://crates.io/crates/thiserror) | `2.0.21` | `MIT OR Apache-2.0` | Active Rust standard; exact count `UNVERIFIED` | Typed validation/unit/provenance error enums mapped cleanly to Python `ValueError` | No runtime caveats |
| `bytemuck` | [crates.io/crates/bytemuck](https://crates.io/crates/bytemuck) | `1.25.2` | `Zlib OR Apache-2.0 OR MIT` | Active; exact count `UNVERIFIED` | Zero-copy `&[AreaM2]` ↔ `&[f64]` slice casting for `#[repr(transparent)]` newtypes | **Bypass hazard**: `Pod` allows bit-casting raw floats without running invariant constructors—do NOT derive `Pod` on strictly validated `nutype` non-negative/finite types unless checked |
| `proptest` | [crates.io/crates/proptest](https://crates.io/crates/proptest) | `1.12.0` | `MIT OR Apache-2.0` | Tens of millions of downloads; active | Property-based testing + shrinking on flag/token parsers, unit conversions, and Arrow roundtrips | Slow if generating huge strings; pair with `bolero` for coverage-guided fuzzing |
| `bolero` | [crates.io/crates/bolero](https://crates.io/crates/bolero) | `0.13.x` | `MIT` | Hundreds of thousands/month; active | Unified fuzz harness (`libFuzzer`/`AFL`/`kani`/proptest backends) for untrusted CSV/flag/IDF strings | Coverage-guided `libFuzzer` mode requires Linux/macOS fuzzing toolchain in CI |
| `cargo-deny` | [crates.io/crates/cargo-deny](https://crates.io/crates/cargo-deny) | Active (exact patch `UNVERIFIED`) | `MIT OR Apache-2.0` | Active (`EmbarkStudios/cargo-deny`) | CI enforcement of `Apache-2.0 OR MIT` compatibility, blocking GPL/LGPL/OpenSSL/unknown transitive crates | SQLite "blessing" (`libsqlite3-sys`) needs explicit policy isolation; native `-sys` crates may trigger `askalono` low-confidence warnings |
| `cargo-audit` | [crates.io/crates/cargo-audit](https://crates.io/crates/cargo-audit) | `0.23.0` | `Apache-2.0 OR MIT` | Active (`rustsec/rustsec`) | Audits `Cargo.lock` against RustSec vulnerability advisories | Checks Rust crates only; Python deps still need `pip-audit` / `uv` checks |

---

## Table 2: Validation Approaches Comparison (Tabular Building Records: 10k–100k rows × 30–60 cols)

*(Note: No single published benchmark tests all four engines on identical 10k–100k × 30–60 column geospatial building tables; measured baselines below cite published sources, while OpenUBEM-specific 100k-row figures for `openubem-schema` are marked `PROJECTED / UNVERIFIED` until Phase 1 T06 profiling.)*

| Approach | Throughput | Memory Footprint | Type & Invariant Guarantees | GeoDataFrame / GeoParquet Support | Fit for OpenUBEM |
|---|---|---|---|---|---|
| **`pandas` `.apply(axis=1)` / `iterrows()`** *(current `footprint_schema.py:64,97,127`)* | **Slowest.** Seconds to tens of seconds at 100k rows due to Python interpreter frames and per-row `pd.Series` allocation ([source](https://www.pythonalchemist.com/) / search summary). | High: allocates a `pd.Series` per row + Python `object` string/Shapely pointers. | Weak runtime checks only (`str(dtype) == "Int64"`, ad-hoc lambdas); allows `NaN` vs `""` vs `None` drift (`simulation/parallel.py:220-225`). | Native (`GeoDataFrame`), but row loops force Python-level geometry attribute access. | **Replace in Step 1–5 hot paths.** |
| **Pydantic v2 (`pydantic-core` in Rust)** | **4×–50× faster (~17× typical) than Pydantic v1** on Python dicts/JSON ([pydantic.dev](https://pydantic.dev/)); ~1.3M item validations in ~6 s (~217k/s) in published bulk benchmarks. Still bottlenecked by Python object instantiation on 100k DataFrame rows. | High for full tables: materializes 100k Python `BaseModel` instances + dicts if used row-wise. | Strong runtime validation (`finite`, enums, `model_validate_json`), but **no compile-time Rust unit/ledger checks** across pipeline stages. | None natively; geometries must be serialized to WKB/GeoJSON or skipped. | **Use only for small JSON configs/manifests** (e.g., `egrid_2022.json`, `gpusim_provenance.json`), **not** DataFrame columns. |
| **Polars / Patito / `pandera.polars`** | **Milliseconds at 100k rows** (~40–150 ms reported for 1M-row Polars-backed checks depending on constraint complexity; sub-100 ms at 100k rows; 100k×60 exact OpenUBEM case `UNVERIFIED`). | Low: Apache Arrow columnar buffers; multi-threaded Rust expressions; lazy pushdown (`LazyFrame`). | Columnar dtype/range/regex checks at runtime; Patito bridges Pydantic syntax to Polars, but **lacks Rust compile-time ADTs/unit types** for internal Rust kernels (`openubem-results`, `openubem-idf`). | Weak: Polars has no native GeoParquet/GeoArrow CRS support without external plugins (`polars-st`), forcing Pandas/GeoPandas conversions. | Good pure-Python alternative if staying in Python, but duplicates schema logic once `openubem-results`/`openubem-idf` run in Rust. |
| **`openubem-schema` + `pyo3-arrow` (Recommended)** | **PROJECTED: <10–50 ms for 100k × 60 cols (`UNVERIFIED` until T06)** — single-pass GIL-released (`py.allow_threads`) Rust columnar scan + `rayon` over Arrow buffers. | Lowest: **zero-copy** Arrow PyCapsule buffer sharing with `pyarrow` / `pandas ArrowDtype` / `geoarrow-rs` (`0.9.0`). | **Strongest:** Compile-time Rust `#[repr(transparent)]` unit newtypes, exhaustive end-use/ABUPS/status ADTs, typestate double-count prevention, fail-closed token grammar. | Native GeoParquet 1.1 & GeoArrow via `geoarrow` (`0.9.0`) + `geoparquet` (`0.9.0`); `.gpkg` bridged via `pyogrio(use_arrow=True)`. | **Best fit:** Single source of truth shared across Step 1–5 Python boundary AND Phase 1–5 Rust crates. |

---

## Code / Type Design Sketch (`crates/openubem-schema/src/`)

```rust
use nutype::nutype;
use serde::{Deserialize, Serialize};
use smallvec::SmallVec;
use std::collections::BTreeMap;
use thiserror::Error;

// ── 1. Zero-Cost Physical Unit Newtypes & Scalar Invariants ──────────────────
// Manual #[repr(transparent)] for pure arithmetic & Arrow buffer compatibility;
// nutype for validated domain scalars (finite, non-negative, total Eq/Ord).
#[nutype(
    validate(finite, greater_or_equal = 0.0),
    derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)
)]
pub struct AreaM2(f64);

#[repr(transparent)]
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Serialize, Deserialize)]
pub struct EnergyJ(pub f64);

#[repr(transparent)]
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Serialize, Deserialize)]
pub struct EnergyKwh(pub f64);

#[repr(transparent)]
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Serialize, Deserialize)]
pub struct EuiKwhM2(pub f64);

#[repr(transparent)]
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Serialize, Deserialize)]
pub struct GwpKgCo2M2(pub f64);

#[repr(transparent)]
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Serialize, Deserialize)]
pub struct UValueWm2K(pub f64);

#[repr(transparent)]
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Serialize, Deserialize)]
pub struct TempCelsius(pub f64);

#[repr(transparent)]
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Serialize, Deserialize)]
pub struct TempKelvin(pub f64);

impl EnergyJ {
    pub const fn to_kwh(self) -> EnergyKwh { EnergyKwh(self.0 / 3_600_000.0) }
}
impl EnergyKwh {
    pub fn per_area(self, area: AreaM2) -> Result<EuiKwhM2, SchemaError> {
        let a = area.into_inner();
        if a <= 0.0 { return Err(SchemaError::NonPositiveFloorArea(a)); }
        Ok(EuiKwhM2(self.0 / a))
    }
}
impl TempCelsius {
    pub const fn to_kelvin(self) -> TempKelvin { TempKelvin(self.0 + 273.15) }
}

// ── 2. Exhaustive Domain ADTs (10 End-Uses, 14 ABUPS DH Rows, Status, Prov) ──
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub enum EndUse {
    Heating, Cooling, InteriorLighting, InteriorEquipment,
    Fans, Pumps, WaterSystems, Cooking, Refrigeration, Elevators,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub enum AbupsDistrictRow {
    Heating, Cooling, InteriorLighting, ExteriorLighting, InteriorEquipment,
    ExteriorEquipment, Fans, Pumps, HeatRejection, Humidification,
    HeatRecovery, WaterSystems, Refrigeration, Generators,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SimulationStatus {
    Success, SuccessCached, SuccessCsvFallback,
    FailedFatal, FailedCrash, FailedTimeout, NotAttemptedInvalidIdf, NotSimulated,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum ConfidenceTier { High, Medium, Low }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LegacyProvenance { AshraeStandard, Heuristic, KdeImputed, PdeGenerated }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ProvenanceLineage {
    Observed { source: String }, // e.g., OSM_OBSERVED, OSM_OBSERVED_FT
    Imputed { method: String, source: String, tier: ConfidenceTier },
    LegacyImputed(LegacyProvenance),
    StandardDefault { source: String },
    Missing { source: String },
}

// ── 3. Double-Count-Proof End-Use Ledger + Floor Area Provenance (OPEN-01/46/61/64) ──
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FloorAreaProvenance { EioSimulated, FootprintTimesFloors }

#[derive(Debug, Clone, Copy)]
pub struct ResolvedFloorArea { pub area: AreaM2, pub provenance: FloorAreaProvenance }

#[derive(Debug, Clone, Copy, Default)]
pub struct FuelSplitKwh { pub gas: f64, pub elec: f64, pub district: f64 }

impl FuelSplitKwh {
    pub fn total(self) -> EnergyKwh { EnergyKwh(self.gas + self.elec + self.district) }
    pub fn validate_non_negative(&self) -> Result<(), SchemaError> {
        if self.gas < 0.0 || self.elec < 0.0 || self.district < 0.0 {
            return Err(SchemaError::NegativeMeter);
        }
        Ok(())
    }
}

pub struct RawMeters;
pub struct ReconciledLedger;

pub struct EndUseLedger<State> {
    floor_area: ResolvedFloorArea,
    core: [FuelSplitKwh; 10],         // Indexed by EndUse as usize (fixed 10 slots: no duplicate keys)
    pure_district: [f64; 6],          // ExteriorLighting, ExteriorEquipment, HeatRejection, Humidification, HeatRecovery, Generators
    _state: std::marker::PhantomData<State>,
}

impl EndUseLedger<RawMeters> {
    /// De-folds elevators out of InteriorEquipment once (OPEN-46) and maps all 14 ABUPS rows (OPEN-64).
    pub fn reconcile(mut self, elevator_elec_kwh: f64) -> Result<EndUseLedger<ReconciledLedger>, SchemaError> {
        let equip_idx = EndUse::InteriorEquipment as usize;
        let elev_idx = EndUse::Elevators as usize;
        if elevator_elec_kwh > 0.0 {
            self.core[equip_idx].elec = (self.core[equip_idx].elec - elevator_elec_kwh).max(0.0);
            self.core[elev_idx].elec = elevator_elec_kwh;
        }
        for split in &self.core { split.validate_non_negative()?; }
        Ok(EndUseLedger { floor_area: self.floor_area, core: self.core, pure_district: self.pure_district, _state: std::marker::PhantomData })
    }
}

// ── 4. Zero-Heap Canonical Quality Flag Set (smallvec) ───────────────────────
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(u8)]
pub enum QualityFlag {
    NoFloors, NoHeight, GenericTag, NoFunction, OverlapResolved, HeightOnlyFt, NoBuildingTag, NoYear,
    // ... closed canonical vocabulary; unknown strings fail closed
}

#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct QualityFlagSet(SmallVec<[QualityFlag; 8]>); // Inline on stack up to 8 flags

impl QualityFlagSet {
    pub fn parse_legacy(input: &str) -> Result<Self, SchemaError> {
        let mut flags: SmallVec<[QualityFlag; 8]> = SmallVec::new();
        for raw in input.split(|c| c == ',' || c == '|') {
            let tok = raw.trim();
            if tok.is_empty() { continue; }
            let flag = QualityFlag::parse_strict(tok)?; // Fails closed on unregistered tokens
            flags.push(flag);
        }
        flags.sort_unstable();
        flags.dedup();
        Ok(Self(flags))
    }
}

#[derive(Debug, Error)]
pub enum SchemaError {
    #[error("non-positive floor area: {0}")] NonPositiveFloorArea(f64),
    #[error("negative meter reading")] NegativeMeter,
    #[error("unregistered data_quality_flag token: {0}")] UnknownFlagToken(String),
}
```

---

## Q1. Making Scientific Invariants Unrepresentable at Compile Time in Rust

### 1.1 Physical Unit Newtypes: Manual `#[repr(transparent)]` vs `uom` vs `dimensioned` vs `nutype`
OpenUBEM's bugs stem from confusing quantities (`J` vs `kWh`, `kWh/m²` vs `kWh`, simulated `.eio` floor area vs `footprint × floors`, Celsius vs Kelvin in thermal/UTCI equations). Four Rust approaches address this:

- **Manual `#[repr(transparent)]` newtypes (Recommended primary pattern):** Wrapping `f64` in `#[repr(transparent)] pub struct EnergyKwh(pub f64);` guarantees identical ABI, size, and alignment to `f64` ([Rust Reference — Type Layout](https://doc.rust-lang.org/reference/type-layout.html)). You implement only physically meaningful operations (`EnergyJ::to_kwh()`, `EnergyKwh::per_area(AreaM2) -> Result<EuiKwhM2, _>`, `TempCelsius::to_kelvin()`), preventing `AreaM2 + EnergyKwh` or accidental double-division by `AreaM2`. Because `#[repr(transparent)]` has zero runtime wrapper cost, slices and buffers map cleanly across `arrow-rs` (`Float64Array`) and `pyo3`.
- **`nutype` (`0.8.0`, `MIT`):** Procedural macro generating validated newtypes with `try_new()` constructors, sanitization, and `serde` enforcement ([crates.io/crates/nutype](https://crates.io/crates/nutype)). Crucially for floating-point invariants, `validate(finite, greater_or_equal = 0.0)` rules out `NaN` and `±Inf`, unlocking safe `Eq` and `Ord` derivation on `f64` ([greyblake/nutype](https://github.com/greyblake/nutype)). Ideal for bounded scalars (`AreaM2`, `UValueWm2K`, non-empty `OsmId`). Pair with `FromPyObject`/`IntoPyObject` in `openubem-py` so `NaN`/negative areas fail immediately at the Python boundary with `PyValueError`.
- **`uom` (`0.38.0`, Feb 2026, `Apache-2.0 OR MIT`):** Full compile-time SI dimensional analysis using typenum-encoded `ISQ<...>` dimensions ([crates.io/crates/uom](https://crates.io/crates/uom)). While powerful inside standalone physics kernels, **`uom` creates severe friction at `serde`, `pyo3`, and `arrow-rs` boundaries**: macro expansion inflates compile times, compiler errors dump multi-line `ISQ<P1, Z0, ...>` signatures, `uom` types are foreign types requiring newtype wrappers for custom serialization, and `arrow-rs` cannot construct a zero-copy `Float64Array` directly from `Vec<Length<f64>>` without unpacking (`lengths.iter().map(|l| l.value).collect()`), stripping unit safety at the boundary anyway.
- **`dimensioned` (`0.8.0`, Apr 2022, `MIT OR Apache-2.0`):** Type-level dimensional analysis similar to `uom` ([crates.io/crates/dimensioned](https://crates.io/crates/dimensioned)), **flagged inactive (>4 years since last release in Apr 2022)**. Not recommended for new OpenUBEM infrastructure.

**Verdict:** Use **manual `#[repr(transparent)]` newtypes** for unit algebra (`EnergyJ`, `EnergyKwh`, `EuiKwhM2`, `GwpKgCo2M2`, `UValueWm2K`, `TempCelsius`, `TempKelvin`) and **`nutype`** (`finite` / domain bounds) for validated boundary scalars (`AreaM2`, `ConfidenceWeight`). Note a subtle caveat if using `bytemuck` (`1.25.2`): never derive `bytemuck::Pod` on `nutype` invariant types because arbitrary byte reinterpretation would bypass `try_new()` checks.

### 1.2 Exhaustive `enum` ADTs for OpenUBEM's Closed Vocabularies
Inspecting OpenUBEM's Python code reveals four closed vocabularies currently represented as raw strings:
1. **10 OpenUBEM End-Uses** ([`openubem/results/aggregator.py:29-44`](../../../../../../openubem/results/aggregator.py#L29-L44), [`openubem/results/parser.py:48-55`](../../../../../../openubem/results/parser.py#L48-L55)): `Heating`, `Cooling`, `InteriorLighting`, `InteriorEquipment`, `Fans`, `Pumps`, `WaterSystems` (DHW), `Cooking` (`InteriorEquipment:NaturalGas`), `Refrigeration`, `Elevators` (`Elevators:InteriorEquipment:Electricity`, `OPEN-46 T05`).
2. **14 ABUPS District-Heating End Uses rows** ([`openubem/results/parser.py:66-81`](../../../../../../openubem/results/parser.py#L66-L81)): 8 rows split existing end-uses (`Heating`, `Cooling`, `Interior Lighting`, `Interior Equipment`, `Fans`, `Pumps`, `Water Systems`, `Refrigeration`), and 6 rows are pure-district (`Exterior Lighting`, `Exterior Equipment`, `Heat Rejection`, `Humidification`, `Heat Recovery`, `Generators`, [`openubem/results/carbon.py:114-122`](../../../../../../openubem/results/carbon.py#L114-L122)).
3. **Simulation & Generation Statuses** ([`openubem/simulation/runner.py:105-161`](../../../../../../openubem/simulation/runner.py#L105-L161), [`parallel.py:141,206,244`](../../../../../../openubem/simulation/parallel.py#L141-L244), [`aggregator.py:67,130`](../../../../../../openubem/results/aggregator.py#L67-L130)): `Success`, `SuccessCached`, `SuccessCsvFallback`, `FailedFatal`, `FailedCrash`, `FailedTimeout`, `NotAttemptedInvalidIdf`, `NotSimulated`. Notice that in Rust, an exhaustive `match` on `SimulationStatus` forces every downstream consumer (like `is_success()` or aggregator filtering) to handle `SuccessCsvFallback` vs `FailedFatal` explicitly rather than relying on duplicated `_SUCCESS_STATUSES` sets across 4 Python files (`aggregator.py:67`, `__init__.py:133`, `visualization.py:16`, `plotting_suite.py:42`).
4. **Provenance Lineages** ([`openubem/semantic/provenance.py:27-55`](../../../../../../openubem/semantic/provenance.py#L27-L55), [`openubem/acquisition/footprint_schema.py:92-110`](../../../../../../openubem/acquisition/footprint_schema.py#L92-L110)): An algebraic `ProvenanceLineage` enum separates `Observed` (weight `1.0`), `Imputed { method, source, tier }` (`HIGH=1.0`, `MED=0.5`, `LOW=0.1`), `LegacyImputed` (`KDE_IMPUTED=0.5`, `HEURISTIC=0.5`, `PDE_GENERATED=0.1`, `ASHRAE_STANDARD=0.1` — preventing the `T07.1` regression where legacy tokens fell through to observed `1.0`), `StandardDefault`, and `Missing`. Plus an explicit `EngineProvenance` enum (`EnergyPlus { version }`, `GpuSim { kernel }`) ensures every output kWh carries simulation engine lineage.

### 1.3 Preventing Double-Counting by Construction (Typestate & Fixed-Slot Ledgers)
Why did OpenUBEM suffer four U.S. fleet EUI restatements (`153.82 → 153.95 → 172.41 → 171.38 → 154.10 kWh/m²`)? Because Python stored loose `dict[str, float]` meters and overlapping summary columns (`dhw_eui` alongside `dhw_gas_eui` + `dhw_elec_eui` + `dhw_district_eui`; `equipment_eui` overlapping `elevators_eui`; `heating_eui` overlapping `heating_district_eui`).

In Rust:
- **Fixed-slot `[FuelSplitKwh; 10]` array indexed by `EndUse as usize`**: A building can have **at most one** `FuelSplitKwh { gas, elec, district }` per `EndUse`. You cannot accidentally add DHW twice (`D-IMP-05`) or forget one of the 14 ABUPS rows (`OPEN-64`), because `AbupsDistrictRow` maps exhaustively via `match` into either `core[EndUse].district` (the 8 overlapping rows) or `pure_district[...]` (the 6 pure-district rows).
- **Computed totals, never stored totals**: `total_eui_kwh_m2` and `dhw_eui_kwh_m2` are pure methods (`ledger.total_kwh()`, `split.total()`), never independently mutable fields that can go out of sync with their components.
- **Typestate `EndUseLedger<RawMeters>` → `EndUseLedger<ReconciledLedger>`**: Only `EndUseLedger<ReconciledLedger>` exposes `.to_eui()` and `.compute_gwp(&CarbonFactors)`. Moving from `RawMeters` to `ReconciledLedger` consumes `self` by value, performs the `OPEN-46` elevator de-folding (`InteriorEquipment.elec -= Elevators.elec`) **exactly once**, and validates non-negativity. Calling de-folding twice is a compile error.
- **Denominator lock (`ResolvedFloorArea`)**: `EndUseLedger` binds a single `ResolvedFloorArea { area: AreaM2, provenance: FloorAreaProvenance }` at construction (`OPEN-01`), so Step 5 `aggregator.py` cannot silently divide one end-use by `.eio` area and another by `footprint × floors`.

---

## Q2. Rust-Backed Validation at the Python Boundary (`pydantic-core` vs `openubem-schema` vs Pandera/Patito/Polars)

### 2.1 How `pydantic-core` Achieves 4×–50× Speedups
Pydantic v2 (`pydantic-core`, built with **PyO3** and **maturin**) separates the Python DSL (`pydantic`) from the compiled Rust validation engine (`pydantic-core`) ([pydantic.dev](https://pydantic.dev/), [thedataquarry.com](https://thedataquarry.com/)). It achieves **4×–50× speedups (~17× average on typical models)** over Pydantic v1 via four mechanisms:
1. **Single-pass UTF-8 JSON parsing (`model_validate_json`):** Parses raw JSON bytes and validates constraints concurrently in Rust without calling Python's `json.loads()` or allocating intermediate Python `dict`/`list` graphs.
2. **Flattened Rust validator plan:** Compiles schema definitions upfront into a static tree/array of Rust enum match arms (`SchemaValidator`), eliminating recursive Python stack-frame allocations per field.
3. **Direct CPython C-API pointer walking:** PyO3 inspects `PyDict`, `PyString`, and `PyFloat` pointers without copying primitives until final model construction, offloading hot parsing (like ISO-8601 dates via `speedate`) to Rust crates.
4. **Reduced GC pressure:** Scratch buffers and validation errors stay in Rust memory rather than triggering Python object allocations on every check.

### 2.2 When to Use Pydantic v2 vs `openubem-schema` vs Pandera/Patito/Polars
- **Pydantic v2 (`BaseModel`):** Optimal for **small nested payloads, configs, and JSON manifests** (`egrid_2022.json`, `01_buildings_clean.schema.json`, `SimTask` batch specs). **Anti-pattern for 10k–100k building tables:** validating 100k rows × 60 columns through Pydantic `BaseModel` requires boxing 6M scalar cells into Python dicts/objects and instantiating 100k Python class instances—losing the columnar advantage.
- **Pandera / Patito / Polars:** Polars (`pola.rs`) executes validation checks as multi-threaded vectorized Rust expressions over Arrow buffers; `pandera.polars` compiles `DataFrameModel` checks into `LazyFrame` plans, and `patito` maps Pydantic-style classes onto Polars expressions. Public community benchmarks report 1M-row Polars-backed validation completing in ~40–150 ms (exact 100k × 60 OpenUBEM schema timings remain `UNVERIFIED`). **Limitation for OpenUBEM:** Step 1–5 relies on `GeoDataFrame` (`geometry` column + CRS), and Phases 1–5 will already run `openubem-results`, `openubem-idf`, and `openubem-sim` in Rust. Using Patito/Pandera would split schema truth between Python decorators and Rust structs.
- **Dedicated `openubem-schema` + `pyo3-arrow` (Recommended):** Validates entire Arrow `RecordBatch`es in a single GIL-released (`py.allow_threads`) Rust call using `rayon` across columns/row chunks. **Zero Python object instantiation per cell**, shared compile-time enums/unit types with `openubem-results` and `openubem-idf`, and direct zero-copy handoff to/from `pyarrow`, `pandas ArrowDtype`, and `geoarrow-rs`.

*(Gap note: Exact side-by-side wall-clock measurements on OpenUBEM's 8,139-building U.S. corpus and 3,832-home M8 districts across `pandas.apply`, Pydantic v2, Polars/Patito, and `openubem-schema` are not yet measured; Phase 0 T02 + Phase 1 T06 should benchmark this directly on `austin_centre`.)*

---

## Q3. Zero-Copy Arrow / GeoArrow / Parquet Interchange

### 3.1 `arrow-rs` + `pyo3-arrow` / `arro3` + PyCapsule Protocol
The **Arrow PyCapsule Interface** (`__arrow_c_schema__`, `__arrow_c_array__`, `__arrow_c_stream__`) standardized by Apache Arrow allows Rust extensions built with **`pyo3-arrow` (`0.21.0`, `MIT OR Apache-2.0`)** (from `kylebarron/arro3`) to exchange Arrow arrays, tables, and record batch streams **zero-copy** with `pyarrow`, `polars >= 1.2`, `pandas >= 2.2`, and `arro3-core` by passing C `ArrowArray` / `ArrowSchema` pointers inside Python `PyCapsule` objects ([crates.io/crates/pyo3-arrow](https://crates.io/crates/pyo3-arrow)).

### 3.2 Behaviour of OpenUBEM Column Types Across the FFI Boundary
1. **Nullable `Int64` (`levels`, `year_built`, `underground`, `n_warnings`, `n_severe`):**
   - Today `footprint_schema.py:76,140` and `simulation/parallel.py:221-222` cast to pandas `"Int64"` (`IntegerArray` extension dtype, which holds a NumPy `int64` buffer + boolean mask, *not* Arrow's bit-packed validity bitmap).
   - Converting pandas `"Int64"` → `pyarrow.Table` requires a validity mask pack unless pandas uses **`dtype="int64[pyarrow]"`** (`pd.ArrowDtype(pa.int64())`). Once backed by PyArrow (`int64[pyarrow]`), transfer via `__arrow_c_array__` to `arrow::array::Int64Array` in `pyo3-arrow` is **strictly zero-copy**, with `pd.NA` mapping 1:1 to Arrow's validity bitmap.
2. **String & Dictionary Provenance Columns (`provenance_*`, `data_quality_flag`, `status`):**
   - **Gotcha (`Utf8` vs `LargeUtf8`):** `pa.Table.from_pandas(df)` frequently produces `LargeUtf8` (`LargeStringArray`, 64-bit offsets), whereas `arrow-rs` default builders emit `Utf8` (`StringArray`, 32-bit offsets). `openubem-schema` should read via a helper accepting `DataType::Utf8 | DataType::LargeUtf8 | DataType::Utf8View` (and `Dictionary(_, Utf8 | LargeUtf8)`) so zero-copy works regardless of Python Arrow string flavor.
   - **Dictionary-encoded provenance (`DictionaryArray<Int8Type | Int16Type | Int32Type>`):** Provenance columns (`ASHRAE_STANDARD`, `OSM_OBSERVED`, `success_cached`, etc.) have tiny cardinality (<50 unique values across 40,800 buildings). Encoding them as Arrow `DictionaryArray` (mapped to `pd.Categorical` / `ArrowDtype(pa.dictionary(pa.int32(), pa.utf8()))`) shares both the integer index buffer and the unique-string dictionary buffer zero-copy across PyCapsule FFI and cuts RAM + validation time by validating the small dictionary values once rather than scanning 40k strings.
3. **`GeoPackage` (`.gpkg`) vs `GeoParquet` (`1.0`/`1.1`) & `GeoDataFrame`:**
   - **GeoPackage (`.gpkg`):** SQLite-based (`footprint_schema.py:152`). `geoarrow-rs` does **not** read `.gpkg`. Keep `.gpkg` ingress in Python using **`pyogrio` (`use_arrow=True`)**, which streams GDAL OGR batches directly into Arrow memory buffers without Fiona's row-wise Python loop.
   - **GeoParquet (`1.0`/`1.1`) + `geoarrow-rs` (`0.9.0`, `geoparquet` `0.9.0`):** GeoParquet stores tabular attributes flat alongside a WKB geometry column and a `geo` JSON footer specifying `version`, `primary_column`, `geometry_types`, spatial `bbox`, and **PROJJSON CRS** (`CRS84` default if omitted; OpenUBEM always writes explicit UTM CRS from `estimate_utm_crs()`). `geoarrow-rs` reads/writes GeoParquet natively in Rust (`Apache-2.0 OR MIT`) and exposes coordinate-array GeoArrow memory layouts (`PolygonArray`) zero-copy across PyCapsule. Note: converting a GeoArrow table back to a Shapely-backed `geopandas.GeoDataFrame` (`.to_geopandas()`) still pays Shapely object creation cost, so attribute/provenance/schema checks in Step 1–2 should operate on the Arrow/GeoArrow columns *before* or *without* materializing Shapely objects.

---

## Q4. Canonical Provenance & Flag-Token Normalization

Today, `data_quality_flag` suffers live delimiter drift: `,` in `footprint_schema.py:126` & `aggregator.py:144-148` vs `|` in `semantic/provenance.py:23,104-110`, with `NaN`/`""`/`None` ambiguity and O(N) Python string splitting per cell.

### Design of `QualityFlagSet` (`smallvec` + Closed Enum + Fail-Closed Grammar)
1. **Zero-heap stack storage (`smallvec` `1.16.6`, `MIT OR Apache-2.0`):** Each building carries at most ~1–8 quality flags (`no_floors`, `no_height`, `generic_tag`, `no_function`, `overlap_resolved`, `height_only_ft`, `no_building_tag`, `no_year`, plus M09 `{METHOD}_{SOURCE}_{TIER}` imputation flags). Storing `SmallVec<[QualityFlag; 8]>` (`#[repr(u8)]` closed enum for Step 1 flags, or compact tagged enum `FlagToken::Core(CoreFlag) | FlagToken::Imputed { method: MethodCode, source: SmallStr, tier: ConfidenceTier }`) keeps the entire flag set on the stack with zero heap allocation for the common `<= 8` flag case.
2. **Legacy delimiter-tolerant ingress, single canonical egress (`D-RS-03`):**
   - `parse_legacy(s)` splits on `c == ',' || c == '|'`, trims whitespace, skips empty segments (treating `null`/`""` identically as empty `QualityFlagSet`), maps each token through a strict `match` (or `phf` perfect hash table for static tokens) + `{METHOD}_{SOURCE}_{TIER}` parser (`provenance.py:79-95`), sorts (`sort_unstable()`), and deduplicates (`dedup()`).
   - **Fail-closed on unknown tokens:** Any unregistered token returns `Err(SchemaError::UnknownFlagToken(tok))` instead of silently passing typos downstream.
   - **Canonical serialization:** Emits sorted tokens joined by a single ratified separator (recommend `|` per `provenance.py:23`, with an explicit `DelimiterMode::CommaLegacy` opt-in adapter strictly for Step 1/5 shadow-parity mode when `OPENUBEM_RUST_BACKEND="shadow"`).
3. **Vectorized Arrow provenance scorer (`add_lineage_summary` replacement):** Replaces the nested Python loop in `provenance.py:198-200` by scanning Arrow `StringArray`/`DictionaryArray` provenance columns in Rust with `rayon`, applying `LEGACY_TOKEN_WEIGHT` (`0.5` / `0.1`) before `{METHOD}_{SOURCE}_{TIER}` parsing (`T07.1` rule) and writing contiguous `Int64Array` (`imputed_fields_count`) + `Float64Array` (`mean_imputation_confidence`) directly back to Python zero-copy.

---

## Q5. Supply-Chain & Licence Control (`cargo-deny`, `cargo-audit`, `proptest` / `bolero`)

OpenUBEM is dual-licensed **`Apache-2.0 OR MIT`** ([`PLAN_rust_migration.md`](../../../PLAN_rust_migration.md) §1.1, §3 Guardrail 5). Automated CI governance prevents accidental copyleft or vulnerable transitive crates:

1. **Strict `deny.toml` (`cargo-deny`, `MIT OR Apache-2.0`):**
   `cargo-deny` recursively walks the entire transitive dependency graph (including `-sys` crates) using `askalono` license detection ([EmbarkStudios/cargo-deny](https://github.com/EmbarkStudios/cargo-deny)). Configure `[licenses]` to allow **only** permissive SPDX identifiers:
   ```toml
   [graph]
   all-features = true

   [advisories]
   yanked = "deny"
   unmaintained = "workspace"

   [licenses]
   confidence-threshold = 0.85
   allow = [
     "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause",
     "ISC", "Unicode-3.0", "Zlib",
   ]
   # Explicitly omit GPL-*, AGPL-*, LGPL-*, OpenSSL, Unlicense globally!
   ```
2. **Transitive Hazard Analysis (SQLite, OpenSSL, GEOS):**
   - **GEOS (`geos` / `geos-sys`):** Wraps C++ GEOS under **`LGPL-2.1-or-later`** (copyleft). **Blocked** by `deny.toml` above—`openubem-schema` must use pure-Rust `geoarrow` / `geo` (`Apache-2.0 OR MIT`) and never pull `geos-sys`.
   - **OpenSSL (`openssl` / `openssl-sys`):** Uses the historical `OpenSSL` license (and `ring` uses mixed `MIT AND ISC AND OpenSSL` BoringSSL headers that frequently trigger `askalono` unknown-license failures). **Blocked** in `openubem-schema` (which does zero network I/O anyway; HTTP fetchers stay in Python per NG3).
   - **SQLite (`rusqlite` / `libsqlite3-sys`):** SQLite is public domain via the "SQLite Blessing", which `cargo-deny` does not recognize as standard `MIT`/`Apache-2.0` (often requiring `Unlicense` or `[[licenses.clarify]]` with `LICENSE` hash). **`openubem-schema` must NOT depend on `rusqlite` or `libsqlite3-sys`**; isolate `rusqlite` strictly to `crates/openubem-results` (Phase 1 T05) with a crate-scoped `[[licenses.exceptions]]` in `deny.toml` after owner sign-off.
3. **Pinning & Advisory Auditing (`Cargo.lock` + `cargo-audit`):**
   Commit `Cargo.lock` to git (even for workspace library crates) so CI, Mac M2 Pro, Windows x64, and Speed HPC wheels build identical dependency trees, run `cargo check --locked` / `cargo deny check --locked`, and run **`cargo-audit` (`0.23.0`, `Apache-2.0 OR MIT`)** on every PR against the RustSec database.
4. **Property-Based & Coverage-Guided Fuzzing (`proptest` + `bolero`):**
   - **`proptest` (`1.12.0`, `MIT OR Apache-2.0`):** Test round-trip invariants (`parse_legacy(canonical_str) == set`), idempotence (`append(set, x)` twice == once), delimiter equivalence (`,` vs `|`), non-`NaN`/`Inf` rejection in `AreaM2`, and arbitrary `0..255` UTF-8 fuzzing on `parse_token()` ensuring **zero panics**.
   - **`bolero` (`0.13.x`, `MIT`):** Wrap the same property tests in `bolero::check!` so CI can run fast randomized checks on every PR and nightly `libFuzzer` coverage-guided fuzzing on token/JSON/Arrow ingestion boundaries.

---

## Q6. Concrete `openubem-schema` Crate Design & Incremental Adoption Path

### 6.1 Crate Boundary & Workspace Layout (Guardrail 2 Compliant)
```text
crates/
├── openubem-schema/      # ZERO pyo3 deps! Pure Rust: unit newtypes, ADTs, EndUseLedger,
│                         # QualityFlagSet, provenance scorer, Arrow schema validators
│   Cargo.toml: arrow (60.x, default-features=false), parquet (60.x, optional),
│               nutype (0.8), smallvec (1.16), serde (1.0), thiserror (2.0), geoarrow (0.9, optional)
└── openubem-py/          # Thin PyO3 (0.30.x) + pyo3-arrow (0.21) adapter -> openubem._rust
```
- **Error mapping:** `SchemaError` (`thiserror`) maps to `PyValueError` (invalid units/flags/schema) or `PyRuntimeError` (unexpected internal Arrow layout error)—**zero `.unwrap()`/`panic!()` across FFI**.
- **GIL release:** All batch Arrow validation and provenance scoring functions extract PyCapsules on the GIL, then call `py.allow_threads(|| validate_batch(&batch))`.

### 6.2 Incremental Adoption Path (Steps 1, 2, 4, 5 behind `OPENUBEM_RUST_BACKEND`)

| Pipeline Step | Current Python Bottleneck / Bug Site | `openubem-schema` Integration | Shadow-Parity Gate (`OPENUBEM_RUST_BACKEND="shadow"`) |
|---|---|---|---|
| **Step 1** (`acquisition/footprint_schema.py`) | `iterrows()`/`apply(axis=1)` (`lines 64, 97, 127`), `,` flags (`line 126`), late `Int64` casts (`line 76`), `.gpkg` export | Python keeps `pyogrio(use_arrow=True)` `.gpkg`/GeoParquet I/O; passes Arrow table zero-copy via `pyo3-arrow` to `validate_step1_footprints()` (checks 23-col schema, unique `osm_id`, `AreaM2 >= 20.0`, `provenance_*`, canonical `QualityFlagSet`). | Run over `austin_centre` + 4 M8 districts; require 0 schema/flag diffs (with `,` legacy formatter toggle during shadow) before `"on"`. |
| **Step 2** (`semantic/provenance.py`) | Per-cell Python loop in `add_lineage_summary()` (`lines 198-200`), `|` vs `,` drift, `T07.1` legacy weight fragility | `score_provenance_batch()` scans Arrow `Dictionary`/`Utf8` columns in parallel `rayon` loop; `append_flag_batch()` normalizes `QualityFlagSet` across masked rows. | Bit-exact match (`|Δconf| <= 1e-12`, exact `imputed_fields_count`) across 346 EU-08 + U.S. enriched GeoParquets. |
| **Step 4** (`simulation/parallel.py`) | Late `Int64`/`fillna("")` casts (`lines 220-225`), unvalidated `status` strings | `validate_sim_manifest()` enforces `SimulationStatus` enum + Arrow `Int64` nullability + non-null `error_summary` string contract before writing `04_simulation_manifest.parquet`. | Bit-exact Parquet schema & row parity across golden cell runs. |
| **Step 5** (`results/{parser,carbon,aggregator}.py`) | `OPEN-01`, `OPEN-46`, `OPEN-61`, `OPEN-64`, `D-IMP-05` double-counting, `,` `_merge_flags` (`aggregator.py:135-148`), 4 duplicated `_SUCCESS_STATUSES` sets | `EndUseLedger<RawMeters>::reconcile()` → `EndUseLedger<ReconciledLedger>` feeds `compute_gwp()` and `aggregator.py` directly from `openubem-results` Arrow batches; `merge_flags_batch()` replaces `df.apply(_merge_flags, axis=1)`. | Bit-exact (`<= 1e-12 kWh`) across retained 8,139 U.S. + 346 EU-08 + 3,832 M8 SQL/CSV results before flipping `"on"`. |

*(Downstream Phase 3 reuse: `openubem-idf` also imports `UValueWm2K` and typed construction/surface enums from `openubem-schema` to eliminate `getattr` + `.lower()` string checks in [`openubem/idf/compliance.py:28-100`](../../../../../../openubem/idf/compliance.py#L28-L100).)*

---

## Gaps & Negative Results

1. **No published 10k–100k × 30–60 column cross-tool validation benchmark:** While Pydantic v2's speedup vs v1 (4×–50×, ~17× typical) and Polars' Rust engine scale (~40–150 ms at 1M rows) are documented, **no primary source benchmarks Pydantic v2 vs `pandera.polars` vs Patito vs `pyo3-arrow` on identical 10k–100k × 30–60 column geospatial building tables** on the same hardware. Treat throughput projections for `openubem-schema` as `UNVERIFIED` until Phase 0 T02 / Phase 1 T06 measures them on `austin_centre` and 8,139 U.S. buildings.
2. **Exact crates.io download figures for several crates (`uom`, `arrow`, `parquet`, `pyo3`, `pyo3-arrow`, `geoarrow`, `cargo-deny`):** Search summaries confirmed active 2025–2026 release tracks and licences, but crates.io dynamically renders exact download counts via JS/API, so unprinted download figures are left `UNVERIFIED` rather than estimated.
3. **`dimensioned` is unmaintained (`0.8.0`, Apr 2022):** Negative result — do not adopt for OpenUBEM.
4. **`uom` is unsuitable as an FFI/Arrow boundary type:** Negative result — compile-time `ISQ` type bloat and inability to wrap `Vec<uom::...>` zero-copy into Arrow `Float64Array` make `#[repr(transparent)]` newtypes + `nutype` strictly superior at boundaries.
5. **`geoarrow-rs` has no GeoPackage (`.gpkg`) driver and `pandas` `"Int64"` is not zero-copy until Arrow-backed:** Python-side `pyogrio(..., use_arrow=True)` and `dtype="int64[pyarrow]"` (or `pa.Table.from_pandas`) remain necessary at the Step 1 ingress boundary.
6. **SQLite licensing conflict in `cargo-deny`:** `libsqlite3-sys` (used by `rusqlite`) carries SQLite's public-domain blessing rather than `Apache-2.0 OR MIT`; isolating `rusqlite` out of `openubem-schema` and strictly inside `openubem-results` is required to keep `openubem-schema`'s dependency tree 100% pure `Apache-2.0 OR MIT` / BSD / ISC / Zlib.

# DR02 — Rust Building Energy Modeling (BEM), IDF/EPW Parsing & Deterministic 3D Extrusion Ecosystem

**Date:** 2026-11-26  
**Feeds:** Plan §4 (R3, R5), Phase 3 (T09–T11), Phase 5 (T15–T16), Owner Decision D-RS-06  
**Target License Constraint:** `Apache-2.0 OR MIT` (no GPL/AGPL/LGPL copyleft dependencies in OpenUBEM core wheels)

---

## Executive Summary

- **No production-ready Rust EnergyPlus IDF/IDD/epJSON crate exists.** Searches across `crates.io` and GitHub show zero standalone, maintained Rust crates for EnergyPlus IDF, IDD, or epJSON parsing; crates matching "IDF" target Espressif `esp-idf` firmware or PCB `idf-parser` formats (`crates.io`). OpenUBEM must author `openubem-idf` clean-room.
- **The Rust BEM/EPW ecosystem is nascent and mostly reference-only for UBEM.** `germolinal/simple` (MIT, ~11 stars, active) implements a standalone Wasm-capable building simulator rather than an EnergyPlus pipeline; `hamiltonkibbe/epw-rs` (`v0.1.4`, MIT, 1 star, ~32 downloads/90d, static since late 2024/early 2025) is an alpha EPW reader; `communitiesuk/epb-home-energy-model` (MIT, ~32 stars, active) implements the UK Home Energy Model; `modelscript` is **AGPL-3.0** and disqualified.
- **For IDF/ExpIDF/IDD parsing, a hand-written zero-copy byte scanner with `memchr` + `fast-float2` (or `winnow` for structured sub-grammars like `Schedule:Compact`) is optimal.** In `rosetta-rs/parse-rosetta-rs` release JSON benchmarks, `winnow` (`v1.0.1`) achieved `27 ms` vs `pest` (`v2.8.6`, `62 ms`) and `nom` (`v8.0.0`, `68 ms`), near `serde_json` (`18 ms`), while `logos` (`v0.16.1`) serves strictly as a DFA lexer (`>1,000 MB/s` claimed on tokenizing workloads).
- **For deterministic 3D extrusion (`openubem-extrude`), pure-Rust `geo` (`v0.33.1`) + `i_overlay` (`v9.2.0`) + `rstar` (`v0.14.0`) + `glam` (`v0.34.3`) is completely `MIT OR Apache-2.0`.** `geo`'s modern `BooleanOps` directly delegates to `i_overlay` (a pure-Rust fixed-point/grid-snapped overlay engine), avoiding `geos` (**LGPL** C library `libgeos` linking constraints), `CGAL` (**GPLv3+/LGPLv3+**), and `geo-clipper` (ISC wrapper around C++ Clipper1 / `clipper-sys` requiring a C++ toolchain; note `clipper2-rust` `v1.2.0` uses `BSL-1.0`).
- **Newell's method + canonical quantized vertex keys eliminate `FINDING 284`, `OPEN-56`, cyclic permutation misses, and 1-ULP fatals by construction.** Quantizing 3D coordinates onto an integer nanometer/0.1 mm grid (`i64`) before emitting `BuildingSurface:Detailed` vertices guarantees bit-identical coordinates across interzone mates, and `rstar` R-tree spatial indexing reduces `intersect_match` from `O(surface_pairs²)` (`M > 800` hangs in [`openubem/idf/surfaces.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/idf/surfaces.py#L166-L172)) to `O(N log N)`.
- **For CTF (`≤12×12` symmetric `eigh`) and `CalcScriptF` (`10×10` to `100×100` solves), pure-Rust `nalgebra` + `faer` eliminates Windows/HPC BLAS/Fortran linking pain.** `nalgebra` (`v0.35.0`, `Apache-2.0`) excels at small fixed/stack matrices (`≤32×32`: `49.9 µs` vs `faer` `63.6 µs` at `32×32` symmetric `f64` EVD in `faer` 0.8 benchmarks), while `faer` (`v0.24`, `MIT`) pulls ahead at `N ≥ 64` (`249.3 µs` vs `293.1 µs` at `64×64`; `987.5 µs` vs `1.9 ms` at `128×128`). `ndarray-linalg` (`v0.18`) requires `openblas-src`/`gfortran`, which fails by default on Windows without MSYS2/MinGW or proprietary Intel MKL.
- **Rust cannot accelerate EnergyPlus's internal C++ time-stepping via `libenergyplusapi`, but replacing `ExpandObjects` (`-x`) removes repeated process/startup overhead.** No official or active Rust `libenergyplusapi` crate exists (`bindgen` over `runtime.h`/`datatransfer.h` is feasible only for co-simulation callbacks, still subject to E+ global state reset discipline). Generating pre-expanded IDFs natively in `openubem-idf` removes `-x` completely.
- **Recommended Phase 3 & Phase 5a split:** Land `openubem-idf` (Phase 3) first using `memchr` + `fast-float2` + `unicase` + `serde_json` (schema-driven IDD/epJSON validation) + PyO3 shadow-diffing against `eppy`; follow with `openubem-extrude` (Phase 5a) using `geo` + `i_overlay` + `rstar` + `glam` + `nalgebra`/`faer`.

---

## Table 1: Rust BEM / IDF / EPW Repositories & Crates

| Name | URL | Scope | Licence | Stars / Downloads | Last Commit / Release | Maintained (Y/N) | Usability for OpenUBEM (1–5) |
|---|---|---|---|---|---|---|---|
| **`germolinal/simple`** | [github.com/germolinal/simple](https://github.com/germolinal/simple) | Holistic Rust building performance simulation (thermal, lighting, solar, weather, geometry, Wasm) | `MIT` | ~11 stars (`UNVERIFIED` exact downloads; not on crates.io as a library) | Recent activity reported; exact commit date `UNVERIFIED` | **Y** | **2** — Reference-only for Rust BEM physics architecture; does not parse EnergyPlus IDF/IDD/epJSON. |
| **`hamiltonkibbe/epw-rs`** | [github.com/hamiltonkibbe/epw-rs](https://github.com/hamiltonkibbe/epw-rs) · [crates.io/crates/epw-rs](https://crates.io/crates/epw-rs) | Alpha EPW weather file reader (`EPWFile`, `BufRead`, optional `polars` DataFrame export) | `MIT` | 1 star; ~32 downloads (90-day window) | Crate `v0.1.4` indexed Feb 2026; repo commits static since late 2024 / early 2025 | **N** (effectively dormant; approaching 2-yr threshold) | **2** — Alpha (`0.1.4`), lacks EPW writer and `PresentWeather` enum; trivial to replace with a clean 150-line OpenUBEM EPW parser. |
| **`communitiesuk/epb-home-energy-model`** | [github.com/communitiesuk/epb-home-energy-model](https://github.com/communitiesuk/epb-home-energy-model) | UK Government Home Energy Model (HEM) calculation engine in Rust | `MIT` | ~32 stars | Active (commits within days/weeks of late 2026; exact date `UNVERIFIED`) | **Y** | **1** — UK SAP/HEM-specific residential physics; no EnergyPlus IDF/EPW/3D extrusion reuse. |
| **`AZX-PBC-OSS/hpxml-rs`** | [github.com/AZX-PBC-OSS/hpxml-rs](https://github.com/AZX-PBC-OSS/hpxml-rs) | Rust HPXML parser, validator, serializer with Python/C++/Julia bindings | `UNVERIFIED` (not indexed in public search metadata) | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | **1** — Targets DOE/NREL HPXML (XML), not EnergyPlus IDF/IDD/epJSON. |
| **`energycenterlab/ep2fmu`** | [github.com/energycenterlab/ep2fmu](https://github.com/energycenterlab/ep2fmu) | Packages EnergyPlus models as FMUs (Python exporter + precompiled Rust runtime) | `BSD-3-Clause` | 0 stars | `UNVERIFIED` | `UNVERIFIED` | **1** — FMU co-simulation wrapper only; not an IDF parser or geometry builder. |
| **`modelscript/modelscript`** | [github.com/modelscript/modelscript](https://github.com/modelscript/modelscript) | Polyglot web/Wasm engineering compiler (Modelica, SysML v2, STEP; targets `.idf`/`.epjson`) | **GNU `AGPL-3.0`** (dual enterprise license) | ~20 stars | `UNVERIFIED` | `UNVERIFIED` | **0 (Disqualified)** — **AGPL-3.0 copyleft** violates OpenUBEM's `Apache-2.0 OR MIT` policy. |
| **EnergyPlus IDF / IDD / epJSON / `libenergyplusapi` crates** | — | Standalone Rust EnergyPlus IDF/IDD/epJSON parser or C-API wrapper | N/A | None exist | N/A | **N/A** | **0 (Negative result)** — Confirmed absent on `crates.io` (`idf` hits belong to `esp-idf-*` or PCB `idf-parser`). |

---

## Table 2: Rust Geometry, Parser & Linear-Algebra Crates

| Crate | Version | Licence | Pure-Rust (Y/N) | Relevant Benchmarks (Measured vs Claimed) | Caveats & License Flags |
|---|---|---|---|---|---|
| **`winnow`** | `1.0.5` | `MIT` | **Y** | **Measured** (`parse-rosetta-rs` JSON, release, `winnow v1.0.1`): `27 ms`, `67 KiB` binary overhead vs `serde_json` `18 ms`, `lalrpop` `40 ms`, `chumsky` `47 ms`, `pest v2.8.6` `62 ms`, `nom v8.0.0` `68 ms` (exact CPU/file size `UNVERIFIED` in search summary). | Best-in-class combinator for sub-grammars (`Schedule:Compact`, IDD tags), slightly slower than hand-written zero-copy byte scanning. |
| **`nom`** | `8.0.0` | `MIT` | **Y** | **Measured** (`parse-rosetta-rs` JSON, release, `v8.0.0`): `68 ms`. General text throughput claimed `~200–750 MB/s`. | Superseded in ergonomics and speed on text grammars by `winnow`. |
| **`pest`** | `2.9.6` | `MIT OR Apache-2.0` | **Y** | **Measured** (`parse-rosetta-rs` JSON, release, `v2.8.6`): `62 ms`. Claimed `~50–80 MB/s` for PEG grammars. | Too slow for multi-thousand-IDF batch compilation; heap-allocates `Pair` trees. |
| **`logos`** | `0.16.1` | `MIT OR Apache-2.0` | **Y** | **Claimed**: `>1,000 MB/s` (lexer/DFA tokenizer only, not full parser). | Tokenizes only; still needs a parser/AST layer. Overkill vs `memchr` for IDF `,`/`;`/`!` scanning. |
| **`memchr`** | `2.8.3` | `Unlicense OR MIT` | **Y** | SIMD (`AVX2`/`NEON`) byte search (`memchr`, `memchr2`, `memchr3`); standard backbone for multi-GB/s CSV/1BRC Rust scanners. | Primitive only; requires hand-written state machine for IDF `!` comments and `;` terminators. |
| **`fast-float2`** | `0.2.4` | `MIT OR Apache-2.0` | **Y** | **Claimed**: multi-GB/s fast-path `f64` parsing from `&[u8]` (`2–5×` faster than older `FromStr`/legacy `lexical`). | Replaces deprecated `fast-float` (had RustSec bounds-check advisory on empty slices). |
| **`geo`** | `0.33.1` | `MIT OR Apache-2.0` | **Y** | Delegates 2D polygon boolean ops (`BooleanOps`) directly to `i_overlay`. | Floating-point ops on non-boolean predicates must watch coordinate scale/precision; snap vertices explicitly. |
| **`i_overlay`** | `9.2.0` | `MIT OR Apache-2.0` | **Y** | **Claimed**: matches or beats C++ Clipper via `rayon` parallelism and zero FFI overhead (exact timing table `UNVERIFIED`). | Fixed-point/grid robustness requires bounded finite `f64` coordinates (`≤ 2^500`); supports `IntOverlay` (`i16`/`i32`/`i64`) and `FloatOverlay` (`f32`/`f64`). |
| **`geo-clipper`** | `0.9.0` | `ISC` (wrapper) / **C++ Clipper (`BSL-1.0`)** | **N** (C++ FFI `clipper-sys`) | Battle-tested Clipper1 performance; pays Rust↔C++ conversion & FFI overhead. | Requires C++ compiler at build time; wraps legacy Clipper1. Pure-Rust `i_overlay` is cleaner. |
| **`clipper2` / `clipper2-rust`** | `0.6.1` / `1.2.0` | `MIT OR Apache-2.0` (FFI) / `BSL-1.0` (pure-Rust port) | **N** (`clipper2`) / **Y** (`clipper2-rust`) | Not benchmarked here (`UNVERIFIED`). | `clipper2` compiles C++; `clipper2-rust` is `BSL-1.0` (permissive, not `Apache-2.0 OR MIT`). `i_overlay` already ships inside `geo`. |
| **`geos`** | `11.3.1` | `MIT` (crate) / **`LGPL-2.1+` (`libgeos` C/C++)** | **N** (C++ FFI) | C/C++ GEOS speed; pays FFI conversion cost. | **LGPL Flag:** Static linking into closed/permissive wheels triggers LGPL relinking obligations; requires dynamic `libgeos` distribution + C++ build env. Avoid in `openubem-extrude`. |
| **`cgal` (`rcgal`/`cgal-sys`)** | No mainstream crate | **`GPL-3.0+` / `LGPL-3.0+`** (component-dependent) | **N** | N/A | **GPL Flag:** Strong copyleft (`GPL`) taints `Apache-2.0 OR MIT` distribution. **Do not use.** |
| **`rstar`** | `0.14.0` | `MIT OR Apache-2.0` | **Y** | `RTree::bulk_load` (Sort-Tile-Recursive) `O(N log N)` build & `O(log N + k)` AABB query (exact ns/query `UNVERIFIED`). | 2D/3D AABB queries only; combine with exact polygon/plane checks for surface matching. |
| **`glam`** | `0.34.3` | `MIT OR Apache-2.0` | **Y** | SIMD-accelerated `DVec3`/`Vec3`/`DMat4` stack primitives. | 3D/4D graphics sizes only; no general `N×N` decompositions (`eigh`, `LU`). |
| **`nalgebra`** | `0.35.0` | `Apache-2.0` | **Y** | **Measured** (`faer` 0.8 benchmark, symmetric `f64` EVD): `49.9 µs` (`32×32`), `293.1 µs` (`64×64`), `1.9 ms` (`128×128`), `102.1 ms` (`512×512`) (CPU hardware `UNVERIFIED`). | Beats `faer` at `N ≤ 32`; `SymmetricEigen` uses iterative QR/Jacobi and degrades rapidly at `N ≥ 128`. Note license is `Apache-2.0` only (compatible with `Apache-2.0 OR MIT`). |
| **`faer`** | `0.24` | `MIT` | **Y** | **Measured** (`faer` 0.8 symmetric `f64` EVD): `63.6 µs` (`32×32` seq), `249.3 µs` (`64×64`), `987.5 µs` (`128×128`), `4.3 ms` (`256×256`), `16.9 ms` (`512×512` par). Non-symm `faer` 0.9: `207.4 µs` (`32×32`), `1.0 ms` (`64×64`), `5.1 ms` (`128×128`). | Dynamic `Mat<f64>` heap allocation incurs slight setup overhead below `N ≈ 32`; dominates `nalgebra` and `ndarray` at `N ≥ 64`. |
| **`ndarray-linalg`** | `0.18` | `MIT OR Apache-2.0` (crate) | **N** (FFI to OpenBLAS / MKL / Accelerate) | FFI call overhead penalizes small matrices (`12×12` CTF, `10×10–100×100` `CalcScriptF`); `ndarray` without BLAS EVD measured `127.5 µs` (`32×32`), `970.3 µs` (`64×64`), `5.4 ms` (`128×128`). | **Build/Linking Hazard:** `openblas-src` fails on Windows without MSYS2/MinGW + `gfortran`; Intel MKL has proprietary redistribution terms. Avoid. |

---

## Table 3: `eppy` / `geomeppy` Failure Modes vs. Rust Structural Fixes

| Legacy Failure Mode (Observed in OpenUBEM) | Root Cause in `eppy` / `geomeppy` | Rust Structural Fix (`openubem-idf` / `openubem-extrude`) |
|---|---|---|
| **Bundled IDD v8.0 field-shift errors** ([`openubem/config.py:13-26`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/config.py#L13-L26)) | `eppy` falls back to `iddcurrent` (v8.0.0), missing `Space Name` inserted after `Zone Name` in EnergyPlus 9.6+, shifting all `BuildingSurface:Detailed` fields by 1. | Embed/pin the exact **EnergyPlus 23.1 `Energy+.idd`** (or `Energy+.schema.epJSON`) compiled via `build.rs` or loaded explicitly at startup; validate field indices against strict 23.1 typed structs (`BuildingSurfaceDetailed`). |
| **Silent extensible-field & `;` truncation** ([`openubem/idf/builder.py:105-125`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/idf/builder.py#L105-L125)) | `EpBunch.__repr__` zips `obj[1:]` with `objls[1:]`; when `len(obj) > len(objls)`, `zip` drops trailing extensible fields and the `;` terminator, corrupting IDFs. | Store extensible vertex/schedule/ventilation tuples in typed `Vec<Vertex3>` / `Vec<Field>` fields; serializer unconditionally emits `,` separators and final `;` independent of field-label metadata. |
| **Python batch `expidf` parsing bottleneck** (`general_model.py`, `subset.py`, `compile.py`) | Python string splitting, regex, and `EpBunch` dict construction across thousands of expanded IDFs. | Zero-copy `&[u8]` scanner (`memchr` + `fast-float2` + `unicase`), parallelized across buildings with `rayon` (`v1.12.0`). |
| **Inverted exterior walls (`FINDING 284`: 35,709+ walls)** | `geomeppy`'s `is_clockwise()` fails on non-convex / arbitrary 2D polygons, inverting wall vertex order and flipping outward normals inward. | Compute signed 2D shoelace area (`i_overlay` / `geo` canonical CCW outer rings, CW holes) + **3D Newell's method** normal verification against outward zone vector (`dot(n_newell, outward_dir) > 0`), reversing vertex order deterministically if negative. |
| **Negative-volume 10 m³ zone stubs (`OPEN-56`: 8,160 buildings, 57.74× ACH / −11.8% heating)** | Unvalidated/inverted footprint rings and degeneracies in `geomeppy.add_block` produce self-intersecting or inverted zone volumes. | Pre-clean 2D footprints via `i_overlay` (`OverlayRule::Union` / non-zero fill, collinearity pruning, minimum area guard) and assert `signed_volume > 0` (via divergence theorem over closed zone polyhedron) before serialization. |
| **`intersect_match()` infinite hangs (`M > 800`, `M = 1455`)** ([`openubem/idf/surfaces.py:166-172`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/idf/surfaces.py#L166-L172)) | `geomeppy.intersect_match()` performs brute-force `O(S²)` polygon intersections across all surface pairs in Python. | Replace with **`rstar` 3D AABB R-tree** broadphase (`O(S log S)`) + coplanarity check + exact 2D `i_overlay` polygon clipping in local `(u, v)` plane. |
| **Missed cyclic-permutation floor/ceiling pairs** ([`openubem/idf/surfaces.py:127-160`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/idf/surfaces.py#L127-L160)) | `geomeppy`'s `almostequal()` compares vertex lists positionally (`v[i] == partner[i]`), missing identical polygons rotated by a vertex index offset (`_pair_interfloor_surfaces` workaround). | Normalize surface matching by **canonicalized quantized vertex set / lexicographically minimal cyclic rotation** (e.g., `CanonicalPolyKey` sorted/rotated on quantized `i64` grid) plus opposite-normal verification (`dot(n_a, n_b) ≈ -1`). |
| **1-ULP mirrored coordinate drift (`GetSurfaceData: Vertex size mismatch` on EU-11/EU-14)** | Floating-point transforms across adjacent blocks/zones drift by ~`1e-10`–`1e-15` m (`...771` vs `...7706`), tripping EnergyPlus's strict interzone matching. | Snap all extruded coordinates to a **canonical `i64` integer grid** (e.g., `0.1 mm` = `1e-4 m` or `1 µm` = `1e-6 m` units) prior to `BuildingSurface:Detailed` emission; mirrored pairs format identical `f64`/decimal strings from the exact same `i64` lattice points. |

---

## Q1. Existing Rust BEM / EnergyPlus / EPW Ecosystem

A comprehensive search across `crates.io`, `lib.rs`, and GitHub confirms that **no general-purpose, production-usable Rust EnergyPlus IDF, IDD, or epJSON parser/writer exists as of late 2026**. Searching `crates.io` for `idf` returns microcontroller crates for Espressif's ESP-IDF (`esp-idf-part`, etc.) and unrelated PCB Intermediate Data Format parsers (`idf-parser`). Likewise, no Rust crate wraps EnergyPlus's `epJSON` schema directly (`serde_json` is used ad hoc where needed).

The public Rust ecosystem touching Building Energy Modeling (BEM) and EPW weather consists of five small or domain-adjacent projects:

1. **`germolinal/simple` (SIMPLE — Germán Molina)** ([GitHub](https://github.com/germolinal/simple)): An MIT-licensed holistic building performance simulation engine in Rust (PhD research, Victoria University of Wellington), compiling natively and to WebAssembly. Its source tree modularizes `weather`, `geometry`, `heat`, and `solar` engines (~11 stars, active). **Assessment:** Valuable as a pure-Rust BEM physics reference, but it implements its own model format and solver rather than EnergyPlus IDF/IDD/epJSON or 3D footprint extrusion.
2. **`hamiltonkibbe/epw-rs`** ([GitHub](https://github.com/hamiltonkibbe/epw-rs), [crates.io](https://crates.io/crates/epw-rs), [docs.rs](https://docs.rs/epw-rs)): An MIT-licensed alpha (`v0.1.4`, indexed Feb 2026 on `crates.io`, 1 GitHub star, ~32 downloads in 90 days) EPW parser (`EPWFile::from_path`, `BufRead`, optional `polars` DataFrame conversion). Its roadmap lists lazy loading, `PresentWeather` enum, and EPW writing as unimplemented, and repository commits have been dormant since late 2024/early 2025 (approaching the 2-year inactivity threshold). **Assessment:** Too incomplete and unmaintained to adopt as a dependency; writing a clean EPW parser/writer inside OpenUBEM takes <200 LOC.
3. **`communitiesuk/epb-home-energy-model`** ([GitHub](https://github.com/communitiesuk/epb-home-energy-model)): Actively maintained MIT-licensed (~32 stars) Rust implementation of the UK Government's Home Energy Model (HEM). **Assessment:** Domain-specific to UK residential compliance; unusable for EnergyPlus UBEM workflows.
4. **`AZX-PBC-OSS/hpxml-rs`** ([GitHub](https://github.com/AZX-PBC-OSS/hpxml-rs)): Rust parser, validator, and serializer for DOE/NREL Home Performance XML (HPXML) with Python/C++/Julia bindings (stars/license/commit date `UNVERIFIED`). **Assessment:** XML/HPXML-only; does not handle IDF/IDD/epJSON.
5. **`energycenterlab/ep2fmu`** ([GitHub](https://github.com/energycenterlab/ep2fmu)): `BSD-3-Clause` (0 stars) Python exporter with a precompiled Rust runtime to package EnergyPlus models as FMUs without local C/C++ compilation. **Assessment:** Co-simulation packaging only.
6. **`modelscript/modelscript`** ([GitHub](https://github.com/modelscript/modelscript)): Polyglot web/Wasm compiler (~20 stars) targeting Modelica, SysML v2, and EnergyPlus `.idf`/`.epjson`. **Disqualified:** Open-core under **GNU AGPL-3.0**, incompatible with OpenUBEM's `Apache-2.0 OR MIT` license.

**Conclusion for Q1:** Every project above is either reference-only, domain-mismatched, dormant alpha, or copyleft-encumbered. OpenUBEM must build `openubem-idf` and `openubem-extrude` clean-room.

---

## Q2. High-Speed IDF / ExpIDF / IDD Parsing in Rust

### Parser Architecture Comparison

Measured release-mode results from [`rosetta-rs/parse-rosetta-rs`](https://github.com/rosetta-rs/parse-rosetta-rs) (JSON benchmark; exact CPU model and payload size `UNVERIFIED` in search excerpts) alongside crate characteristics:

| Architecture | Crate & Version | Licence | Measured / Claimed Speed | Fit for IDF / ExpIDF / IDD |
|---|---|---|---|---|
| **Hand-written zero-copy byte scanner** | `memchr` (`v2.8.3`) + `fast-float2` (`v0.2.4`) | `Unlicense OR MIT` / `MIT OR Apache-2.0` | `serde_json` hand-written baseline: `18 ms` in `parse-rosetta-rs`. `memchr` + `fast-float2` routinely achieve **multi-GB/s** (claimed) on delimited ASCII streams. | **Best for IDF & `ExpIDF`:** IDF grammar is flat (`ObjectType, field1, field2, ... ;` with `!` line comments). Zero-copy `&[u8]` slicing avoids UTF-8 validation overhead per token and `String` heap allocations. |
| **Parser combinators (modern)** | `winnow` (`v1.0.5`) | `MIT` | **Measured:** `27 ms` (`v1.0.1`, `67 KiB` overhead) in `parse-rosetta-rs`. Claimed `~600–800+ MB/s` on text streams. | **Best for structured sub-grammars:** `Energy+.idd` metadata tags (`\field`, `\type`, `\begin-extensible`, `\retaincase`) and `Schedule:Compact` (`For:` / `Until:`) benefit from `winnow`'s composable zero-copy `&[u8]` combinators. |
| **Parser combinators (legacy)** | `nom` (`v8.0.0`) | `MIT` | **Measured:** `68 ms` (`v8.0.0`) in `parse-rosetta-rs`. | Slower than `winnow` on text parsing; no advantage over `winnow`. |
| **DFA Lexer + custom parser** | `logos` (`v0.16.1`) | `MIT OR Apache-2.0` | **Claimed:** `>1,000 MB/s` lexing only. | Unnecessary complexity: IDF only has 3 structural delimiters (`,`, `;`, `!`), which `memchr3(b',', b';', b'!')` handles directly in SIMD without proc-macro DFA tables. |
| **PEG generator** | `pest` (`v2.9.6`) | `MIT OR Apache-2.0` | **Measured:** `62 ms` (`v2.8.6`) in `parse-rosetta-rs`. Claimed `~50–80 MB/s`. | **Reject:** Heap-allocated `Pair` trees create GC-like allocation pressure across 1,200+ IDFs. |

### Handling EnergyPlus IDD / epJSON Schema Quirks

A production `openubem-idf` parser must explicitly model five EnergyPlus format rules:
1. **Case-insensitive ASCII object & key lookup vs. `\retaincase`:** EnergyPlus treats class names and most alpha values case-insensitively (`unicase` `v2.10.0`, `MIT OR Apache-2.0`, or ASCII `eq_ignore_ascii_case` + FxHash/AHash), **except** IDD fields annotated with `\retaincase` (file paths, external lookup keys, schedule/surface names where case is preserved on round-trip). Storing raw `&'a str` / `Cow<'a, str>` slices preserves original casing while indexing keys via ASCII case-folding.
2. **Comment stripping (`!` vs `!-`):** Everything from `!` to `\n` is a comment (note `!-` auto-generated field comments from IDFEditor/eppy). Crucially, `!` inside quoted strings does not normally occur in IDF (IDF lacks general string quoting; commas/semicolons cannot appear inside fields), so `memchr3(b',', b';', b'!')` over `&[u8]` is exact.
3. **Blank defaults & trailing omitted fields:** In IDF, `Field1, , Field3;` leaves `Field2` blank (populated from IDD `\default` at simulation time), and objects terminated early by `;` omit all remaining optional fields. Typed Rust structs must represent optional fields with `Option<T>` / IDD-derived defaults rather than positional `Vec` assumptions.
4. **Extensible fields (`\begin-extensible` / `\extensible:<N>`):**
   - `BuildingSurface:Detailed` (and `FenestrationSurface:Detailed`, `Shading:*:Detailed`) switches after fixed header fields (including the EnergyPlus 9.6+ `Space Name` field!) to a repeating `N=3` triplet `(X, Y, Z)` vertex array up to `;`. Parsing directly into `SmallVec<[[f64; 3]; 8]>` or `Vec<[f64; 3]>` eliminates `eppy`'s `EpBunch.__repr__` `objls` truncation bug permanently.
   - `Schedule:Compact` repeats variable-length alpha/numeric fields (`Through:`, `For:`, `Interpolate:`, `Until:`, value) after `Name` and `Schedule Type Limits Name`. A `winnow` sub-parser can validate `For:` / `Until: HH:MM` rules directly into compact schedule blocks for `gpusim`.
5. **epJSON schema parity (`Energy+.schema.epJSON`):** EnergyPlus 23.1 ships a machine-readable JSON Schema (`Energy+.schema.epJSON`) alongside `Energy+.idd`. Parsing `Energy+.idd` (or `Energy+.schema.epJSON` via `serde_json` `v1.0.154`) at build time (`build.rs`) or startup lets `openubem-idf` verify field counts, `\retaincase`, and extensible stride `N` against EnergyPlus 23.1 automatically—preventing the `eppy` v8.0 IDD field-shift bug.

### Realistic Throughput Expectations
- **Observed baseline (`UNVERIFIED` hardware from `parse-rosetta-rs`):** `winnow` parses JSON at ~40–50% of `serde_json` speed (`27 ms` vs `18 ms`).
- **Expected IDF scanner throughput (theoretical / architectural estimate, NOT measured on IDF):** Given `memchr` (`AVX2`/`NEON`) delimiter scanning plus `fast-float2` (`GB/s`-class float parsing) and zero-copy `&[u8]` object tables, a Rust IDF scanner targeting `BuildingSurface:Detailed`-heavy `eplusout.expidf` files (typically 0.5–5 MB per multi-zone building) should realistically sustain **300–800 MB/s per core** for syntax + float parsing (faster if skipping unused classes via fast class-name prefix match), scaling near-linearly across cores with `rayon` (`v1.12.0`). A 1,200-building district (~1–3 GB total IDF/ExpIDF text) would parse in **<1–2 seconds on an 8-core CPU** vs tens of seconds/minutes in Python `eppy`. *(Marked as architectural estimate; benchmark on actual OpenUBEM `eplusout.expidf` corpus during Phase 3 shadow-diffing.)*

---

## Q3. Replacing `eppy` + `geomeppy` with a Deterministic 3D Rust Extruder

### Crate Selection & License Audit

| Crate | Version | Licence | Pure-Rust | Role in `openubem-extrude` |
|---|---|---|---|---|
| **`i_overlay`** | `9.2.0` | `MIT OR Apache-2.0` | **Y** | Core 2D polygon boolean operations (footprint cleaning, courtyard hole handling, party-wall/floor-ceiling overlap clipping). Uses internal integer/fixed-point grid (`IntOverlay` / `FloatOverlay`) eliminating floating-point topology cracks. |
| **`geo` + `geo-types`** | `0.33.1` / `0.7.20` | `MIT OR Apache-2.0` | **Y** | Canonical `Polygon<f64>` / `MultiPolygon<f64>` types and `BooleanOps` (which delegates directly to `i_overlay`), area, centroid, and simplification predicates. |
| **`rstar`** | `0.14.0` | `MIT OR Apache-2.0` | **Y** | `RTree::bulk_load` Sort-Tile-Recursive 3D AABB spatial index for `O(N log N)` surface-pair candidate lookup and courtyard/adjacency detection. |
| **`glam`** | `0.34.3` | `MIT OR Apache-2.0` | **Y** | Fast SIMD 3D `DVec3` cross/dot products, Newell normal computation, local `(u, v)` plane projection for 3D-to-2D coplanar polygon clipping. |
| **Disqualified / Avoided:** `geos` (`v11.3.1`), `CGAL`, `geo-clipper` (`v0.9.0`), `clipper2` (`v0.6.1`) | — | `geos`: crate `MIT`, **`libgeos` C++ `LGPL-2.1+`**; `CGAL`: **`GPLv3+/LGPLv3+`**; `geo-clipper`: `ISC` + C++ Clipper (`BSL-1.0`); `clipper2-rust`: pure Rust `BSL-1.0` | Mostly **N** | `CGAL` violates `Apache-2.0 OR MIT` via GPL. `geos` triggers LGPL dynamic-linking/relinking obligations and C++ build complexity. `geo-clipper`/`clipper2` need a C++ compiler. `i_overlay` is pure Rust, `MIT OR Apache-2.0`, and already integrated into `geo`. |

### Clean-Room Deterministic Extrusion Algorithm

To eliminate `FINDING 284`, `OPEN-56`, `intersect_match()` hangs, cyclic-permutation misses, and 1-ULP coordinate drift permanently:

1. **Canonical Integer Grid Snapping (`i64` Lattice):**
   - Immediately upon ingesting 2D footprints and floor elevations `(z_floor, z_ceiling)`, quantize all coordinates onto a deterministic `i64` grid—e.g. **0.1 mm resolution (`scale = 10_000.0`, 1 unit = `1e-4 m`)** or **1 µm (`scale = 1_000_000.0`)**—well inside EnergyPlus's `0.01 m` coincident-vertex tolerance (`_COINCIDENT_VERTEX_TOL` in [`openubem/idf/surfaces.py:164`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/idf/surfaces.py#L164)).
   - Store canonical `[i64; 3]` coordinates as the single source of truth; convert to `f64` and format to fixed decimal precision (e.g. `4` or `6` decimal places) only during final IDF emission. Two coincident or mirrored surfaces generated from adjacent buildings/zones/storeys are **guaranteed bit-identical**, eliminating `GetSurfaceData: Vertex size mismatch` (`EU-11`/`EU-14`) by construction.

2. **2D Footprint Regularization & Courtyard / Dwelling Subdivision (`i_overlay`):**
   - Run `i_overlay` (`IntOverlay` on the quantized `i64` grid!) with `FillRule::NonZero` / `OverlayRule::Subject` to resolve self-intersections, duplicate consecutive vertices, and zero-area spikes before extrusion.
   - Enforce **canonical winding** on 2D footprints via signed shoelace area (`> 0` CCW outer rings, `< 0` CW interior courtyard holes).
   - For interior courtyards (`Polygon` with interiors/holes): extrude exterior ring walls with normals pointing outward from the building solid, and hole ring walls with normals pointing *into* the courtyard void (which is still outward from the thermal zone air volume!). Note EnergyPlus `BuildingSurface:Detailed` cannot contain literal 3D holes in a single floor/roof polygon unless bridged by a zero-width cut or decomposed into convex/simply-connected sub-polygons (or earcut/trapezoidal partition via `geo` / `i_overlay` horizontal slicing) — **OpenUBEM must explicitly decompose holed floors/ceilings into hole-free polygons** (or slit-bridged simple rings) before emitting `Floor`/`Roof`/`Ceiling` surfaces.

3. **Newell's Method & Guaranteed Outward-Normal Winding (Eliminating `FINDING 284` & `OPEN-56`):**
   - For any extruded 3D polygon with vertices $v_0, \dots, v_{n-1}$, compute the exact Newell normal vector:
     $$\mathbf{n} = \sum_{i=0}^{n-1} (v_i - v_{(i+1) \bmod n}) \times (v_i + v_{(i+1) \bmod n})$$
   - **Wall extrusion:** Given a directed 2D edge $A \to B$ of a CCW footprint, the outward 2D normal is $(B_y - A_y, -(B_x - A_x))$. Extruding `[A_bot, B_bot, B_top, A_top]` yields an outward normal in `UpperLeftCorner` + `Counterclockwise` (or `LowerLeftCorner` + `Counterclockwise`) EnergyPlus convention; check `dot(n_newell, outward_2d_normal) > 0` and reverse if negative.
   - **Floor / Ceiling / Roof:** Verify `n_newell.z < 0` for floors (pointing down/out of zone) and `n_newell.z > 0` for ceilings/roofs (pointing up/out of zone).
   - **Closed-Zone Divergence Check (`OPEN-56` guard):** Sum signed tetrahedral volumes $V = \frac{1}{6} \sum_f \sum_{\Delta \in f} v_0 \cdot (v_1 \times v_2)$ across all surfaces of each extruded zone. Assert $V > V_{\min}$ (rejecting negative-volume or degenerate zone stubs prior to IDF output).

4. **`rstar` R-Tree Broadphase + `i_overlay` Clipping for Surface-Pair Matching:**
   - Insert every surface's 3D `AABB<[i64; 3]>` (padded by e.g. `1` grid unit or `1 mm` tolerance) into `rstar::RTree::bulk_load(...)` (`O(S log S)`).
   - Query intersecting AABBs (`O(S log S + K)` where `K` is actual adjacent pairs — **never `O(S²)`**).
   - Filter candidate pairs `(A, B)` from *different zones* (`zone_a != zone_b`) that are:
     1. **Anti-parallel coplanar:** `dot(unit_n_a, unit_n_b) <= -0.9999` and `|dot(centroid_b - centroid_a, unit_n_a)| <= tol`.
     2. **2D Overlap Clipping:** Project both polygons onto A's local 2D orthonormal basis `(u, v)` (`glam::DVec3`), quantize to `i64`, and run `i_overlay` `OverlayRule::Intersect` + `OverlayRule::Difference` (only needed when partial adjacency splits a wall/floor/ceiling, such as multi-dwelling subdivisions or stacked storeys with setbacks!).
   - **Reciprocal Pairing:** Full-match or split sub-polygons emit exact mirrored pairs (`Outside_Boundary_Condition = "Surface"`, `Outside_Boundary_Condition_Object = mate_name`, `Sun_Exposure = "NoSun"`, `Wind_Exposure = "NoWind"`). Because both mates are projected/reconstructed from the same snapped intersection polygon (with reversed vertex winding), **cyclic-permutation misses and ULP drift are impossible**, and [`audit_reciprocal_interzone_wall_surfaces`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/idf/surfaces.py#L41-L91) passes identically by construction.

5. **Fenestration (`FenestrationSurface:Detailed`):**
   - Generate inset window quads on exterior wall local `(u, v)` planes using WWR/sill/head rules, snap to the same `i64` grid (inset by `≥ 0.02 m` from parent wall edges so EnergyPlus never reports window-outside-parent fatals), orient with the exact same outward normal as the parent wall, and reference `Building_Surface_Name`.

---

## Q4. Linear Algebra for CTF (`≤12×12` `eigh`) & `CalcScriptF` (`10×10`–`100×100` Solves)

Inspection of [`openubem/gpusim/ctf.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/gpusim/ctf.py#L60-L162) and [`openubem/gpusim/viewfactors.py`](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/gpusim/viewfactors.py#L122-L141) confirms the exact numerical workloads:
- **CTF (`build_modal_conduction`):** Symmetric **tridiagonal** `f64` matrix `m_mat` of size `n_nodes × n_nodes` with `n_nodes <= max_modes = 12` per opaque construction. Requires all eigenvalues and eigenvectors (`eigh`).
- **`CalcScriptF` (`calc_script_f`):** Dense non-symmetric `f64` matrix `c_mat` of size `n_surf × n_surf` (typically `10×10` to `100×100` per zone/enclosure). Note `viewfactors.py:135-136` computes `c_inv = np.linalg.inv(c_mat); j_mat = c_inv * excite[None, :]` — in Rust, replacing explicit inversion with `LU::solve(&diag(excite))` (`c_mat \ diag(excite)`) is both faster and numerically cleaner while producing the identical `ScriptF` matrix.

### Head-to-Head Comparison (`faer` vs `nalgebra` vs `ndarray-linalg`)

| Criterion | `nalgebra` (`v0.35.0`) | `faer` (`v0.24`) | `ndarray-linalg` (`v0.18`) |
|---|---|---|---|
| **Pure Rust / Zero C/Fortran Linking** | **Yes** (`Apache-2.0`) | **Yes** (`MIT`) | **No** — wraps OpenBLAS / Netlib / Accelerate (`openblas-src` fails by default on Windows without MSYS2 + `gfortran`; Intel MKL adds proprietary redistribution terms). |
| **CTF (`≤12×12` symmetric tridiagonal `eigh`)** | **Winner:** Stack-allocated `SMatrix`/`DMatrix` with zero heap/blocking overhead. Measured `faer` 0.8 `32×32` symmetric `f64` EVD: `nalgebra` `49.9 µs` vs `faer` `63.6 µs`. Even better: `m_mat` is already tridiagonal, so a direct `12×12` symmetric tridiagonal QL/QR eigensolver (skipping Householder reduction) runs in sub-microsecond/few-µs range. | Slight overhead from dynamic `Mat<f64>` heap allocation & blocking dispatch below `N ≈ 32` (`63.6 µs` at `32×32`). | Poor for `12×12`: C/Fortran LAPACK FFI boundary dominates tiny-matrix runtime, plus Windows/HPC build fragility. |
| **`CalcScriptF` (`10×10`–`100×100` dense LU solve/inv)** | Fast for `10×10`–`32×32`; lags `faer` at `64×64`–`100×100` (`293.1 µs` vs `249.3 µs` at `64×64` EVD; LU scales similarly with cache blocking). | **Winner for `N ≥ 32–100`:** Explicit AVX2/AVX-512/NEON SIMD microkernels and panel-packed LU (`faer-lu`); avoids BLAS/LAPACK FFI completely. | Competitive at `N ≥ 100` on Linux/macOS Accelerate, but loses on `10×10–40×40` FFI overhead and breaks cross-platform Windows/HPC pure-Rust wheels. |

**Recommendation for Q4:**
- **Zero-BLAS pure-Rust policy:** Reject `ndarray-linalg` completely so `maturin` builds deterministic Windows, Linux (manylinux HPC), and macOS wheels with zero `gfortran`/OpenBLAS/MKL headaches.
- Use **`nalgebra`** (`v0.35.0`) for `≤12×12` CTF `eigh` (or a ~80-line pure-Rust `f64` symmetric tridiagonal QR/QL helper directly on `m_mat`'s diagonal/off-diagonal vectors, verified against `nalgebra::SymmetricEigen` & `ctf.py`'s conservation check) and **`faer`** (`v0.24`) for `CalcScriptF` (`partial_piv_lu` / `solve`) across `10×10`–`100×100` zones (or `nalgebra` if wanting a single dependency when max zone surface count stays `≤50`).

---

## Q5. Can Rust Accelerate EnergyPlus Itself, or Only IDF Prep (`ExpandObjects`)?

1. **No existing Rust `libenergyplusapi` wrapper & no internal physics speedup:**
   - Searches confirm **no official or maintained Rust crate wraps `libenergyplusapi`**. EnergyPlus exposes C headers (`runtime.h`, `datatransfer.h`, `state.h`) in `include/EnergyPlus/api/`, so `bindgen` FFI bindings (`stateNew()`, `stateDelete()`, runtime callbacks, sensor/actuator handles) are technically straightforward to generate.
   - **However, calling `libenergyplusapi` from Rust does NOT accelerate EnergyPlus's C++ thermal/HVAC time-stepping loop.** EnergyPlus still executes the exact same compiled C++ kernels; FFI callbacks actually add slight overhead if invoked every timestep, and EnergyPlus's global/stateful C++ architecture requires strict state lifecycle discipline (`stateDelete`/`stateNew`) to prevent cross-run state leakage. Parallel district runs still scale via OS processes (`std::process::Command` / worker pools) rather than multithreading inside one `EnergyPlusState`.
2. **Where Rust delivers real EnergyPlus runtime wins — replacing `ExpandObjects` (`-x`) natively:**
   - Invoking `energyplus -x` launches the separate `ExpandObjects` C++ preprocessor binary on every run to translate `HVACTemplate:*` (e.g., `HVACTemplate:Thermostat`, `HVACTemplate:Zone:IdealLoadsAirSystem`, `HVACTemplate:System:*`, `HVACTemplate:Plant:*`) and ground heat-transfer templates into explicit `AirLoopHVAC`, node/branch, and component objects, writing `.expidf` to disk before simulation starts.
   - Generating **pre-expanded IDFs** directly in `openubem-idf` (expanding templates once per archetype or natively in Rust memory) lets OpenUBEM **drop the `-x` flag completely**, eliminating `ExpandObjects` subprocess spawn + redundant disk I/O + double IDF parsing across 300–1,200+ buildings × 10k+ sweeps.
   - Note that for OpenUBEM's primary `gpusim` backend, Rust `openubem-idf` + `openubem-extrude` + pure-Rust CTF/`CalcScriptF` directly replaces the entire Python `eppy`/`geomeppy`/`numpy` compilation pipeline—yielding large end-to-end speedups *without* invoking EnergyPlus at all.

---

## Q6. Concrete Crate Stack & Migration Order

### Recommended Workspace Crate Stack (`Apache-2.0 OR MIT` Compliant)

- **`openubem-idf` (Phase 3 — T09–T11):**
  - Parsing & scanning: `memchr = "2.8.3"`, `fast-float2 = "0.2.4"`, `winnow = "1.0.5"` (for `Energy+.idd` & `Schedule:Compact`), `unicase = "2.10.0"`, `serde = "1"` + `serde_json = "1.0.154"` (for `Energy+.schema.epJSON` validation), `rayon = "1.12.0"` (batch compilation across buildings).
  - EPW weather: clean-room 150-LOC parser/writer inside `openubem-idf` using `memchr` + `fast-float2` (avoiding dormant alpha `epw-rs`).
  - Python FFI: `pyo3` + `maturin` returning Arrow/NumPy/typed structs for `gpusim/compile.py` and `general_model.py`.
- **`openubem-extrude` (Phase 5a — T15–T16):**
  - 2D/3D geometry & spatial indexing: `geo = "0.33.1"`, `geo-types = "0.7.20"`, `i_overlay = "9.2.0"`, `rstar = "0.14.0"`, `glam = "0.34.3"`.
  - Linear algebra (for `gpusim` compiler kernels `ctf.py` & `viewfactors.py` if housed alongside or in `openubem-compile`): `nalgebra = "0.35.0"` (`12×12` CTF `eigh`) + `faer = "0.24"` (`CalcScriptF` `partial_piv_lu` solve).
  - License gate: `cargo-deny` enforcing `MIT`, `Apache-2.0`, `Unlicense`, `ISC`, `BSD-3-Clause` and blocking `GPL`, `AGPL`, `LGPL`.

### Phased Migration Order

1. **Phase 3a — Schema & Zero-Copy IDF/ExpIDF Reader (`openubem-idf`):**
   - Embed/load EnergyPlus 23.1 `Energy+.idd` / `Energy+.schema.epJSON`; build zero-copy `&[u8]` IDF scanner (`memchr` + `fast-float2`), `Schedule:Compact` evaluator (`winnow`), and typed structs for `BuildingSurface:Detailed`, `FenestrationSurface:Detailed`, `Material`, `Construction`, and `Zone`.
   - Shadow-diff against `eppy` on OpenUBEM's US (DOE/ASHRAE 90.1) and EU (TABULA) districts, specifically verifying zero field-shift bugs and zero `EpBunch.__repr__` extensible truncations.
2. **Phase 3b — IDF Writer, `ExpandObjects` Replacement & EPW Reader:**
   - Emit EnergyPlus 23.1 IDFs directly from Rust structs (always `,` and `;`-terminated); drop `eppy` from `openubem/idf/builder.py` and `gpusim/general_model.py` / `compile.py`, and eliminate `-x` (`ExpandObjects`) for `IdealLoadsAirSystem` / templated archetypes.
3. **Phase 3c — Pure-Rust `ctf` & `viewfactors` Compilation Kernels:**
   - Port `build_modal_conduction` (`nalgebra` `SymmetricEigen` / tridiagonal QR) and `calc_approximate_view_factors` / `fix_view_factors` / `calc_script_f` (`faer` LU solve) into Rust with `rayon` batch parallelism across `[B, S, S]`.
4. **Phase 5a — Deterministic 3D Extruder (`openubem-extrude`):**
   - Implement `i64` grid-snapped footprint regularization (`i_overlay`), holed courtyard polygon decomposition, Newell outward-normal verification, divergence-theorem positive-volume assertions (`OPEN-56`), `rstar` AABB + `i_overlay` interzone/interfloor matching (`_pair_interfloor_surfaces`), and fenestration inset generation.
   - Validate with `audit_reciprocal_interzone_wall_surfaces`, EnergyPlus 23.1 simulation smoke runs on EU-11/EU-14 + `M > 800` footprints, and fleet-wide shadow-diffing before removing `geomeppy`.

---

## Gaps & Negative Results

- **Negative Result — Zero Rust IDF/IDD/epJSON/EnergyPlus-API Crates:** Confirmed no reusable public Rust crate exists on `crates.io` or GitHub for EnergyPlus IDF parsing, IDD schema handling, `epJSON` structs, or `libenergyplusapi` safe FFI wrappers.
- **Negative Result — `epw-rs` Not Production-Ready:** `epw-rs` (`v0.1.4`) is alpha, has 1 star and ~32 downloads/90d, lacks an EPW writer, and has had no substantive repo commits since late 2024/early 2025.
- **Unverified Repository Metadata:** Exact last-commit dates for `germolinal/simple`, `communitiesuk/epb-home-energy-model`, `energycenterlab/ep2fmu`, and `AZX-PBC-OSS/hpxml-rs`, as well as stars and exact license of `AZX-PBC-OSS/hpxml-rs`, were not surfaced in search indices and remain `UNVERIFIED`.
- **Benchmark Hardware/Dataset Gaps:** `rosetta-rs/parse-rosetta-rs` (`27 ms` `winnow` vs `68 ms` `nom` vs `62 ms` `pest` vs `18 ms` `serde_json`) and `faer` 0.8/0.9 release EVD tables (`32×32` to `512×512`) lacked explicit CPU model strings and JSON file byte size in the retrieved summaries (`UNVERIFIED` hardware). Additionally, `i_overlay` vs `geo-clipper` numerical timing tables and exact IDF MB/s scanner throughput are unmeasured until benchmarked on OpenUBEM's actual `eplusout.expidf` and EU/US footprint datasets.

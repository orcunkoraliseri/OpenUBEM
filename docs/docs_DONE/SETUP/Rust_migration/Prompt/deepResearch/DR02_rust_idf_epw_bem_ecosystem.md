# DR02 — Rust Building Energy Modeling (BEM), IDF/EPW Parsing & Deterministic 3D Extrusion Ecosystem

**Feeds:** Plan §4 (R3, R5), Phase 3 (T09–T11), Phase 5 (T15–T16), and Owner Decision D-RS-06
**Save output to:** `results/DR02_result.md`

---

## PROMPT

You are a research engineer specialising in Building Performance Simulation (EnergyPlus, IDF/IDD/epJSON, EPW), computational geometry for 3D building massing, and Rust parser/linear-algebra ecosystems. Produce a rigorous, source-cited landscape and architecture report.

### Context
OpenUBEM generates and parses thousands of EnergyPlus 23.1 IDF files (`openubem/idf/`, `openubem/gpusim/`) across US (DOE/ASHRAE 90.1 multi-zone commercial/residential) and European (TABULA/EPISCOPE multi-dwelling) districts (300–1,200+ buildings per district, targeting 10k+ scenario sweeps).

Two legacy Python dependencies cause severe speed and correctness problems:
1. **`eppy` (`>=0.5.63`)**: Bundled IDD v8.0 caused `BuildingSurface:Detailed` field-shift errors (`openubem/config.py:13-26`); `EpBunch.__repr__` silently truncated extensible fields and `;` terminators requiring `_repair_oversized_epbunch_objls` (`openubem/idf/builder.py:105-125`); parsing thousands of expanded IDFs (`eplusout.expidf`) in Python bottlenecks `gpusim` batch compilation (`openubem/gpusim/general_model.py`, `subset.py`, `compile.py`).
2. **`geomeppy` (`>=0.11.8`)**: Broken `is_clockwise()` inverted 35,709+ outdoor walls (`FINDING 284`), produced negative-volume 10 m³ zone stubs across 8,160 buildings (`OPEN-56`, 57.74× ACH error / −11.8% heating), hung infinitely in `intersect_match()` on complex footprints (`M > 800`), missed cyclic-permutation ceiling/floor pairs (`openubem/idf/surfaces.py:127-160`), and suffered 1-ULP mirrored coordinate drift (`642384.787910771` vs `...7706`) causing EnergyPlus fatal `GetSurfaceData: Vertex size mismatch` on EU-11/EU-14 buildings.

Additionally, our `gpusim` compiler runs:
- `build_modal_conduction` (`openubem/gpusim/ctf.py`): symmetric tridiagonal/generalized float64 `eigh` eigensolve (up to `MAX_MODES = 12`) per construction.
- `viewfactors.py`: `CalcApproximateViewFactors`, `FixViewFactors` iterative row/symmetry balancing, and `CalcScriptF` dense float64 matrix inversion per zone/enclosure.

### Questions
1. **Existing Rust BEM / EnergyPlus / EPW ecosystem.** Survey every public Rust crate or GitHub repo touching EnergyPlus, IDF, IDD, epJSON, EPW weather files, or building thermal simulation (including German Molina's `SIMPLE`, `epw-rs`, any OpenStudio/IDF/epJSON parsers, or academic UBEM tools in Rust). Report stars, last commit date, licence, completeness, and whether any is production-usable or reference-only.
2. **High-speed IDF / ExpIDF / IDD parsing in Rust.** Compare parser architectures (`nom`, `winnow`, `pest`, `logos`, or a hand-written zero-copy byte scanner over `!` comments, `,`, and `;` delimiters with case-insensitive ASCII object lookup). Include EnergyPlus IDD/epJSON schema quirks (extensible fields, blank defaults, `\retaincase`, `Schedule:Compact`, `BuildingSurface:Detailed` vertex arrays). What throughput (MB/s or IDFs/s) is realistic?
3. **Replacing `eppy` + `geomeppy` with a deterministic 3D Rust extruder.** How should a clean-room `Apache-2.0 OR MIT` Rust module extrude 2D footprints (including multi-storey stacks, interior courtyards, and dwelling subdivisions) into valid EnergyPlus 23.1 `BuildingSurface:Detailed` + `FenestrationSurface:Detailed` objects? Cover:
   - Newell's method & guaranteed outward-normal winding (eliminating `FINDING 284` and `OPEN-56`),
   - Canonical vertex rounding/snapping so mirrored interzone surfaces share bit-identical coordinates (eliminating ULP drift fatals),
   - Fast polygon intersection/clipping and `rstar` R-tree surface-pair matching (replacing `geomeppy.intersect_match()` without hangs).
   Which Rust crates (`geo`, `i_overlay`, `geo-clipper`, `rstar`, `glam`, `nalgebra`) have permissive licences and exact robustness guarantees?
4. **Linear algebra for CTF & ScriptF in Rust.** Compare `faer`, `nalgebra`, and `ndarray` + `ndarray-linalg` (OpenBLAS/Apple Accelerate) for thousands of small dense float64 eigensolves (`12×12` symmetric tridiagonal) and `10×10` to `100×100` `CalcScriptF` matrix inversions/linear solves. Highlight pure-Rust (zero C/Fortran BLAS linking headaches on Windows/HPC!) performance vs native BLAS.
5. **Can Rust accelerate EnergyPlus itself or only IDF prep?** Briefly confirm whether any Rust wrapper/FFI around EnergyPlus C++ (`libenergyplusapi`) exists or helps, vs generating pre-expanded IDFs (`ExpandObjects` replacement in Rust) to drop E+'s `-x` startup step.
6. **Recommendation.** Concrete crate stack and migration order for `openubem-idf` (Phase 3) and `openubem-extrude` (Phase 5a).

### Required output format
- **Executive summary** (≤10 bullets).
- **Table: Rust BEM/IDF/EPW repositories & crates**: name, URL, scope, licence, stars/downloads, last commit, maintained (Y/N), usability for OpenUBEM (1–5).
- **Table: Rust geometry & linear-algebra crates** (`geo`, `rstar`, `i_overlay`, `faer`, `nalgebra`, etc.): version, licence, pure-Rust (Y/N), relevant benchmarks, caveats.
- **Table: `eppy`/`geomeppy` failure modes vs Rust structural fixes**.
- Sections answering Q1–Q6.
- **Gaps & negative results**.

### Rules
- Cite every factual claim (URL / DOI / crate version + date). Mark anything uncited `UNVERIFIED`.
- Flag any GPL/AGPL/LGPL crate (e.g., `geos` C-library LGPL dynamic-linking nuance, Clipper C++ vs pure-Rust `i_overlay`, CGAL GPL) so we do not violate `Apache-2.0 OR MIT`.
- Search terms to include: "rust energyplus idf parser", "epw-rs", "germolinal simple rust", "faer rust benchmark eigensolver", "i_overlay rust polygon boolean", "winnow nom zero copy parser rust", "rstar rust spatial index".

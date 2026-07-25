# Deep-Research Prompt U05 — UTCI POLYNOMIAL APPROXIMATION & COMPUTATIONAL ALGORITHMS

> SCOPE GUARD — READ FIRST. This prompt examines the **mathematical, algorithmic, and software implementation methods** used to calculate UTCI efficiently. It covers the Bröde et al. (2012) 6th-degree operational polynomial approximation, Look-Up Tables (LUT), vectorized NumPy/C/Fortran implementations, boundary handling, and performance optimization for processing millions of spatial grid points in OpenUBEM. Do NOT cover physiological thermo-regulation (`U01`), non-radiant input scaling (`U02`), radiant flux physics (`U03`), or GUI simulation software (`U04`). See `00_README_utci_prompt_set.md`.

---

## What this document is

A computational math & code optimization specification. The full Fiala multi-node thermo-physiological model consists of a coupled set of non-linear differential equations representing internal body heat transfer, active vasomotor controls, and evaporative sweating. Solving the full Fiala model numerically requires several seconds per space-time point—rendering it computationally impossible for urban-scale simulations containing $10^6$ spatial grid points across 8760 hourly time steps. This prompt analyzes the operational polynomial approximation created by COST Action 730 and evaluates fast computational algorithms for OpenUBEM.

## Role

Computational mathematician & high-performance software engineer. Ground polynomial equations, mathematical error bounds, regression formulations, and code benchmarks in primary literature (Bröde et al. 2012; Fiala et al. 2012; Tartarini & Schiavon 2020 / `pythermalcomfort`; Roudsari et al. / `ladybug_comfort`).

## Why this matters (so you scope correctly)

A high-resolution UTCI spatial map over a $2\text{ km} \times 2\text{ km}$ urban district at $2\text{ m}$ grid resolution contains $1,000,000$ calculation points per hourly time step. Evaluating an unoptimized loop in Python would take hours per time step. OpenUBEM requires a fully vectorized, computationally efficient, and mathematically verified UTCI algorithm capable of executing millions of calculations per second while enforcing strict biometeorological boundary checks.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Full Fiala Model vs. Bröde Operational Polynomial Approximation

| Evaluation Attribute | Full Fiala Thermo-Physiological Model | Bröde et al. (2012) Operational Polynomial | Look-Up Table (LUT) + Interpolation | Source |
|---|---|---|---|---|
| Mathematical Formulation | Coupled 2D/3D PDEs for tissue heat transfer & bio-fluid flow | 6th-degree multi-variable polynomial regression (200+ terms) | Pre-computed 4D grid array ($T_a, v, RH, T_{mrt}-T_a$) | Fiala et al. 2012; Bröde et al. 2012 |
| Calculation Time per Point | $1.0 - 5.0\text{ seconds}$ | $< 1.0\text{ microsecond}$ | $< 0.1\text{ microsecond}$ |  |
| Approximation Error ($\text{RMSE}$) | $0.00^\circ\text{C}$ (Ground Truth Benchmark) | $0.11^\circ\text{C}$ (Max error $< 0.3^\circ\text{C}$) | Function of grid resolution ($0.05 - 0.2^\circ\text{C}$) | Bröde et al. 2012 |
| Memory Footprint | High (State variables per node) | Negligible ($< 10\text{ KB}$ for code/coefficients) | Moderate ($10 - 100\text{ MB}$ for 4D table) |  |
| Operational Domain Limits | Universal physiological solver | Restricted boundary box (See Table 2) | Restricted to table extent |  |

### Table 2 — Bröde Polynomial Boundary Box & Out-of-Bounds Handling Strategy

| Input Parameter | Minimum Valid Bound | Maximum Valid Bound | Out-of-Bounds Penalty / Behaviour | Recommended OpenUBEM Clamp / Flag Strategy | Source |
|---|---|---|---|---|---|
| Air Temperature ($T_a$) | $-50.0^\circ\text{C}$ | $+50.0^\circ\text{C}$ | Severe polynomial divergence | Clamp to $[-50, +50]^\circ\text{C}$; Flag `UTCI_TA_OUT_OF_BOUNDS` | Bröde et al. 2012 |
| Offset ($T_{mrt} - T_a$) | $-30.0^\circ\text{C}$ | $+70.0^\circ\text{C}$ | Unphysical oscillations | Clamp to $[-30, +70]^\circ\text{C}$; Flag `UTCI_TMRT_OUT_OF_BOUNDS` | Bröde et al. 2012 |
| Wind Speed at 1.1m ($v_{1.1m}$) | $0.5\text{ m/s}$ | $17.0\text{ m/s}$ | Exponential error | Clamp $v < 0.5 \to 0.5\text{ m/s}$; Flag `UTCI_WIND_LOW_CLAMP` | Bröde et al. 2012 |
| Water Vapor Pressure ($e$) | $0.0\text{ kPa}$ | $5.0\text{ kPa}$ ($RH \le 100\%$) | Evaporative equilibrium breakdown | Clamp to $[0, 5]\text{ kPa}$; Flag `UTCI_VP_OUT_OF_BOUNDS` | Bröde et al. 2012 |

### Table 3 — Open-Source Python & C/Fortran UTCI Libraries Benchmark

| Package / Library | Primary Language | Internal Algorithm | Vectorization Support (NumPy / Numba / C) | Throughput (Evaluations/sec) | OpenUBEM Fit | Source |
|---|---|---|---|---|---|
| `ladybug_comfort.utci` | Python | Bröde Polynomial | Native NumPy vectorization | $\sim 5,000,000\text{ ops/sec}$ | Excellent (Direct dependency fit) | Roudsari et al. |
| `pythermalcomfort` | Python / C | Bröde Polynomial / Numba | NumPy / C bindings | $\sim 10,000,000\text{ ops/sec}$ | Excellent (C-accelerated benchmark) | Tartarini & Schiavon 2020 |
| `utci` (PyPI package) | Python | Bröde Polynomial | Pure Python loops / NumPy | $\sim 500,000\text{ ops/sec}$ | Moderate |  |
| Custom Numba / Cython kernel | C / JIT Python | Parallelized C-loop | Multi-threaded CPU / GPU (CUDA) | $> 50,000,000\text{ ops/sec}$ | High (Performance tier) |  |

### Table 4 — Polynomial Coefficient Structure & Implementation Verification Test Suite

| Test Case # | $T_a$ ($^\circ\text{C}$) | $T_{mrt}$ ($^\circ\text{C}$) | $v_{1.1m}$ ($\text{m/s}$) | $RH$ (%) | Expected UTCI ($^\circ\text{C}$) | Heat Stress Category | Verification Tolerance |
|---|---|---|---|---|---|---|---|
| TC-01 (Comfort) | $20.0$ | $20.0$ | $1.0$ | $50.0$ | $19.6^\circ\text{C}$ | No thermal stress | $\pm 0.1^\circ\text{C}$ |
| TC-02 (Hot & Sunny) | $35.0$ | $55.0$ | $1.0$ | $50.0$ | $41.2^\circ\text{C}$ | Very strong heat stress | $\pm 0.1^\circ\text{C}$ |
| TC-03 (Extreme Sun & Humid) | $40.0$ | $65.0$ | $0.5$ | $60.0$ | $> 50.0^\circ\text{C}$ | Extreme heat stress | $\pm 0.2^\circ\text{C}$ |
| TC-04 (Cold & Windy) | $-10.0$ | $-10.0$ | $10.0$ | $80.0$ | $-24.5^\circ\text{C}$ | Strong cold stress | $\pm 0.1^\circ\text{C}$ |

---

## Part C — Synthesis (Algorithm & Code Architecture Verdict)

Give:
1. A recommendation on the exact Python library or custom Numba/NumPy module OpenUBEM should select for production UTCI evaluation.
2. A defensive strategy for handling input values that exceed the Bröde operational polynomial boundary box without throwing runtime exceptions.
3. A validation protocol ensuring the mathematical implementation matches COST Action 730 reference benchmarks.

## Output Format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C synthesis.
3. Provide code snippets for vectorized NumPy/Numba evaluation and boundary clamping.
4. **"Confidence and caveats":** address truncation errors and floating-point precision differences across platforms.
5. **Reference list** — complete citations with DOIs.

## Hard Requirements

- **Populate every cell in Tables 1–4.**
- **Enforce strict boundary box checks and clamping rules.**
- **Provide explicit operational polynomial throughput benchmarks.**

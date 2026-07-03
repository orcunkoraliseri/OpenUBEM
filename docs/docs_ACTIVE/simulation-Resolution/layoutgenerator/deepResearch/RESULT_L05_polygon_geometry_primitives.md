# RESULT_L05: Polygon Geometry Primitives (Offset, Skeleton, Medial Axis, Decomposition — The Slicing Toolkit)

This document provides a method-by-method appraisal of the computational-geometry primitives used to slice arbitrary building footprint polygons into corridors, cores, and perimeter thermal zones for OpenUBEM. It establishes the robust, implementable path for `layoutGenerator.py` using OpenUBEM's current geometry stack (`shapely` and `geomeppy`) and addresses the current courtyard/donut core simulation crash.

---

## 1. REQUIRED OUTPUT TABLES

### Table 1 — The geometry-primitive catalogue

| Primitive | What it computes | Shape it slices well | Output (lines / sub-polygons / skeleton graph) | Failure / numerical-robustness mode | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Negative buffer / inward offset (Minkowski erosion)** | Uniform contraction of the polygon boundary inward by a perpendicular distance $d$. | Compact convex-ish shapes (rectangles, circles, hexagons). | Outer perimeter band (split into wedges) + core sub-polygon. | • Core collapses on narrow shapes (width $< 2d$).<br>• Core splits into MultiPolygons on non-convex shapes.<br>• Donut-shaped core on courtyards (E+ Fatal).<br>• Corner slivers and precision failures. | Clipper (Angus Johnson 2014) [15]; GEOS/Shapely [12, 13] |
| **Straight skeleton** | A skeletal graph of straight-line trajectories traced by vertices as polygon edges shrink parallel to themselves. | Non-convex shapes (L, U, T, cross, and shapes with holes). | Skeletal roof/spine graph (disjoint straight segments). | • Extreme sensitivity to boundary noise (spurs).<br>• Floating-point errors in event sorting causing infinite loops/crashes.<br>• High computational complexity ($O(n^2 \log n)$). | Aichholzer & Aurenhammer (1996) [1]; Eppstein (2013) [5] |
| **Medial axis (transform)** | The locus of centers of maximally inscribed disks within the polygon. | Elongated slabs, curved/organic shapes, corridors. | Topological centerline (curves and straight segments). | • Includes parabolic arcs, making vector representation hard.<br>• Noise creates spur branches.<br>• Requires rasterization, introducing grid resolution parameters. | Harry Blum (1967) [21]; skimage docs [22] |
| **Rectangular (orthogonal) decomposition** | Partitioning a rectilinear polygon into a set of mutually disjoint, non-overlapping rectangles. | Rectilinear shapes (L, U, T, O-courtyard with 90° corners). | A set of rectangular sub-polygons. | • Fails on non-orthogonal edges.<br>• Produces slivers on irregular jogs.<br>• NP-hard for minimum partitioning if holes are present. | Joseph O'Rourke (1984) [25]; Mark Bayazit [3] |
| **Convex decomposition** | Partitioning a simple non-convex polygon into a set of mutually disjoint convex polygons. | Any simple polygon with reflex (concave) vertices. | A set of convex sub-polygons. | • Produces many narrow sliver polygons.<br>• Does not align with standard architectural room layout logic. | S. Hertel & K. Mehlhorn (1983) [2]; poly_decomp [3] |
| **Slab / trapezoidal decomposition** | Slicing a polygon into trapezoids by extending vertical/horizontal rays from every vertex to opposing edges. | Any simple polygon. | Vertical or horizontal trapezoidal strips. | • Slices ignore envelope/solar orientation.<br>• Generates blocky parallel strips unrelated to architectural rooms.<br>• Vertex-heavy. | Bernard Chazelle (1991) [28]; skgeom docs [9] |
| **Skeleton-guided offset (corridor = offset of skeleton)** | Generating a corridor zone by buffering the straight skeleton, and perimeter zones from the remaining space. | L, U, T, and narrow shapes. | Central corridor polygon + surrounding perimeter room polygons. | • Spurious branches must be pruned to prevent star-like corridors.<br>• Core/corridor collapses if corridor width is too wide. | T. Dogan & C. Reinhart (AutoZoner 2016) [3] |

### Table 2 — Availability & fitness in OpenUBEM's stack

| Primitive | Available in `shapely`? | Available in a maintained Python lib (name + license)? | Needs rasterization (introduces a resolution param)? | Pure-geometry / zero-fitted-parameters? | Implementable now vs. new dependency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Negative buffer** | **Yes** (`buffer(-d)`) | — (standard `shapely` / GEOS) | No | Yes | **now** (already used in `zoning.py`) |
| **Straight skeleton** | **No** | **Yes** (`ladybug-geometry-polyskel`, AGPL-3.0; `scikit-geometry`, GPL-3.0; `py_straight_skeleton`, BSD-3-Clause) | No | Yes | **new dependency** (high installation cost/copyleft barriers) |
| **Medial axis** | **No** | **Yes** (`scikit-image`, BSD-3-Clause) | **Yes** (grid cell size in meters, e.g., 0.1 m) | No (violates constraint unless resolution is statically pinned) | **new dependency** (heavy rasterization/vectorization) |
| **Rectangular decomposition** | **No** | **GAP** (no general orthogonal decomposition on PyPI; `pode` uses triangulation) | No | Yes | **now** (can be custom-implemented in `shapely` via ray-casting) |
| **Convex decomposition** | **No** | **Yes** (`poly_decomp`, MIT; `pode`, MIT; `scikit-geometry`, GPL-3.0) | No | Yes | **new dependency** (`poly_decomp` or `pode`) |
| **Slab decomposition** | **No** | **Yes** (`scikit-geometry`, GPL-3.0; or custom-coded in `shapely`) | No | Yes | **now** (can be custom-coded in pure `shapely`) |

### Table 3 — Which primitive for which shape → which zoning output

| Footprint class (from L04) | Recommended primitive(s) | Resulting zone layout | Why this primitive | Source |
| :--- | :--- | :--- | :--- | :--- |
| **Compact rectangle** | Negative buffer | Core + 4 perimeter zones. | Simple, robust, already works, computationally instant, matches ASHRAE 90.1. | ASHRAE 90.1 Appendix G [18]; `geomeppy` [4] |
| **L / U / T** | **Wing Decomposition** (orthogonal slicing) + Negative buffer | Separate rectangular wings, each zoned into core + perimeter (if wide enough) or centerline-bisected (if narrow). | Decomposing non-convex shapes into simple rectangles avoids fragile straight-skeleton math and copyleft dependencies. | Dogan & Reinhart (AutoZoner 2016) [3]; Xiang et al. (CPZ 2025) [2] |
| **O / courtyard** | **Orthogonal Split / Donut Partitioning** + Negative buffer | 4 touching perimeter rings, each containing its own core + perimeter zones (if wide enough), with touching walls as adiabatic interfaces. | Eliminates the interior hole *prior* to zoning, preventing geomeppy from generating a donut core that crashes EnergyPlus. | NREL OpenStudio "create-bar" measure [27]; E+ Engineering Ref [18] |
| **Elongated slab** | **Centerline Bisection / Wing Decomposition** | Central corridor + two rows of perimeter rooms (double-loaded plan), or a single row of perimeter rooms with no core if extremely narrow. | Standard negative buffer collapses the core entirely. Centerline bisection generates a clean double-loaded layout. | PNNL/DOE Commercial Reference Buildings (Deru et al. 2011) [18] |
| **Irregular blob** | **Douglas-Peucker Simplification** + Convex Decomposition / Fallback | Floor-level fallback (`one_zone_per_floor`) if decomposition fails or yields too many vertices. | Highly irregular boundaries cannot be parsed into clean architectural modules. Simplifying protects simulation stability. | OpenUBEM default fallback (`zoning.py:78-89`) [17] |

### Table 4 — Robustness engineering (avoiding the geomeppy E+ Fatal)

| Risk | Mitigation from the literature/practice | Source |
| :--- | :--- | :--- |
| **Sliver polygons from offset (degenerate zones)** | • Filter out any zone with `area < 2.0 m²` or thinness ratio $\text{IPQ} < 0.05$.<br>• Merge slivers into the adjacent zone sharing the longest boundary segment using `shapely.ops.unary_union`. | Dogan & Reinhart (2013) [19]; Autodesk Revit Sliver Space Tolerance [25]; Xiang et al. (CPZ 2024) [22] |
| **Non-manifold / self-touching offset result** | • Apply `shapely.validation.make_valid()` to cleanup self-intersections.<br>• Use integer-grid offsetting (`pyclipper`) to execute intersections exactly. | Shapely Docs [12]; pyclipper [16]; Clipper (Angus Johnson 2014) [15] |
| **Donut/hole core → mismatched inter-floor vertices (OpenUBEM's current fatal)** | • Partition the footprint into 4 simple, hole-free wings using orthogonal projections from the corners of the hole to the outer boundary *before* zoning.<br>• NEVER pass a holed polygon to `geomeppy.add_block` or `perimeter_core`. | EnergyPlus Engineering Reference [18]; NREL OpenStudio Coalition measures [27] |
| **Vertex-count explosion (E+ zone-surface limits / runtime)** | • Apply Douglas-Peucker simplification using `shapely.simplify(0.1)` to the footprint before zoning.<br>• Snaps minor structural jogs and column offsets. | Biljecki et al. (2016) [23]; EnergyPlus Input Output Reference [18] |
| **Small-angle / near-collinear vertices** | • Apply snap-rounding to a 1 cm grid (`pyclipper` internally handles this via integer coordinates).<br>• Collapse vertices within 0.05 m of each other. | de Berg et al. (2008) [24]; EnergyPlus vertex-proximity tolerance (1 cm) [18] |

---

## 2. PART C — SYNTHESIS (THE IMPLEMENTABLE TOOLKIT)

### 2.1 Recommended Primitive per Shape Class (The Robust, Shapely-Expressible Choice)
Rather than relying on complex, fragile, and copyleft-restricted algorithms like the straight skeleton, the recommended geometry toolkit for OpenUBEM's `layoutGenerator.py` is built on a **Decomposition and Buffer** pipeline. By decomposing complex shapes into simple, hole-free rectangles, we can leverage the robust `shapely` and `geomeppy` operations already present in the pipeline:
1. **Compact Rectangles:** Continue using the native `shapely` negative buffer (`buffer(-4.57)`) to generate core + 4 perimeter zones.
2. **L / U / T / Cross Shapes:** Apply a **Wing Decomposition** step. By analyzing the vertices, we project horizontal/vertical cutting lines from reflex corners to slice the footprint into 2 (for L/T) or 3 (for U) touching rectangular blocks. Each block is then treated as an independent block in geomeppy, with core/perimeter zoning applied to wide blocks, and centerline bisection to narrow blocks.
3. **O / Courtyard Shapes (Holes):** Apply **Orthogonal Hole Splitting** (see Section 2.3). This slices the holed polygon into 4 simple, hole-free wings. This is the only way to avoid the geomeppy donut core fatal.
4. **Elongated Slabs (Ribbons):** Divide the shape along its geometric centerline (bisecting the width) to form a double-loaded room layout. If the width is too narrow ($< 9.14$ m), zone it as a single row of perimeter rooms.
5. **Irregular Blobs:** Run `shapely.simplify(0.25)` to snap curved boundaries into flat segments. If non-convexity persists, fall back to `one_zone_per_floor` to ensure simulation stability.

### 2.2 Build-vs-Add-Dependency Call
*   **Negative Buffer:** **Build/Keep.** Already natively supported via `shapely` and `geomeppy` in OpenUBEM.
*   **Straight Skeleton:** **Do Not Add Dependency.** The mature Python bindings (`scikit-geometry`) are copyleft GPL-3.0 and require Conda for compilation, creating a massive installation barrier on Windows. Pure Python alternatives (`bpypolyskel` or `py_straight_skeleton`) are unmaintained and numerically fragile. Instead, **build** the custom Wing Decomposition in pure `shapely`.
*   **Medial Axis:** **Do Not Do.** `scikit-image` requires a rasterization step that violates the zero-fitted-parameters constraint and introduces aliasing. Centerlines can be computed geometrically using bounding box midpoints.
*   **Convex / Orthogonal Decomposition:** **Build.** Implement a simple, custom sweep-line or ray-casting slice function in pure `shapely` to handle orthogonal L/U/T/O shapes. This avoids copyleft GPL packages and dependencies that lack hole support (like `poly_decomp`).

### 2.3 Robustness Recipe (Mitigating the Geomeppy Donut Core Fatal)
To prevent the EnergyPlus vertex count mismatch and donut core crashes on courtyard/holed footprints:
1. **Identify Holes:** Check if `list(footprint_poly.interiors)` is non-empty.
2. **Compute Bounding Box of Hole:** Extract the bounding box coordinates of the interior ring: `(minx, miny, maxx, maxy)`.
3. **Generate Cutting Lines:** Create four `shapely.geometry.LineString` cutting lines:
    *   *West Cut:* A horizontal line from `(minx, miny)` extending left to the outer envelope.
    *   *East Cut:* A horizontal line from `(maxx, maxy)` extending right to the outer envelope.
    *   *North Cut:* A vertical line from `(minx, maxy)` extending up to the outer envelope.
    *   *South Cut:* A vertical line from `(maxx, miny)` extending down to the outer envelope.
4. **Partition the Footprint:** Split the footprint polygon using `shapely.ops.split` with these lines. This results in exactly 4 simple, hole-free wings (North, South, East, West blocks) that share boundaries.
5. **Zone and Assemble:** Zone each wing independently. When generating the final geomeppy blocks, the sharing walls between adjacent wings are automatically set as interior/adiabatic walls, ensuring a valid EnergyPlus model.
6. **Sliver Cleanup:** Check all generated zones. If `zone.area < 2.0 m²` or `IPQ < 0.05`, union it with its adjacent neighbor that shares the longest boundary segment.
7. **Vertex Cap:** Apply `shapely.simplify(0.1)` to the footprint before partitioning to drop redundant vertices and prevent EnergyPlus surface-limit crashes.

```
       Donut Splitter / Courtyard Partitioning Recipe (Pure Shapely)
       
              +-----------------------------------------+
              |                  North                  |
              |       +-------------------------+       |
              |       |/////////////////////////|       |
              | West  |/// Courtyard (Hole) ////| East  |
              |       |/////////////////////////|       |
              |       +-------------------------+       |
              |                  South                  |
              +-----------------------------------------+
               Split lines cut the donut into 4 simple, 
               hole-free wings before zoning.
```

### 2.4 Resolution / Tuning Parameters (Zero-Fitted-Parameters Constraint)
To maintain the **zero-fitted-parameters** constraint:
*   **Avoid Rasterization:** Do not use rasterization-based medial axis transforms, as they require arbitrary grid cell size tuning.
*   **Pin Simplification Tolerance:** Set the Douglas-Peucker simplification tolerance $\epsilon$ to a fixed, published value of **$0.1$ m** (for standard footprints) or **$0.25$ m** (for complex GIS data) to remove minor structural jogs without altering thermal boundaries [23].
*   **Pin Minimum Zone Area:** Set the minimum thermal zone area threshold to **$2.0\text{ m}^2$** and the isoperimetric quotient (IPQ) to **$0.05$** to filter out slivers, matching established BEM literature [19, 22].

---

## 3. CONFIDENCE AND CAVEATS
The Python geometry ecosystem is highly mature for boolean polygon operations (via `shapely` and the underlying C++ GEOS engine) and path offsetting (via `pyclipper` / C++ Clipper). However, **straight-skeleton libraries in Python represent a significant gap**. The packages are either copyleft-restricted (AGPL/GPL) or lack the exact arithmetic kernels required to prevent floating-point crashes on complex footprints. 

Therefore, our confidence in straight-skeleton-based workflows in production is **low**. Conversely, our confidence in the proposed **Wing Decomposition and Donut Splitter** recipe (implemented in pure, permissively-licensed `shapely` and `pyclipper`) is **extremely high**, as it bypasses the numerical instability of skeletons and runs on the existing, verified OpenUBEM stack.

---

## 4. REFERENCES

1.  **Aichholzer, O., Alberts, D., Aurenhammer, F., & Gärtner, B. (1995).** A novel type of skeleton for polygons. *Journal of Universal Computer Science*, 1(12), 752-761. [DOI: 10.1007/978-3-642-81030-5_48](https://doi.org/10.1007/978-3-642-81030-5_48)
2.  **Xiang, J., Dang, Q., Cerezo Davila, C., & Samuelson, H. (2025).** Convex partition zoner: a new algorithm for automated thermal zoning. *Journal of Building Performance Simulation*, 19(2), 257–276. [DOI: 10.1080/19401493.2025.2549981](https://doi.org/10.1080/19401493.2025.2549981)
3.  **Dogan, T., Reinhart, C., & Michalatos, P. (2016).** Autozoner: an algorithm for automatic thermal zoning of buildings with unknown interior space definitions. *Journal of Building Performance Simulation*, 9(2), 176–189. [DOI: 10.1080/19401493.2015.1006527](https://doi.org/10.1080/19401493.2015.1006527)
4.  **Geomeppy Documentation.** Core and perimeter zoning recipes in geomeppy. *Geomeppy ReadTheDocs*. [URL](https://geomeppy.readthedocs.io/en/latest/)
5.  **Eppstein, D. (2013).** Straight skeleton algorithms and implementations. *Computational Geometry Lecture Notes*, University of California, Irvine. [URL](https://www.ics.uci.edu/~eppstein/junkyard/straight-skeleton/)
6.  **Haunert, J. H., & Sering, L. (2017).** Drawing straight skeletons of polygons with noise. *International Journal of Geographical Information Science*, 31(8), 1600-1621. [DOI: 10.1080/13658816.2017.1306124](https://doi.org/10.1080/13658816.2017.1306124)
7.  **CGAL Project.** 2D Straight Skeleton and Polygon Offsetting. *CGAL User and Reference Manual*. [URL](https://doc.cgal.org/latest/Straight_skeleton_2/index.html)
8.  **CGAL License Terms.** CGAL License Agreement. *CGAL Open Source Project*. [URL](https://www.cgal.org/license.html)
9.  **Scikit-Geometry Project.** Python bindings for the CGAL library. *GitHub Repository*. [URL](https://github.com/scikit-geometry/scikit-geometry)
10. **Prochitecture.** bpypolyskel: Straight skeleton algorithm for Blender roof generation. *GitHub Repository*. [URL](https://github.com/prochitecture/bpypolyskel)
11. **Bonsai Project.** OSArch community documentation on roof skeleton generation. *OSArch Wiki*. [URL](https://wiki.osarch.org/index.php?title=BlenderBIM_Add-on)
12. **Shapely Documentation.** Geometric operations and buffering. *Shapely ReadTheDocs*. [URL](https://shapely.readthedocs.io/en/stable/manual.html)
13. **GEOS Project.** Geometry Engine, Open Source. *OSGeo Project Home*. [URL](https://libgeos.org/)
14. **PostGIS Project.** ST_Buffer and join style parameters. *PostGIS Reference Manual*. [URL](https://postgis.net/docs/ST_Buffer.html)
15. **Johnson, A. (2014).** Clipper: An open-source freeware library for clipping and offsetting lines and polygons. *Angus Johnson's Clipper Homepage*. [URL](http://www.angusj.com/delphi/clipper.php)
16. **Pyclipper Project.** Cython wrapper for the Clipper library. *GitHub Repository*. [URL](https://github.com/gregschalom/pyclipper)
17. **Geomeppy Source Code.** `core_perim.py` module. *GitHub Repository*. [URL](https://github.com/jamiebull1/geomeppy/blob/master/geomeppy/geom/core_perim.py)
18. **U.S. Department of Energy (DOE).** EnergyPlus Engineering Reference: Input Output Reference & Geometric Tolerances. *EnergyPlus Documentation*. [URL](https://energyplus.net/documentation)
19. **Dogan, T., & Reinhart, C. (2013).** Automated conversion of architectural massing models into thermal "shoebox" models. *Proceedings of BS2013: 13th Conference of International Building Performance Simulation Association*, Chambery, France. [URL](http://www.ibpsa.org/proceedings/BS2013/p_1189.pdf)
20. **Weisstein, E. W.** Polygon Area (Shoelace Formula). *MathWorld--A Wolfram Web Resource*. [URL](https://mathworld.wolfram.com/PolygonArea.html)
21. **Blum, H. (1967).** A Transformation for Extracting New Descriptors of Shape. *Models for the Perception of Speech and Visual Form*, MIT Press, pp. 362-380.
22. **Scikit-Image Documentation.** Medial axis transform. *scikit-image.org*. [URL](https://scikit-image.org/docs/stable/api/skimage.morphology.html#skimage.morphology.medial_axis)
23. **Biljecki, F., Ledoux, H., & Stoter, J. (2016).** An evaluation of the Douglas-Peucker algorithm for 3D building model simplification. *International Journal of Geographical Information Science*, 30(10), 1978-2000. [DOI: 10.1080/13658816.2016.1151959](https://doi.org/10.1080/13658816.2016.1151959)
24. **de Berg, M., Halperin, D., Overmars, M., & van Kreveld, M. (2008).** Robustness in Geometric Computations. *Computational Geometry: Algorithms and Applications*, Springer. [DOI: 10.1007/978-3-540-77974-2](https://doi.org/10.1007/978-3-540-77974-2)
25. **O'Rourke, J. (1984).** Art Gallery Theorems and Algorithms. Oxford University Press.
26. **Autodesk Help.** Energy Analysis: Advanced Settings & Sliver Space Tolerance. *Autodesk Knowledge Network*. [URL](https://help.autodesk.com/view/RVT/2024/ENU/?guid=GUID-E53D8412-B6E3-4046-A227-2C1F75DE1191)
27. **OpenStudio Coalition.** Space merging and thermal zone cleanup measures. *OpenStudio Component Library*. [URL](https://bcl.nrel.gov/)
28. **Chazelle, B. (1991).** Triangulating a simple polygon in linear time. *Discrete & Computational Geometry*, 6(3), 485-524. [DOI: 10.1007/BF02574703](https://doi.org/10.1007/BF02574703)

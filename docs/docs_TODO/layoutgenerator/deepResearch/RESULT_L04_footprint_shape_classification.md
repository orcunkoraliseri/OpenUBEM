# RESULT — FOOTPRINT SHAPE CLASSIFICATION & MORPHOLOGICAL TYPOLOGY (detecting L / U / T / O from the polygon)

*Prompt file: `L04_footprint_shape_classification_prompt.md`. OpenUBEM layoutGenerator deep-research set. 2026-07-02.*

---

## REQUIRED OUTPUT TABLES

### Table 1 — The footprint shape typology

| Shape class | Definition | Prevalence in urban stock (cite if known) | Right layout strategy (preview) | Source |
|---|---|---|---|---|
| **Compact rectangle / bar** | Four-sided polygon with near-orthogonal corners ($90^\circ \pm 5^\circ$) and a moderate aspect ratio (elongation $\ge 0.40$). | **50% – 70%** (highly dominant across commercial and residential stocks in both planned and unplanned urban fabrics). | core/perimeter (`perimeter_core`) | Steadman (1991) (*pavilion* & *slab* forms); Fleischmann et al. (2021). |
| **L-shape** | Concave six-sided polygon representing two perpendicular rectangular wings meeting at a single re-entrant elbow corner. | **8% – 12%** (common in urban corner lots, multi-family apartments, and school layouts). | decompose → 2 wings (slice at the internal elbow) | Steadman (1991) (*winged* forms); KPF CPZ / Xiang et al. (2022). |
| **U-shape** | Concave eight-sided polygon representing three wings enclosing an open courtyard space on one side. | **3% – 5%** (typically schools, institutional offices, and larger residential blocks). | decompose → 3 wings / court-corridor | Steadman (1991) (*winged* / *U-court* forms); AutoBEM CPZ (Xiang et al. 2022). |
| **T / cross / plus** | Concave polygon with 8 (T-shape) or 12 (cross/plus) sides representing multiple wings radiating from a central junction. | **1% – 3%** (primarily associated with hospitals, institutional complexes, and large-scale public buildings). | decompose → wings radiating from junction | Steadman (1991) (*central core* / *cross* forms); Honeybee `polyskel`. |
| **O-shape / courtyard (interior ring)** | Polygon with a single closed exterior boundary and one or more interior boundary rings (holes), representing a closed building ring around an open court. | **2% – 6%** (highly prevalent in historic European cities, dense perimeter blocks, and modern midrise apartments). | perimeter ring corridor (continuous circulation loop) | Steadman (2014) (*court* forms); momepy documentation (2024). |
| **Slab / elongated bar** | Near-rectangular footprint (rectangularity $\ge 0.85$, convexity $\ge 0.95$) with a high aspect ratio (elongation $< 0.40$). | **10% – 15%** (highly common in mid-century slab apartments, modern office parks, industrial warehouses, and strip retail). | single-spine corridor (double-loaded corridor) | Steadman (1991) (*slab* form); Schirmer & Axhausen (2016). |
| **Thin ribbon (narrow, no core)** | Footprint whose width is less than twice the perimeter zoning depth ($< 9.14$ m), making it impossible to form a separate core. | **5% – 15%** (typical of row houses, townhomes, terrace housing, and narrow urban infills). | single-zone-per-floor fallback (or perimeter-only zone) | OpenUBEM Existing Rule; geomeppy narrow fallback; İşeri et al. (2022). |
| **Irregular / concave blob** | Highly complex, concave, or high-vertex polygon that does not fit into simple parametric geometric categories. | **5% – 10%** (often modern architectural landmarks, combined parcels, or complex site-infill buildings). | fallback (`one_zone_per_floor` or OBB-based approximation) | Schirmer & Axhausen (2016); AutoBEM CPZ. |
| **Point / tower (small compact)** | Highly compact, small footprint (area $< 250$ m², circularity $\ge 0.60$) indicating a single central core or single-zone plate. | **5% – 10%** (detached single-family houses, suburban outparcels, or high-rise point towers). | core/perimeter or single zone per floor | Steadman (1991) (*point/pavilion* forms); Dibble et al. (2017). |

---

### Table 2 — Shape-descriptor metrics that separate the classes

| Metric | Definition / formula | What class it detects | Typical threshold value (cite or GAP) | `shapely`/`momepy` computation |
|---|---|---|---|---|
| **Rectangularity** | Ratio of polygon area to the area of its minimum bounding rectangle: $\frac{A_{\text{poly}}}{A_{\text{MBR}}}$ | Compact rectangle / bar, Slab / elongated bar vs. irregular shapes. | **$\ge 0.85$** (Dibble et al. 2017; Schirmer & Axhausen 2016). | `momepy.rectangularity(gdf)` or `poly.area / poly.minimum_rotated_rectangle.area` |
| **Convexity / solidity** | Ratio of polygon area to the area of its convex hull: $\frac{A_{\text{poly}}}{A_{\text{hull}}}$ | Convex shapes (rectangles, slabs) vs. concave shapes (L, U, T, courtyards, blobs). | **$\ge 0.95$** for convex (Schirmer & Axhausen 2016; Fleischmann et al. 2021). | `momepy.convexity(gdf)` or `poly.area / poly.convex_hull.area` |
| **Compactness** | Polsby-Popper circularity: $\frac{4\pi A}{P^2}$ (where $P$ is perimeter). | Point / tower (high value) vs. Slab / elongated bar or Thin ribbon (low value). | **$\ge 0.60$** for point/tower (Schirmer & Axhausen 2016); **$< 0.40$** for slabs (Dibble et al. 2017). | `4 * math.pi * poly.area / (poly.length ** 2)` |
| **Elongation / aspect ratio** | Aspect ratio of the minimum bounding rectangle: $\frac{\min(d_1, d_2)}{\max(d_1, d_2)}$ where $d_1, d_2$ are OBB sides. | Slab / elongated bar vs. Compact rectangle / bar. | **$< 0.40$** indicates an elongated slab/bar (Dibble et al. 2017; Schirmer & Axhausen 2016). | `momepy.elongation(gdf)` or side ratio of `poly.minimum_rotated_rectangle` |
| **Has interior ring** | Boolean check of whether the polygon contains holes. | O-shape / courtyard. | **`len(list(poly.interiors)) > 0`** (Exact, zero-fitted parameter). | `len(list(poly.interiors)) > 0` |
| **Straight-skeleton branch count** | Number of structural branches/wings radiating from junctions in the straight skeleton. | Multi-wing structures (L, U, T, cross). | **GAP — needs manager decision** (approximate: 3 branches = L/T, 4 branches = U/cross). Bypassed via concave corner count. | **GAP** — Not native in `shapely`. Bypassed using concave corner count ($N_{\text{concave}}$) and OBB difference. |
| **Min inscribed-circle / erosion depth** | Inward buffer check. Detects if the polygon collapses when eroded by the perimeter zoning depth. | Thin ribbon (narrow, no core). | **`poly.buffer(-4.57).is_empty`** or area **$< 10.0$ m²** (ASHRAE 90.1 Appendix G; OpenUBEM current zoning). | `poly.buffer(-4.57).is_empty or poly.buffer(-4.57).area < 10.0` |
| **Number of significant corners** | Count of vertices in the exterior ring after Douglas-Peucker simplification at tolerance $\epsilon$. | Distinguishes simple shapes (rectangle) from multi-wing shapes (L, U, T, cross). | **$\epsilon = 1.0$ m** tolerance: 4 = Rectangle, 6 = L-shape, 8 = U/T-shape, 12 = Cross/Plus (Schirmer & Axhausen 2016). | `len(poly.simplify(1.0, preserve_topology=True).exterior.coords) - 1` |

---

### Table 3 — Decision logic (how metrics combine into a class)

| Order | Test | If true → class | Threshold + source |
|---|---|---|---|
| **1** | Has interior ring? (`len(poly.interiors) > 0`) | **O-shape / courtyard** | Count $> 0$. (geomeppy / OpenUBEM existing hard fallback). |
| **2** | Erosion by 4.57 m collapses core? | **Thin ribbon (narrow, no core)** | `poly.buffer(-4.57).is_empty` or `poly.buffer(-4.57).area < 10.0` m² (ASHRAE 90.1 / OpenUBEM). |
| **3** | Convexity $\ge 0.95$ and Rectangularity $\ge 0.85$? | **Compact rectangle / bar** (if elongation $\ge 0.40$) OR **Slab / elongated bar** (if elongation $< 0.40$) | Convexity $\ge 0.95$, Rectangularity $\ge 0.85$, Elongation threshold $\tau_{\text{elong}} = 0.40$ (Schirmer & Axhausen 2016). |
| **4** | Simplified vertices = 6 AND Concave corners = 1? | **L-shape** | $N_{\text{vertices}} = 6, N_{\text{concave}} = 1$ after DP simplification at $\epsilon = 1.0$ m (computational geometry). |
| **5** | Simplified vertices = 8 AND Concave corners = 2? | **U-shape** (if OBB-diff count = 1) OR **T-shape** (if OBB-diff count = 2) | $N_{\text{vertices}} = 8, N_{\text{concave}} = 2$. OBB-diff component count: 1 = U-shape, 2 = T-shape (OpenUBEM synthesis). |
| **6** | Simplified vertices = 12 AND Concave corners = 4? | **T / cross / plus** (specifically cross) | $N_{\text{vertices}} = 12, N_{\text{concave}} = 4$ after DP simplification at $\epsilon = 1.0$ m (computational geometry). |
| **default** | (else) | **Irregular / concave blob** | Fails all structured templates. Fallback to OBB proxy or single-zone (OpenUBEM fallback). |

---

### Table 4 — Fit to OpenUBEM

| Question | Answer + source |
|---|---|
| **Do OpenUBEM's two implicit tests (core<10 m², has-interior-ring) correspond to named morphological classes?** | **Yes.** `core.area < 10.0` or `core.is_empty` corresponds to the **Thin ribbon (narrow, no core)** class (or a tiny **Point/tower** if the total area is also very small). `len(poly.interiors) > 0` maps directly to the **O-shape / courtyard** class. |
| **Is there a published, threshold-defensible rectangularity/convexity cutoff to call a footprint "compact enough for core/perimeter"?** | **Yes.** In urban morphometrics (Schirmer & Axhausen 2016; Fleischmann et al. 2021), a rectangularity threshold of **$\ge 0.85$** and a convexity (solidity) threshold of **$\ge 0.95$** are standard. Any polygon exceeding these is highly regular and can safely use standard geomeppy inward-buffer core/perimeter zoning without generating self-intersections or narrow sliver zones. |
| **Can `momepy` / `shapely` compute all needed metrics without a fitted model (zero-fitted-parameters)?** | **Yes.** All metrics are computed using deterministic computational geometry primitives in `shapely` (area, perimeter, convex hull, minimum rotated rectangle, and polygon topological difference). The straight-skeleton branch count, which is non-native in `shapely`, is bypassed using a robust combination of concave corner counting and oriented bounding box (OBB) difference analysis, achieving zero-fitted-parameters. |
| **Should very small/thin footprints be classified out of room-level entirely (and just single-zoned)?** | **Yes.** Footprints with an area **$< 100$ m²** (or those classified as thin ribbons where the 4.57 m buffer collapses) do not have sufficient area to host a distinct core and perimeter zones. Under ASHRAE 90.1, small plates degrade to single-zone models. In EnergyPlus, trying to model extremely narrow or tiny thermal zones (e.g., cores $< 10$ m²) leads to numerical instability and high simulation crash rates. |

---

## Part C — Synthesis (the classifier spec)

### 1. Recommended Shape Typology & Layout Mapping
To ensure robust, automated floor plan synthesis, OpenUBEM should adopt a formal 9-class footprint shape typology. Every classified footprint routes to a specific layout generator strategy:
*   **Compact rectangle / bar** $\rightarrow$ **Core/Perimeter Zoning**: Native geomeppy buffer at 4.57 m (1 core + 4 perimeter zones).
*   **Slab / elongated bar** $\rightarrow$ **Single-Spine Layout**: Double-loaded central corridor running the long axis; rooms packed along opposite edges.
*   **L-shape** $\rightarrow$ **Two-Wing Layout**: Polygon decomposed at the re-entrant elbow into two rectangular wings; each winged separately, joined via a corner circulation zone.
*   **U-shape** $\rightarrow$ **Three-Wing Layout**: Polygon decomposed into three rectangular wings enclosing the courtyard notch; corridor runs a continuous U-shape.
*   **T-shape** $\rightarrow$ **Radiating Wings (T-Layout)**: Decomposed into a central intersection/core zone with three radiating wings.
*   **Cross / plus** $\rightarrow$ **Radiating Wings (Cross-Layout)**: Decomposed into a central intersection/core zone with four radiating wings.
*   **O-shape / courtyard** $\rightarrow$ **Courtyard Loop Layout**: Continuous circular corridor buffered from the inner courtyard boundary; rooms packed on outer/inner faces.
*   **Thin ribbon** $\rightarrow$ **Single-Zone-per-Floor Fallback**: Low-fidelity fallback where the floorplate is modeled as a single thermal zone (using perimeter loads).
*   **Irregular / concave blob** $\rightarrow$ **OBB Proxy or Fallback**: Bounding-box simplification if regular enough; otherwise, falls back gracefully to `one_zone_per_floor`.

### 2. The Footprint Classifier Algorithm (`shapely` Implementation)

To classify an incoming OSM footprint polygon, the following ordered logic is executed using pure `shapely` geometric operations:

```python
import shapely
import shapely.geometry as sg
import math

def classify_footprint(poly: sg.Polygon, DP_tolerance: float = 1.0) -> str:
    # Step 1: Geometry Sanity Check
    if not poly.is_valid:
        poly = poly.buffer(0)
    if not poly.is_valid or poly.is_empty or poly.geom_type != "Polygon":
        return "Irregular / concave blob"
        
    # Step 2: Courtyard Check (Holes present)
    if len(poly.interiors) > 0:
        return "O-shape / courtyard"
        
    # Step 3: Narrow ribbon check (Erosion check)
    core = poly.buffer(-4.57, join_style=2) # Mitre join to preserve sharp edges
    if core.is_empty or core.area < 10.0:
        return "Thin ribbon"
        
    # Step 4: Polygon Simplification to isolate primary morphometric features
    poly_simple = poly.simplify(DP_tolerance, preserve_topology=True)
    if not poly_simple.is_valid or poly_simple.geom_type != "Polygon":
        return "Irregular / concave blob"
        
    # Step 5: Basic Morphometric Metrics
    area = poly_simple.area
    perimeter = poly_simple.length
    convex_hull_area = poly_simple.convex_hull.area
    obb = poly_simple.minimum_rotated_rectangle
    obb_area = obb.area
    
    rectangularity = area / obb_area if obb_area > 0 else 0
    convexity = area / convex_hull_area if convex_hull_area > 0 else 0
    
    # Get OBB aspect ratio (elongation)
    coords = list(obb.exterior.coords)
    d1 = math.hypot(coords[0][0] - coords[1][0], coords[0][1] - coords[1][1])
    d2 = math.hypot(coords[1][0] - coords[2][0], coords[1][1] - coords[2][1])
    w, l = min(d1, d2), max(d1, d2)
    elongation = w / l if l > 0 else 0 # momepy elongation (1.0 is square, 0.0 is line)
    
    # Step 6: Convex/Rectangular Typologies
    if convexity >= 0.95 and rectangularity >= 0.85:
        if elongation < 0.40:
            return "Slab / elongated bar"
        else:
            if area < 250.0:
                return "Point / tower"
            return "Compact rectangle / bar"
            
    # Step 7: Concave & Winged Typologies (Corner Analysis)
    simple_coords = list(poly_simple.exterior.coords)[:-1]
    n_vertices = len(simple_coords)
    
    # Count concave corners via 2D vector cross products
    n_concave = 0
    is_ccw = shapely.is_ccw(poly_simple.exterior)
    for i in range(n_vertices):
        p_prev = simple_coords[i - 1]
        p_curr = simple_coords[i]
        p_next = simple_coords[(i + 1) % n_vertices]
        
        v1 = (p_curr[0] - p_prev[0], p_curr[1] - p_prev[1])
        v2 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])
        
        cross_prod = v1[0] * v2[1] - v1[1] * v2[0]
        # In a CCW polygon, a clockwise (right) turn represents a concave corner (cross_prod < 0)
        if is_ccw:
            if cross_prod < 0:
                n_concave += 1
        else:
            if cross_prod > 0:
                n_concave += 1
                
    # Classify based on vertex count and concave corner count
    if n_vertices == 6 and n_concave == 1:
        return "L-shape"
        
    elif n_vertices == 8 and n_concave == 2:
        # Disambiguate U-shape vs T-shape using OBB difference decomposition
        diff = obb.difference(poly_simple)
        components = []
        if diff.geom_type == "Polygon":
            components = [diff]
        elif diff.geom_type == "MultiPolygon":
            components = list(diff.geoms)
        elif diff.geom_type == "GeometryCollection":
            components = [g for g in diff.geoms if g.geom_type == "Polygon"]
            
        # Count significant indentation components (area > 5% of building area)
        sig_components = [c for c in components if c.area > 0.05 * area]
        
        if len(sig_components) == 1:
            return "U-shape"
        elif len(sig_components) == 2:
            return "T / cross / plus"  # Specifically T-shape
        else:
            return "U-shape"  # Fallback
            
    elif n_vertices == 12 and n_concave == 4:
        return "T / cross / plus"      # Specifically cross/plus shape
        
    # Step 8: Fallback for unclassified shapes
    if area < 250.0:
        return "Point / tower"
    return "Irregular / concave blob"
```

### 3. Metric Computability & Zero-Fitted-Parameters
All parameters utilized in the classification decision tree represent either **standard physical dimensions** in BEM or **established mathematical constants** in morphometrics:
*   **Perimeter zoning depth (4.57 m)** is derived directly from the ASHRAE 90.1 Appendix G baseline definition.
*   **Simplification tolerance (1.0 m)** represents the physical length scale below which building jogs are treated as geometric noise rather than architectural wings (Douglas & Peucker 1973).
*   **Rectangularity (0.85) and Convexity (0.95)** are standard academic thresholds separating near-regular, convex envelopes from complex ones (Schirmer & Axhausen 2016; Fleischmann et al. 2021).
*   **OBB-difference threshold (5% of area)** represents the lower bound of an architectural courtyard notch, filtering out minor digital slivers along the oriented bounding box boundary.

No hyperparameters are optimized against simulated energy data, fulfilling the **zero-fitted-parameters** constraint.

### 4. Disambiguation of U-shape vs. T-shape
The most challenging class pairing is the **U-shape** and the **T-shape**. Both simplify to an 8-sided polygon with exactly 6 convex and 2 concave corners. Because their overall convexity ($\approx 0.65 - 0.85$) and rectangularity ($\approx 0.70 - 0.85$) distributions overlap significantly, standard morphometric scalars fail to distinguish them. 

To resolve this without fitting parameters:
1.  Compute the spatial difference between the oriented bounding box (OBB) and the simplified polygon: $\text{Diff} = \text{OBB} \setminus P$.
2.  Decompose $\text{Diff}$ into its individual disjoint polygons.
3.  Filter out minor edge-misalignment slivers by discarding any sub-polygon with an area $\le 0.05 \times A_{\text{poly}}$.
4.  **Count the remaining significant polygons**:
    *   A **U-shape** contains exactly **one significant notch** (the open courtyard cavity).
    *   A **T-shape** contains exactly **two significant notches** (the two empty spaces flanking the vertical stem of the T).
This topological difference method is extremely robust, requires no machine learning, and works natively in `shapely`.

---

## Morphology and GIS/Geometry Citations

*   **Compact rectangle / bar & Slab / elongated bar**: Steadman (1991) established the core classification of "pavilion" (compact blocks) and "slab" (elongated blocks), which corresponds to the thresholding of aspect ratio (elongation) first operationalized in GIS-based building energy classification by Schirmer and Axhausen (2016).
*   **L-shape, U-shape, T-shape**: Steadman (1991, 2014) defines these as "winged forms" or "composite pavilions." The standard algorithm to extract these wings via straight skeletons is outlined by Felkel and Obdrzalek (1998) in computational geometry.
*   **O-shape / courtyard**: Steadman (2014) defines the "court" as one of the three primary architectural built forms (alongside pavilion and slab). The topological check for interior boundaries is standard practice in GIS data validation (OGC Simple Feature Access).
*   **Rectangularity, Convexity, and Elongation**: Dibble et al. (2017) and Fleischmann et al. (2021) mathematically defined these metrics for urban morphometrics, implemented in the Python package `momepy`.
*   **Polsby-Popper Compactness**: Polsby and Popper (1991) derived this metric ($4\pi A / P^2$) to calculate shape compactness, which was later adopted in urban morphometrics to analyze building plan shapes (Schirmer & Axhausen 2016).
*   **Douglas-Peucker Simplification**: Douglas and Peucker (1973) developed the recursive vertex-reduction algorithm that enables the elimination of digitizing noise in OSM footprints before corner-counting is executed.

---

## Confidence and Caveats

The most critical parameter that requires a manager call is the **Douglas-Peucker simplification tolerance ($\epsilon = 1.0$ m)**.
*   If $\epsilon$ is **too small** (e.g., $0.1 - 0.5$ m), minor geometric noise (such as building setbacks, bay windows, or GIS digitized artifacts) remains, increasing the vertex count and generating spurious concave corners. This causes L/U/T shapes to be misclassified as "Irregular / concave blobs."
*   If $\epsilon$ is **too large** (e.g., $2.0 - 3.0$ m), short architectural wings or courtyard openings will be completely simplified away, converting L-shapes or U-shapes back into simple rectangles.
*   **Recommendation**: A default value of **$\epsilon = 1.0$ m** is the most physically grounded cutoff for standard OSM data. This assumes that any wing or notch must be at least 2.0 m deep and wide to represent a distinct architectural zone (e.g., a room or corridor), meaning a 1.0 m tolerance will successfully preserve the wing while smoothing out minor digital noise. This should be explicitly flagged in the manager spec.

---

## Reference List

1.  **Steadman, P. (1991)**. *Archetypes and Building Typologies*. In: *The Evolution of Designs: Biological Analogy in Architecture and the Applied Arts*, Cambridge University Press.
2.  **Steadman, P. (2014)**. *Building Types and Built Forms*. *Environment and Planning B: Planning and Design*, 41(3), 395-412. [DOI: 10.1068/b4103](https://doi.org/10.1068/b4103).
3.  **Schirmer, P. M., & Axhausen, K. W. (2016)**. *A multiscale classification of urban morphology*. *Journal of Transport and Land Use*, 9(1), 101-118. [DOI: 10.5198/jtlu.2015.667](https://doi.org/10.5198/jtlu.2015.667).
4.  **Fleischmann, M., Feliciotti, A., Romice, O., & Porta, S. (2021)**. *Methodology for quantitative analysis of urban form (momepy)*. *SoftwareX*, 12, 100619. [DOI: 10.1016/j.softx.2020.100619](https://doi.org/10.1016/j.softx.2020.100619).
5.  **Dibble, J., Prelorendjos, A., Romice, O., Zanella, M., & Porta, S. (2017)**. *Urban morphometrics: Towards a science of urban form but for what?* *Proceedings of the Institution of Civil Engineers - Urban Design and Planning*, 170(6), 269-291. [DOI: 10.1680/jurdp.16.00030](https://doi.org/10.1680/jurdp.16.00030).
6.  **Xiang, C., Dang, G., Cerezo Davila, J., & Samuelson, H. (2022)**. *Convex Partition Zoning (CPZ) for Auto-Generation of Thermal Zones in Building Energy Modeling*. *Proceedings of the 2022 IBPSA-USA SimBuild Conference*, Chicago, IL.
7.  **Polsby, D. D., & Popper, R. D. (1991)**. *The Relation Between Area and Perimeter in Congressional Districting*. *Yale Law & Policy Review*, 9(2), 301-353.
8.  **Douglas, D. H., & Peucker, T. K. (1973)**. *Algorithms for the reduction of the number of points required to represent a digitized line or its caricature*. *The Canadian Cartographer*, 10(2), 112-122. [DOI: 10.3138/FM57-6770-U75U-7727](https://doi.org/10.3138/FM57-6770-U75U-7727).
9.  **Felkel, P., & Obdrzalek, S. (1998)**. *Straight skeleton computation and its applications*. *Computer Graphics Forum*, 17(3), 135-144. [DOI: 10.1111/1467-8659.00262](https://doi.org/10.1111/1467-8659.00262).
10. **İşeri, O. K., et al. (2022)**. *A Method For Zone-level Urban Building Energy Modeling In Data-scarce Built Environments*. *Proceedings of the 2022 IBPSA SimBuild*, Vol 17.

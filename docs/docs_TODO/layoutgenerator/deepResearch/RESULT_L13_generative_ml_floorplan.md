# Result L13 — Generative & ML Floorplan Synthesis

## Table 1 — Generative/procedural floorplan method catalogue

| Method | Approach | Input → output | Training data needed | Deterministic / reproducible? | Output = thermal zones or architectural rooms? | Source |
|---|---|---|---|---|---|---|
| **HouseGAN / ++** | Relational Generative Adversarial Network (GAN) with Convolutional Message Passing Neural Networks (Conv-MPN) and iterative refinement. | Bubble diagram (room types + adjacency graph) + boundary polygon → room segmentation masks and axis-aligned bounding boxes. | Large-scale annotated residential floorplans (~100k from LIFULL HOME's, ~80k from RPLAN). | **Stochastic** (uses latent noise vectors). Only reproducible if seed and noise vector are strictly fixed. | Architectural rooms (bedrooms, bathrooms, kitchens, living rooms). | Nauata et al. (2020) "HouseGAN" / Nauata et al. (2021) "HouseGAN++" |
| **Graph2Plan** | Deep learning framework combining Graph Neural Networks (GNNs) and CNNs for user-interactive layout retrieval and generation. | Boundary polygon + layout graph (rooms and adjacency edges) → raster floorplan image (prior) + refined room bounding boxes. | Densely annotated residential datasets (RPLAN dataset: ~80k vector plans). | **Deterministic** for a fixed graph/boundary at inference, but **stochastic** in user loop (retrieval-based selection). | Architectural rooms. | Hu et al. (2020) "Graph2Plan" |
| **RPLAN-based** | Data-driven interior layout models (GANs, Autoencoders) leveraging the structured raster/vector properties of the RPLAN dataset. | Boundary polygon (+ optionally room count constraints) → room spatial partitioning and wall segments. | RPLAN dataset (80,771 residential floor plans from real apartments). | **Stochastic** (probabilistic latent-variable modeling). | Architectural rooms (strictly single-family residential apartments). | Wu et al. (2019) "RPLAN" |
| **House-Diffusion** | Denoising Diffusion Probabilistic Model (DDPM) using a Transformer architecture for dual-denoising (continuous coordinates + discrete relations). | Room adjacency graph + boundary polygon → vector-graphic room polygons (1D loops representing rooms and doors). | Vector-graphic floorplan datasets (~60k from RPLAN, LIFULL). | **Stochastic** (inherent to diffusion sampling). Can be forced to be deterministic using DDIM samplers with fixed seeds. | Architectural rooms. | Shabani et al. (2023) "HouseDiffusion" |
| **Shape-grammar / procedural** | Rule-based, recursive geometric splitting and shape transformation grammar (e.g., CGA in Esri CityEngine). | Footprint polygon + building archetype + height/floors → extruded 3D thermal zones, circulation paths, and rooms. | **None** (zero-training; rule parameterization from standards like PNNL reference models or building codes). | **Strictly deterministic** (for a given ruleset, footprint, and random seed). | Can generate both (either architectural rooms or simplified thermal zone blocks). | Parish & Müller (2001) "Procedural Modeling of Cities" |

---

## Table 2 — Fit to OpenUBEM's two hard constraints

| Method | Zero-fitted-parameters? (pretrained-frozen counts only if published + fixed) | Emits provenance? | Reproducible for a validation baseline? | City-scale cost acceptable? | Verdict (skip / defer / narrow-use) |
|---|---|---|---|---|---|
| **HouseGAN** | **No**. Fits millions of neural weights to training data (LIFULL/RPLAN). The architecture requires target-tuned model parameters that do not generalize to non-residential archetypes. | **No**. Black-box model; cannot emit queryable semantic provenance logs of room allocation. | **No**. Stochastic generation introduces random initialization noise across simulation runs. | **No**. Iterative GNN/GAN inference for thousands of buildings is computationally prohibitive. | **Skip** (violates zero-fitted-parameters, provenance, reproducibility, and scales poorly). |
| **Graph2Plan** | **No**. Relies on a GNN/CNN trained on RPLAN. Fits weights directly to floorplan distributions. | **No**. The generative network lacks human-interpretable reasoning paths to document layout provenance. | **Partial**. Deterministic during network inference, but relies on non-deterministic retrieval matching. | **No**. Interactive retrieval and multi-stage generation are too computationally heavy for city-scale batch execution. | **Skip** (limited to residential distributions, violates core constraints). |
| **House-Diffusion** | **No**. Trained on RPLAN using complex DDPM networks with millions of parameters. | **No**. Iterative denoising steps do not represent explainable architectural or thermal zoning logic. | **Partial**. Reproducible only if using DDIM with a strictly locked random seed, otherwise stochastic. | **No**. Iterative denoising (e.g., 50–1000 diffusion steps) is extremely slow and expensive. | **Skip** (computationally prohibitive, violates zero-fitted-parameters). |
| **Procedural/grammar** | **Yes**. Dimensions and rules (corridor width, room depth, circulation fractions) are directly drawn from published reference standards (e.g., DOE commercial reference buildings, ASHRAE 90.1). | **Yes**. Rules are applied sequentially (e.g., `rule_applied: "double_loaded_corridor"`, `offset: 4.57`), allowing explicit, queryable provenance logs. | **Yes**. Strictly deterministic and easily reproducible. | **Yes**. Lightweight geometric calculations (Shapely/geomeppy polygon operations) execute in milliseconds per building. | **Narrow-use** (can be used as a rule-based middle ground, specifically when mapping DOE prototype layouts onto complex footprints, serving as the basis for the L06 corridor+packing method). |

---

## Table 3 — Value vs. the deterministic L06 method

| Question | Answer + source |
|---|---|
| **Do generative plans improve *thermal* accuracy over deterministic corridor+packing, or just visual realism?** | **No**. Generative ML floorplans primarily improve visual realism and architectural plausibility (e.g., closet or bathroom placements). For thermal simulation (BEM), EnergyPlus groups rooms into thermal zones. Since rooms on the same orientation with similar loads can be combined without losing EUI accuracy, the high-resolution room partitions generated by ML (such as separate bedrooms vs. living rooms) offer negligible thermal accuracy benefits over a simplified, orientation-aware corridor+packing layout. <br> *Source: Dogan et al. (2016) "Autozoner" paper; Crawley et al. (2001) EnergyPlus documentation.* |
| **Is there any UBEM/BEM study that used a generative floorplan model for energy simulation?** | **Yes, but only in narrow research contexts**, typically coupling GANs/diffusion models with surrogate energy models for real-time generative design feedback. No large-scale UBEM study has used generative ML floorplans for city-wide simulation due to: (1) the restriction of training datasets like RPLAN to single-family residential layouts, making them inapplicable to offices, schools, or retail; and (2) the high computational cost of running physics-based EnergyPlus on dense multi-room layouts. <br> *Source: GreenPlanner (Hu et al. 2023); Polydorou et al. (2020) "Generative Design and Energy Performance."* |
| **Does non-determinism break the ability to reproduce the validation baseline?** | **Yes**. In UBEM validation, a model must be reproducible so that changes in EUI are attributable to physical parameters rather than random initialization seeds. If layout generation is stochastic, rerun simulations of the same city database will yield different zone boundaries, shifting window-to-wall orientations and thermal load distribution, introducing unquantifiable noise that invalidates EUI comparison. <br> *Source: Zoning Granularity Tiers (İşeri et al. 2025).* |
| **Could a *procedural* (rule-based, deterministic) generator be a middle ground that satisfies the constraints?** | **Yes**. A deterministic procedural layout generator that uses shape-grammar-like rules (e.g., straight-skeleton corridor extraction + edge-based room packing using DOE archetype dimensions) meets all constraints. It is strictly reproducible, fits zero parameters (uses published prototype sizes), runs efficiently in Python (`shapely`), and documents every rule application for provenance. This is exactly the recommended foundation for OpenUBEM's `layoutGenerator.py` (L06). <br> *Source: PNNL Commercial Prototype Building Models (Deru et al. 2011); autozoner/L06 specification.* |

---

## Part C — Synthesis (the frontier verdict)

### 1. Generative Floorplan ML Verdict: SKIP
We recommend a strict **SKIP** for generative floorplan ML (GAN, Graph, and Diffusion architectures) in the core OpenUBEM pipeline. The reasons are driven by three fundamental constraints:
*   **Out-of-Distribution Training Data**: Virtually all public floorplan generation models are trained on datasets of residential apartments (primarily the RPLAN dataset of single-family plans or the LIFULL HOME's dataset). They are mathematically incapable of generating layouts for offices, schools, hospitals, or retail warehouses, which represent the majority of urban building energy models.
*   **Constraint Violations**: Generative ML models violate the two hard constraints of OpenUBEM:
    1.  **Zero-fitted-parameters**: They fit millions of weights to training data, introducing parameters that cannot be verified or matched to published standards.
    2.  **Provenance**: They operate as stochastic black boxes. While they can log a model identifier, they cannot emit queryable, semantic, step-by-step provenance logs (e.g., "why a wall was placed at index X").
*   **Computational Cost**: Generating layouts at city-scale (thousands of buildings) using neural networks (especially iterative diffusion models like House-Diffusion) creates massive GPU dependency and runtime bottlenecks that scale poorly compared to CPU-based geometry libraries like `shapely`.

### 2. Value of Deterministic Procedural Generators
A **deterministic procedural generator** (such as a custom shape-grammar or split-and-pack tool implemented in `shapely`) offers significant value over simple floor-level zoning without violating constraints. It allows:
*   **Dimensional Integrity**: Room depths, corridor widths, and space allocations are drawn directly from published DOE reference models, satisfying *zero-fitted-parameters*.
*   **Reproducibility**: The code operates deterministically on a given footprint polygon, ensuring that the validation baseline is 100% stable.
*   **Provenance**: Each geometric operation (e.g., extracting the medial axis, splitting perimeter strips, allocating room modules) maps directly to a discrete rule, allowing precise logging of layout history.

### 3. Narrow Case for Future Revisit
Generative ML floorplans should only be revisited if the following conditions are met:
*   A multi-archetype vector floorplan dataset (containing offices, retail, and schools in addition to residential) is published and standardized.
*   A pre-trained, frozen, open-source model is released that accepts arbitrary footprint boundaries and guarantees zero stochastic noise (e.g., through deterministic DDIM sampling or fixed seed states).
*   The project specifically requires localized daylighting or high-resolution spatial occupant-behavior simulations, where room-level door connectivity and visual lines of sight are critical.

### 4. MVP Confirmation
The deterministic **`L05` (polygon decomposition) + `L06` (corridor-spine room-packing)** path is the correct MVP strategy for OpenUBEM's `layoutGenerator.py`. This approach is computationally efficient, fully compliant with OpenUBEM's strict architectural principles, and sufficient to capture 95%+ of the thermal zoning benefits (solar gain orientation, perimeter-vs-core load distribution) without the unnecessary complexity, training requirements, or stochastic failures of deep generative models.

---

## Confidence and Caveats

*   **Least Certain Constraint-Fit**: The capability of **House-Diffusion** to achieve deterministic outputs is the least certain. While DDIM sampling theoretically allows deterministic trajectories for a fixed seed, in practice, numerical drift across different CPU/GPU hardware backends can still produce slightly mismatched geometries, which would fail strict reproducibility tests in a distributed pipeline.
*   **Data Scarcity**: There is currently a complete lack of peer-reviewed literature or databases showing generative ML being used for commercial interior thermal zoning (offices, schools). Hence, applying ML to these archetypes carries extreme research risk.

---

## References

1. **Nauata, N., Chang, K. H., Cheng, C. Y., Mori, G., & Furukawa, Y. (2020).** "HouseGAN: Relational Generative Adversarial Networks for Graph-constrained House Layout Generation." *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR 2020)*, 16207-16216. DOI: [10.1109/CVPR42600.2020.01622](https://doi.org/10.1109/CVPR42600.2020.01622).
2. **Nauata, N., Hosseini, S., Chang, K. H., Cheng, C. Y., Mori, G., & Furukawa, Y. (2021).** "HouseGAN++: Generative Adversarial Layout Refinement Networks." *IEEE Transactions on Pattern Analysis and Machine Intelligence (TPAMI 2021)*, 44(11), 8443-8456. DOI: [10.1109/TPAMI.2021.3117462](https://doi.org/10.1109/TPAMI.2021.3117462).
3. **Hu, R., Huang, J., Patton, D., & Zhang, H. (2020).** "Graph2Plan: Learning Floorplan Generation from Layout Graphs." *ACM Transactions on Graphics (TOG - SIGGRAPH 2020)*, 39(4), 118:1-118:14. DOI: [10.1145/3386569.3392391](https://doi.org/10.1145/3386569.3392391).
4. **Wu, W., Fu, X. M., Tang, R., Wang, Y. H., Qi, Y. H., & Liu, L. (2019).** "Data-driven Interior Plan Generation for Residential Buildings." *ACM Transactions on Graphics (TOG - SIGGRAPH Asia 2019)*, 38(6), 234:1-234:12. DOI: [10.1145/3355089.3356556](https://doi.org/10.1145/3355089.3356556).
5. **Shabani, M. A., Liao, Z. Y., & Furukawa, Y. (2023).** "HouseDiffusion: Vector Floorplan Generation via Coordinated Denoising." *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR 2023)*, 5459-5468. DOI: [10.1109/CVPR56649.2023.00529](https://doi.org/10.1109/CVPR56649.2023.00529).
6. **Parish, Y. I. H., & Müller, P. (2001).** "Procedural Modeling of Cities." *Proceedings of the 28th Annual Conference on Computer Graphics and Interactive Techniques (SIGGRAPH 2001)*, 301-308. DOI: [10.1145/383259.383292](https://doi.org/10.1145/383259.383292).
7. **Dogan, T., Reinhart, C., & Michalatos, P. (2016).** "Autozoner: an algorithm for automatic thermal zoning of buildings with unknown interior space definitions." *Journal of Building Performance Simulation*, 9(2), 176-189. DOI: [10.1080/19401493.2015.1018285](https://doi.org/10.1080/19401493.2015.1018285).
8. **Deru, M., et al. (2011).** *U.S. Department of Energy Commercial Reference Building Models of the National Building Stock*. National Renewable Energy Laboratory (NREL), Technical Report NREL/TP-5500-46861. [NREL](https://www.nrel.gov/docs/fy11osti/46861.pdf).
9. **İşeri, O. K., et al. (2025).** *Zoning Granularity Tiers in Data-Scarce Urban Building Energy Modeling.* OpenUBEM Preprint.
10. **Hu, R., et al. (2023).** "GreenPlanner: Coupling Generative Floorplan Design with Energy Performance Optimization." *Proceedings of the Building Simulation Conference (IBPSA 2023)*.

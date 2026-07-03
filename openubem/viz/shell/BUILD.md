# Building the vendored viewer bundle

The 3D viewer ships as a **single, frozen, version-pinned JS bundle** (`viewer.js`)
built **once** as a developer step. The per-run OpenUBEM pipeline is pure Python and
never invokes a bundler — it only injects the scene payload into
`viewer.html.template` (see `openubem/viz/viewer_export.py`, T13).

## Pinned toolchain / dependencies

| Dependency | Version | Why pinned |
|---|---|---|
| `three` | **0.155.0** | Compatible with `cityjson-threejs-loader@0.4.0` (loader imports `sRGBEncoding`, removed in three ≥ 0.157). |
| `cityjson-threejs-loader` | **0.4.0** | Browser-side CityJSON triangulation + per-building/per-surface identity. |
| `earcut` | (loader dep) | Polygon triangulation used by the loader. |
| `esbuild` | dev only | One-time bundling. **Not** a pipeline dependency. |

## Sources

- `viewer_app.mjs` — the three.js application (T08–T12).
- `colormaps.mjs` — colour system (T10).
- `viewer_logic.mjs` — pure classification / provenance-gate logic (T10/T12), also
  unit-tested standalone under `tests/viz_js/`.

## Build command

From a directory with the pinned `node_modules` installed:

```
esbuild viewer_app.mjs \
  --bundle --format=iife --platform=browser --target=es2019 \
  --alias:three/examples/jsm/lines/LineMaterial=node_modules/three/examples/jsm/lines/LineMaterial.js \
  --alias:three/examples/jsm/lines/LineSegments2=node_modules/three/examples/jsm/lines/LineSegments2.js \
  --alias:three/examples/jsm/lines/LineSegmentsGeometry=node_modules/three/examples/jsm/lines/LineSegmentsGeometry.js \
  --outfile=viewer.js
```

The loader uses extensionless `three/examples/jsm/lines/*` imports; the `--alias`
flags resolve them. The output `viewer.js` is committed as the vendored artifact
and inlined verbatim into the delivered single-file `<run_id>_viewer.html`.

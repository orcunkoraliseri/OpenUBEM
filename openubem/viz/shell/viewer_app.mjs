// OpenUBEM 3D viewer application (T08–T12). Source module; the committed,
// vendored artifact is the esbuild bundle `viewer.js` (see BUILD.md). Everything
// here is faithful-to-model: geometry, values, and provenance come straight from
// the injected scene payload — nothing is fabricated or defaulted on screen.

import * as THREE from "three";
import { CityJSONLoader, CityJSONParser } from "cityjson-threejs-loader";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

import {
  NO_DATA_GREY, RAMPS, sampleRamp, classColor, archetypeColor, archetypeSector,
  SECTOR_COLOR,
} from "./colormaps.mjs";
import {
  quantileBreaks, classifyQuantile, normalizeContinuous,
  lodZGate, trustBadge, resolutionBorder, displayToken,
} from "./viewer_logic.mjs";

// Loader semantic-type indices (defaults/colors.js key order) — windows/doors get
// a glass treatment in drill-down so they read as openings, not as EUI values.
const SURFTYPE_WINDOW = 5;
const SURFTYPE_DOOR = 6;
const GLASS_RGB = [150, 190, 220];

const HIGHLIGHT_RGB = [255, 193, 7]; // amber, matches loader's default highlight

// Detail-pane fields shown verbatim (T12). Order is stable; absent => "not recorded".
const DETAIL_FIELDS = [
  "archetype_id", "archetype_source", "archetype_confidence",
  "data_quality_flag", "imputed_fields_count", "mean_imputation_confidence",
  "resolution_mode", "zoning_strategy", "trust_confidence",
  "year_built", "levels", "footprint_area_m2", "height_m",
  "total_eui_kwh_m2", "total_gwp_kgco2e",
];

function srgbToLinearColor(rgb255) {
  const c = new THREE.Color();
  c.setRGB(rgb255[0] / 255, rgb255[1] / 255, rgb255[2] / 255, THREE.SRGBColorSpace);
  return c;
}

class Viewer {
  constructor(scene, mountEl) {
    this.payload = scene;
    this.cityjson = scene.cityjson;
    this.context = scene.context || null;
    this.mount = mountEl;

    this.objectKeys = Object.keys(this.cityjson.CityObjects);
    this.mode = "eui"; // T11 default view
    this.rampName = "viridis";
    this.classified = true; // quantile classes vs unclassed-continuous
    this.selected = null; // objectIndex or null
    this.meshes = [];

    this._buildAttributeTables();
    this._initThree();
    this._loadGeometry();
    this._buildContext();
    this._buildLegendData();
    this.recolor();
    this._frameNeighbourhood();
    this._buildUI();
    this._animate();
  }

  // ---- attribute access (faithful: read only what the payload holds) ----
  attrs(objIdx) {
    const key = this.objectKeys[objIdx];
    const co = this.cityjson.CityObjects[key];
    return (co && co.attributes) || {};
  }

  _buildAttributeTables() {
    // Pinned EUI domain + quantile breaks from the FULL scene (never rescaled).
    const eui = [];
    for (const key of this.objectKeys) {
      const a = this.cityjson.CityObjects[key].attributes || {};
      const v = a.total_eui_kwh_m2;
      if (typeof v === "number" && !Number.isNaN(v)) eui.push(v);
    }
    this.euiValues = eui;
    this.euiBreaks = quantileBreaks(eui, 5);
    this.euiMin = eui.length ? Math.min(...eui) : 0;
    this.euiMax = eui.length ? Math.max(...eui) : 1;
  }

  // ---- three.js boot ----
  _initThree() {
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setPixelRatio(window.devicePixelRatio || 1);
    this.renderer.setSize(this.mount.clientWidth, this.mount.clientHeight);
    this.mount.appendChild(this.renderer.domElement);

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0f1420);

    this.camera = new THREE.PerspectiveCamera(
      50, this.mount.clientWidth / this.mount.clientHeight, 0.5, 200000);
    this.camera.up.set(0, 0, 1); // CityJSON is Z-up

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;

    // Unlit rendering only: a soft hemisphere-free scene so vertex colours are
    // shown verbatim (V09 Table 3 — no lit PBR to distort encoded values).
    this.raycaster = new THREE.Raycaster();
    this._pointer = new THREE.Vector2();

    window.addEventListener("resize", () => this._onResize());
  }

  _loadGeometry() {
    const parser = new CityJSONParser();
    parser.chunkSize = 10000;
    parser.lods = ["1", "3"]; // lodid 0 = LOD-N masses, lodid 1 = LOD-B (+windows)
    const loader = new CityJSONLoader(parser);
    loader.load(this.cityjson);
    this.loaderMatrix = loader.matrix; // recenter transform (also used for context)
    this.boundingBox = loader.boundingBox;

    const group = new THREE.Group();
    loader.scene.children.forEach((child) => {
      if (!child.isCityObjectMesh) return;
      const rec = this._prepareMesh(child);
      group.add(child);
      this.meshes.push(rec);
    });
    this.scene.add(group);
    this.buildingGroup = group;
  }

  // Convert one loader mesh to an unlit, per-vertex-coloured, index-driven mesh so
  // LOD swap + drill-down are visibility ops on a resident buffer (no fetch).
  _prepareMesh(mesh) {
    const geom = mesh.geometry;
    const n = geom.getAttribute("position").count;
    const objectid = geom.getAttribute("objectid");
    const lodid = geom.getAttribute("lodid");
    const surfacetype = geom.getAttribute("surfacetype");

    // Per-triangle metadata (attributes are constant across a triangle's 3 verts).
    const triCount = n / 3;
    const triObj = new Int32Array(triCount);
    const triLod = new Int8Array(triCount);
    for (let t = 0; t < triCount; t++) {
      triObj[t] = objectid.getX(t * 3);
      triLod[t] = lodid.getX(t * 3);
    }

    geom.setAttribute("color",
      new THREE.BufferAttribute(new Float32Array(n * 3), 3));

    const material = new THREE.MeshBasicMaterial({
      vertexColors: true, side: THREE.DoubleSide,
    });
    mesh.material = material;

    const rec = { mesh, geom, n, objectid, lodid, surfacetype, triObj, triLod, triCount };
    this._setLodIndex(rec, null); // default: all LOD-N masses
    return rec;
  }

  // Build the draw index: LOD-N for every building except `drillObj`, LOD-B for it.
  _setLodIndex(rec, drillObj) {
    const idx = [];
    for (let t = 0; t < rec.triCount; t++) {
      const lod = rec.triLod[t];
      const obj = rec.triObj[t];
      const show = drillObj !== null && obj === drillObj ? lod === 1 : lod === 0;
      if (show) { const b = t * 3; idx.push(b, b + 1, b + 2); }
    }
    rec.geom.setIndex(idx);
    rec.geom.computeBoundingSphere();
  }

  // ---- colouring (T10/T11) ----
  _colorForBuilding(objIdx) {
    const a = this.attrs(objIdx);
    if (this.mode === "archetype") {
      // Diverge the two paths: truly-absent id -> reserved no-data grey; any
      // PRESENT id (incl. OpenUBEMUnknown / unmapped) -> archetypeColor, which
      // routes unmapped ids to the distinct Fallback swatch, never no-data grey.
      return a.archetype_id === undefined ? NO_DATA_GREY : archetypeColor(a.archetype_id);
    }
    // EUI (default)
    const v = a.total_eui_kwh_m2;
    if (typeof v !== "number" || Number.isNaN(v)) return NO_DATA_GREY;
    if (this.classified) {
      return classColor(this.rampName, classifyQuantile(v, this.euiBreaks), 5);
    }
    return sampleRamp(this.rampName, normalizeContinuous(v, this.euiMin, this.euiMax));
  }

  recolor() {
    for (const rec of this.meshes) {
      const color = rec.geom.getAttribute("color");
      // Cache per-building colour to avoid recomputing per vertex.
      const cache = new Map();
      for (let v = 0; v < rec.n; v++) {
        const obj = rec.objectid.getX(v);
        const st = rec.surfacetype.getX(v);
        let rgb;
        if (st === SURFTYPE_WINDOW || st === SURFTYPE_DOOR) {
          rgb = GLASS_RGB;
        } else if (this.selected !== null && obj === this.selected) {
          rgb = HIGHLIGHT_RGB;
        } else {
          rgb = cache.get(obj);
          if (!rgb) { rgb = this._colorForBuilding(obj); cache.set(obj, rgb); }
        }
        const c = srgbToLinearColor(rgb);
        color.setXYZ(v, c.r, c.g, c.b);
      }
      color.needsUpdate = true;
    }
  }

  // ---- context placeholders (T04/T11): failed/absent buildings, hatched grey ----
  _buildContext() {
    if (!this.context || !this.context.features || !this.context.features.length) {
      this.contextGroup = null;
      return;
    }
    const center = new THREE.Vector3();
    if (this.boundingBox) this.boundingBox.getCenter(center);
    center.z = 0; // loader recenters x/y only

    const group = new THREE.Group();
    const mat = new THREE.MeshBasicMaterial({
      color: srgbToLinearColor(NO_DATA_GREY), transparent: true, opacity: 0.5,
      side: THREE.DoubleSide, wireframe: false,
    });
    const edgeMat = new THREE.LineBasicMaterial({ color: 0x555555 });
    for (const f of this.context.features) {
      const h = (f.properties && f.properties.height) || 3.5;
      const shape = this._geojsonToShape(f.geometry, center);
      if (!shape) continue;
      const extr = new THREE.ExtrudeGeometry(shape, { depth: h, bevelEnabled: false });
      const m = new THREE.Mesh(extr, mat);
      group.add(m);
      // Hatch affordance: wire overlay so approximations read as "not real geometry".
      group.add(new THREE.LineSegments(new THREE.EdgesGeometry(extr), edgeMat));
    }
    this.scene.add(group);
    this.contextGroup = group;
  }

  _geojsonToShape(geometry, center) {
    if (!geometry) return null;
    let ring;
    if (geometry.type === "Polygon") ring = geometry.coordinates[0];
    else if (geometry.type === "MultiPolygon") ring = geometry.coordinates[0][0];
    else return null;
    if (!ring || ring.length < 3) return null;
    const shape = new THREE.Shape();
    ring.forEach(([x, y], i) => {
      const px = x - center.x, py = y - center.y;
      if (i === 0) shape.moveTo(px, py); else shape.lineTo(px, py);
    });
    return shape;
  }

  // ---- camera framing ----
  _frameNeighbourhood() {
    const box = new THREE.Box3();
    for (const rec of this.meshes) {
      rec.geom.computeBoundingBox();
      box.union(rec.geom.boundingBox);
    }
    if (box.isEmpty()) box.set(new THREE.Vector3(-100, -100, 0), new THREE.Vector3(100, 100, 30));
    const center = new THREE.Vector3(); box.getCenter(center);
    const size = new THREE.Vector3(); box.getSize(size);
    const radius = Math.max(size.x, size.y, size.z) || 100;
    this.controls.target.copy(center);
    this.controls.minDistance = radius * 0.05;
    this.controls.maxDistance = radius * 6;
    this.camera.position.set(center.x + radius * 0.8, center.y - radius * 0.8, center.z + radius * 0.7);
    this.camera.lookAt(center);
    this._homeTarget = center.clone();
    this._sceneRadius = radius;
    this.controls.update();
  }

  // ---- interaction (T09) ----
  _onPointerDown(ev) {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this._pointer.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
    this._pointer.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
    this._downXY = [ev.clientX, ev.clientY];
  }

  _onPointerUp(ev) {
    // Ignore drags (orbit), only treat clean clicks as selection.
    if (this._downXY) {
      const dx = ev.clientX - this._downXY[0], dy = ev.clientY - this._downXY[1];
      if (dx * dx + dy * dy > 25) return;
    }
    this.raycaster.setFromCamera(this._pointer, this.camera);
    const hits = this.raycaster.intersectObjects(this.meshes.map((r) => r.mesh), false);
    if (!hits.length) return;
    const hit = hits[0];
    const rec = this.meshes.find((r) => r.mesh === hit.object);
    const info = rec.mesh.resolveIntersectionInfo(hit);
    this._selectBuilding(info.objectIndex, rec);
  }

  _selectBuilding(objIdx, rec) {
    // Select + drill-down are ONE action (V04 §4): highlight + reveal LOD-B.
    this.selected = objIdx;
    for (const r of this.meshes) this._setLodIndex(r, r === rec ? objIdx : null);
    this.recolor();
    this._showDetail(objIdx);
    // Reframe on the selected building.
    (rec || this.meshes[0]).geom.computeBoundingBox();
  }

  _backToNeighbourhood() {
    this.selected = null;
    for (const r of this.meshes) this._setLodIndex(r, null);
    this.recolor();
    this._hideDetail();
    this.controls.target.copy(this._homeTarget);
    this.controls.update();
  }

  // ---- UI chrome (T08 compass/scale, T10 legend, T12 provenance) ----
  _buildUI() {
    this.renderer.domElement.addEventListener("pointerdown", (e) => this._onPointerDown(e));
    this.renderer.domElement.addEventListener("pointerup", (e) => this._onPointerUp(e));
    window.addEventListener("keydown", (e) => { if (e.key === "Escape") this._backToNeighbourhood(); });

    this._buildControls();
    this._buildLegend();
    this._buildCompassScale();
    this._buildDetailPane();
  }

  _buildControls() {
    const el = document.createElement("div");
    el.className = "ubem-controls";
    el.innerHTML = `
      <div class="ubem-panel-title">OpenUBEM viewer</div>
      <label>Colour by
        <select id="ubem-mode">
          <option value="eui">Annual EUI (kWh/m²)</option>
          <option value="archetype">Archetype (sector)</option>
        </select>
      </label>
      <label>Ramp
        <select id="ubem-ramp">
          <option value="viridis">viridis</option>
          <option value="cividis">cividis (CVD)</option>
        </select>
      </label>
      <label><input type="checkbox" id="ubem-classed" checked> Quantile classes</label>
      <button id="ubem-back">Back to neighbourhood (Esc)</button>
    `;
    this.mount.appendChild(el);
    el.querySelector("#ubem-mode").addEventListener("change", (e) => {
      this.mode = e.target.value; this.recolor(); this._buildLegend();
    });
    el.querySelector("#ubem-ramp").addEventListener("change", (e) => {
      this.rampName = e.target.value; this.recolor(); this._buildLegend();
    });
    el.querySelector("#ubem-classed").addEventListener("change", (e) => {
      this.classified = e.target.checked; this.recolor(); this._buildLegend();
    });
    el.querySelector("#ubem-back").addEventListener("click", () => this._backToNeighbourhood());
  }

  _buildLegendData() {
    // Archetypes present in the scene, grouped by sector (text labels always shown).
    const present = new Set();
    for (const key of this.objectKeys) {
      const a = this.cityjson.CityObjects[key].attributes || {};
      if (a.archetype_id !== undefined) present.add(a.archetype_id);
    }
    this.presentArchetypes = Array.from(present).sort();
  }

  _swatch(rgb) {
    return `<span class="ubem-swatch" style="background:rgb(${rgb[0]},${rgb[1]},${rgb[2]})"></span>`;
  }

  _buildLegend() {
    let el = this.mount.querySelector(".ubem-legend");
    if (!el) { el = document.createElement("div"); el.className = "ubem-legend"; this.mount.appendChild(el); }
    if (this.mode === "archetype") {
      const rows = this.presentArchetypes.map((id) =>
        `<div class="ubem-legrow">${this._swatch(archetypeColor(id))}
          <span class="ubem-leglabel">${id}</span>
          <span class="ubem-legsub">${archetypeSector(id)}</span></div>`).join("");
      el.innerHTML = `<div class="ubem-panel-title">Archetype (by sector)</div>${rows}
        <div class="ubem-legrow">${this._swatch(NO_DATA_GREY)}<span class="ubem-leglabel">no data</span></div>`;
    } else {
      const breaks = this.euiBreaks;
      let body = "";
      if (this.classified) {
        const edges = [this.euiMin, ...breaks, this.euiMax];
        for (let i = 0; i < 5; i++) {
          body += `<div class="ubem-legrow">${this._swatch(classColor(this.rampName, i, 5))}
            <span class="ubem-leglabel">${edges[i].toFixed(0)} – ${edges[i + 1].toFixed(0)}</span></div>`;
        }
      } else {
        const stops = [0, 0.25, 0.5, 0.75, 1].map((t) => this._swatch(sampleRamp(this.rampName, t))).join("");
        body = `<div class="ubem-rampbar">${stops}</div>
          <div class="ubem-legrow"><span class="ubem-leglabel">${this.euiMin.toFixed(0)} → ${this.euiMax.toFixed(0)} kWh/m²</span></div>`;
      }
      el.innerHTML = `<div class="ubem-panel-title">Annual EUI (kWh/m²)</div>${body}
        <div class="ubem-legrow">${this._swatch(NO_DATA_GREY)}<span class="ubem-leglabel">no data</span></div>`;
    }
  }

  _buildCompassScale() {
    const el = document.createElement("div");
    el.className = "ubem-hud";
    el.innerHTML = `
      <svg class="ubem-compass" width="64" height="64" viewBox="-32 -32 64 64">
        <circle r="30" class="ubem-compass-ring"/>
        <g id="ubem-compass-needle">
          <polygon points="0,-24 6,6 0,0 -6,6" class="ubem-compass-n"/>
        </g>
        <text x="0" y="-14" class="ubem-compass-label">N</text>
      </svg>
      <div class="ubem-scalebar"><div class="ubem-scalebar-line"></div><span id="ubem-scale-label">–</span></div>
    `;
    this.mount.appendChild(el);
    this._compassNeedle = el.querySelector("#ubem-compass-needle");
    this._scaleLabel = el.querySelector("#ubem-scale-label");
    this._scaleLine = el.querySelector(".ubem-scalebar-line");
  }

  _updateHud() {
    // Compass: heading = camera azimuth in the XY (Z-up) plane; N is +Y.
    const dir = new THREE.Vector3();
    this.camera.getWorldDirection(dir);
    const heading = Math.atan2(dir.x, dir.y); // radians, 0 = looking toward +Y (N)
    if (this._compassNeedle) {
      this._compassNeedle.setAttribute("transform", `rotate(${(heading * 180 / Math.PI).toFixed(1)})`);
    }
    // Scale bar: metres spanned by a fixed 80px at the target distance.
    if (this._scaleLabel) {
      const dist = this.camera.position.distanceTo(this.controls.target);
      const vFov = (this.camera.fov * Math.PI) / 180;
      const worldPerPixel = (2 * Math.tan(vFov / 2) * dist) / this.mount.clientHeight;
      const rawMetres = worldPerPixel * 80;
      const nice = this._niceNumber(rawMetres);
      const px = Math.round(nice / worldPerPixel);
      this._scaleLine.style.width = `${px}px`;
      this._scaleLabel.textContent = `${nice} m`;
    }
  }

  _niceNumber(x) {
    const pow = Math.pow(10, Math.floor(Math.log10(x)));
    const f = x / pow;
    const nice = f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10;
    return nice * pow;
  }

  // ---- detail pane + provenance (T12) ----
  _buildDetailPane() {
    const el = document.createElement("div");
    el.className = "ubem-detail hidden";
    el.innerHTML = `<div class="ubem-panel-title">Building <span id="ubem-detail-id"></span>
      <button id="ubem-detail-close">×</button></div>
      <div id="ubem-detail-badges"></div>
      <table id="ubem-detail-table"></table>
      <div id="ubem-detail-zgate"></div>`;
    this.mount.appendChild(el);
    this._detailEl = el;
    el.querySelector("#ubem-detail-close").addEventListener("click", () => this._backToNeighbourhood());
  }

  _showDetail(objIdx) {
    const a = this.attrs(objIdx);
    const key = this.objectKeys[objIdx];
    this._detailEl.classList.remove("hidden");
    this._detailEl.querySelector("#ubem-detail-id").textContent = key;

    // Badges: resolution-mode border + merged trust badge, shape/text not hue-only.
    const border = resolutionBorder(a.resolution_mode);
    const trust = trustBadge(a.trust_confidence === undefined ? null : a.trust_confidence);
    const glyphChar = { solid: "●", half: "◐", hollow: "○", not_recorded: "—" }[trust.glyph];
    this._detailEl.querySelector("#ubem-detail-badges").innerHTML = `
      <span class="ubem-badge ubem-border-${border.weight}">resolution: ${border.label}</span>
      <span class="ubem-badge">trust: <b>${glyphChar}</b> ${trust.label}</span>`;

    // Verbatim field table (absent => "not recorded", never blank/fabricated).
    const rows = DETAIL_FIELDS.map((f) =>
      `<tr><td>${f}</td><td>${displayToken(a[f])}</td></tr>`).join("");
    this._detailEl.querySelector("#ubem-detail-table").innerHTML = rows;

    // LOD-Z gate (Rule V04-RMG-01): enable per real zoning_strategy only.
    const gate = lodZGate(a.zoning_strategy);
    const zEl = this._detailEl.querySelector("#ubem-detail-zgate");
    zEl.innerHTML = `
      <div class="ubem-panel-subtitle">Interior detail (LOD-Z)</div>
      <button ${gate.zoneBreakdown ? "" : "disabled"}>Zone breakdown</button>
      <button ${gate.floorLevel ? "" : "disabled"}>Floor-level</button>
      ${gate.disclosure ? `<div class="ubem-disclosure">${gate.disclosure}</div>` : ""}
      ${gate.zoneBreakdown || gate.floorLevel
        ? `<div class="ubem-disclosure">per-zone rendering deferred in MVP — no synthetic zones drawn</div>` : ""}`;
  }

  _hideDetail() {
    if (this._detailEl) this._detailEl.classList.add("hidden");
  }

  // ---- loop ----
  _onResize() {
    const w = this.mount.clientWidth, h = this.mount.clientHeight;
    this.camera.aspect = w / h; this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }

  _animate() {
    const loop = () => {
      requestAnimationFrame(loop);
      this.controls.update();
      this._updateHud();
      this.renderer.render(this.scene, this.camera);
    };
    loop();
  }
}

export function boot() {
  const el = document.getElementById("scene-data");
  if (!el) { console.error("no #scene-data payload"); return; }
  const scene = JSON.parse(el.textContent);
  const mount = document.getElementById("ubem-viewer") || document.body;
  window.__ubemViewer = new Viewer(scene, mount);
  window.__ubemReady = true;
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
}

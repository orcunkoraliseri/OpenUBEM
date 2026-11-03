"""EU-18a T02: write `plans3D/index.html` and `plans3D/PLANS_<district>.html`
from the IDFs that exist today (`D-EU-54`, the owner's "premiere part").

Geometry (zones, rings, storey count, dwelling count, areas,
``geometry_outcome``, ruled/box, has-core) is read out of the emitted IDF via
``scripts/eu_idf_plan_reader.py`` -- never out of the side-car (rule 3).
Descriptive-only fields the IDF itself cannot carry (the scheme name, the
recorded refusal reason, the `FINDING 204` out-of-band tag) are read from the
per-building side-car and always labelled ``sidecar`` in the embedded JSON
and on the page, per rule 3: "a side-car figure may be quoted only as
'side-car says X, IDF says Y'". A building is flagged ``divergent`` whenever
the side-car's own claim (``DWELLING_LAYOUT_EMITTED*`` vs not) disagrees with
what the IDF's zone kinds actually show (`FINDING 213`).

🔴 Content rule (`D-EU-54` §2): no EUI, no demand, no EnergyPlus output, no
run or job id, no weather -- not in the page, not in the JSON blob, not in a
tooltip. Only ``geometry_outcome`` is read from the manifest; none of its
simulation columns are ever touched here.

Self-contained (dependency decision §4.5): one inline ``<style>``, one inline
``<script>``, one embedded JSON blob per district page, no CDN, no external
script, no network fetch, no image file -- the folder must open from disk
with no internet. Ring coordinates are rounded to 1 cm
(``round_ring_1cm``) only in this JSON blob, never in the canonical reader
output (dependency decision §4.4).
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path

from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from scripts.eu_idf_plan_reader import BuildingPlan, district_paths, read_district, round_ring_1cm
from scripts.run_eu_s2_district_campaign import DISTRICTS

ROOT = Path(__file__).resolve().parents[1]
PLANS_DIR = ROOT / "docs/docs_ACTIVE/europeanLocations/plans3D"

FORBIDDEN_TERMS = ("eui", "kwh", "energyplus", "heating", "cooling", "epw", "job")


def _load_sidecar(root: Path, building_id: str) -> dict | None:
    path = root / "layouts" / f"{building_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _zone_polygon(zone) -> Polygon | None:
    polys = [Polygon(ring).buffer(0) for ring in zone.rings if len(ring) >= 3]
    polys = [p for p in polys if not p.is_empty]
    if not polys:
        return None
    return unary_union(polys)


def _facade_contact_min_by_storey(plan: BuildingPlan) -> dict[int, float | None]:
    """Minimum exterior-facade contact per storey, measured on the IDF's own
    zone rings: the length of a dwelling zone's own boundary that lies on
    the storey's overall exterior boundary (not shared with a neighbouring
    zone). ``None`` where fewer than 2 dwelling zones exist on that storey
    (facade contact is not a meaningful acceptance quantity there)."""
    by_storey: dict[int, list] = {}
    for zone in plan.zones:
        by_storey.setdefault(zone.storey, []).append(zone)

    result: dict[int, float | None] = {}
    for storey, zones in by_storey.items():
        dwelling_zones = [z for z in zones if z.kind == "dwelling"]
        if len(dwelling_zones) < 2:
            result[storey] = None
            continue
        zone_polys = {}
        for z in zones:
            poly = _zone_polygon(z)
            if poly is not None:
                zone_polys[z.name] = poly
        storey_union = unary_union(list(zone_polys.values()))
        geoms = list(storey_union.geoms) if hasattr(storey_union, "geoms") else [storey_union]
        exterior_lines = [LineString(g.exterior.coords) for g in geoms if g.geom_type == "Polygon"]
        exterior_boundary = unary_union(exterior_lines) if exterior_lines else None
        mins = []
        for z in dwelling_zones:
            poly = zone_polys.get(z.name)
            if poly is None or exterior_boundary is None:
                continue
            contact = poly.boundary.intersection(exterior_boundary.buffer(1e-6))
            mins.append(contact.length)
        result[storey] = min(mins) if mins else None
    return result


def _building_record(plan: BuildingPlan, root: Path) -> dict:
    sidecar = _load_sidecar(root, plan.building_id)
    sidecar_ruled = bool(sidecar and str(sidecar.get("geometry_outcome", "")).startswith("DWELLING_LAYOUT_EMITTED"))
    idf_ruled = plan.is_ruled()
    facade_by_storey = _facade_contact_min_by_storey(plan)

    storeys_payload = []
    zones_by_storey: dict[int, list] = {}
    for zone in plan.zones:
        zones_by_storey.setdefault(zone.storey, []).append(zone)
    for storey in sorted(zones_by_storey):
        zones_payload = []
        for zone in zones_by_storey[storey]:
            zones_payload.append({
                "name": zone.name,
                "kind": zone.kind,
                "rings": [round_ring_1cm(ring) for ring in zone.rings],
                "area_m2": round(zone.area_m2, 3),
            })
        storeys_payload.append({
            "storey": storey,
            "zones": zones_payload,
            "facade_contact_min_m": (
                round(facade_by_storey[storey], 2) if facade_by_storey.get(storey) is not None else None
            ),
        })

    circulation_pct = (
        round(100.0 * plan.circulation_area_m2 / plan.gross_area_m2, 2) if plan.gross_area_m2 > 0 else None
    )

    return {
        "building_id": plan.building_id,
        "stem": plan.stem,
        "storey_count": plan.storey_count,
        "dwelling_count": plan.dwelling_count,
        "geometry_outcome": plan.geometry_outcome,
        "is_ruled": idf_ruled,
        "has_core": plan.has_unconditioned_core(),
        "gross_area_m2": round(plan.gross_area_m2, 3),
        "conditioned_area_m2": round(plan.conditioned_area_m2, 3),
        "circulation_area_m2": round(plan.circulation_area_m2, 3),
        "circulation_pct": circulation_pct,
        "divergent": idf_ruled != sidecar_ruled,
        "sidecar": {
            "scheme": sidecar.get("scheme") if sidecar else None,
            "fallback_reason": sidecar.get("fallback_reason") if sidecar else None,
            "circulation_outside_ruled_absolute_band": (
                sidecar.get("circulation_outside_ruled_absolute_band") if sidecar else None
            ),
            "geometry_outcome": sidecar.get("geometry_outcome") if sidecar else None,
        } if sidecar else None,
        "storeys": storeys_payload,
    }


def _district_build_date(root: Path) -> str:
    idf_dir = root / "idfs"
    mtimes = [p.stat().st_mtime for p in idf_dir.glob("*.idf")]
    if not mtimes:
        return "unknown"
    return dt.datetime.fromtimestamp(min(mtimes)).strftime("%Y-%m-%d")


CSS = """
:root { --bg:#0e1116; --panel:#161b22; --line:#2a3038; --text:#e6edf3; --muted:#8b949e;
  --dwelling:#3f7cf5; --circulation:#e0a72d; --whole:#5c6773; --accent:#e05252; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--text); font-family: system-ui, sans-serif; }
header { padding:12px 16px; border-bottom:1px solid var(--line); }
header h1 { margin:0 0 4px 0; font-size:18px; }
header .meta { color:var(--muted); font-size:12px; }
.layout { display:flex; height:calc(100vh - 64px); }
.sidebar { width:340px; border-right:1px solid var(--line); display:flex; flex-direction:column; }
.controls { padding:10px; border-bottom:1px solid var(--line); display:flex; flex-direction:column; gap:6px; }
.controls input, .controls select { background:var(--panel); color:var(--text); border:1px solid var(--line);
  padding:5px; border-radius:4px; font-size:12px; }
.list { overflow-y:auto; flex:1; }
.item { display:flex; gap:8px; padding:6px 10px; border-bottom:1px solid var(--line); cursor:pointer; align-items:center; }
.item:hover, .item.selected { background:var(--panel); }
.item svg { width:48px; height:48px; flex-shrink:0; background:#0a0d12; border-radius:3px; }
.item .label { font-size:11px; line-height:1.3; overflow:hidden; }
.item .label .id { color:var(--text); }
.item .label .sub { color:var(--muted); }
.detail { flex:1; overflow-y:auto; padding:16px; }
.badge { display:inline-block; padding:1px 6px; border-radius:3px; font-size:11px; margin-right:6px; }
.badge.ruled { background:#123; color:#7fb0ff; }
.badge.box { background:#332; color:#cbb; }
.badge.core { background:#332a10; color:#e0a72d; }
.badge.divergent { background:#3a1414; color:#ff8a8a; }
.badge.out-of-band { background:#3a1414; color:#ff8a8a; }
.metrics { display:grid; grid-template-columns: repeat(auto-fill, minmax(160px,1fr)); gap:8px; margin:12px 0; }
.metrics .m { background:var(--panel); border:1px solid var(--line); border-radius:4px; padding:8px; }
.metrics .m .k { color:var(--muted); font-size:11px; }
.metrics .m .v { font-size:14px; }
.storey { border:1px solid var(--line); border-radius:4px; margin-bottom:12px; padding:8px; }
.storey h3 { margin:0 0 6px 0; font-size:13px; color:var(--muted); }
.storey svg { width:100%; height:320px; background:#0a0d12; border-radius:3px; }
.note { color:var(--muted); font-size:12px; margin:8px 0; }
.refused { color:var(--accent); font-weight:600; }
.empty { color:var(--muted); padding:24px; }
"""


def _page_html(district: str, source_tree: str, build_date: str, records: list[dict], totals: dict) -> str:
    payload = {
        "district": district,
        "source_tree": source_tree,
        "build_date": build_date,
        "totals": totals,
        "buildings": records,
    }
    payload_json = json.dumps(payload, separators=(",", ":"))
    title = html.escape(f"Plans — {district}")
    return f"""<!doctype html>
<html><head><meta charset="utf-8"/><title>{title}</title>
<style>{CSS}</style></head>
<body>
<header>
  <h1>{html.escape(district)}</h1>
  <div class="meta">Source: <code>{html.escape(source_tree)}</code> · built {html.escape(build_date)} ·
    {totals['total']} buildings · {totals['ruled']} ruled ({totals['ruled_pct']}%) · {totals['cored']} with a core</div>
</header>
<div class="layout">
  <div class="sidebar">
    <div class="controls">
      <input id="search" placeholder="search building_id / stem" />
      <select id="f-ruled"><option value="">ruled / massing box — all</option>
        <option value="ruled">ruled</option><option value="box">massing box</option></select>
      <select id="f-core"><option value="">has core — all</option>
        <option value="yes">has core</option><option value="no">no core</option></select>
      <select id="f-storeys"><option value="">storey count — all</option></select>
      <select id="f-scheme"><option value="">scheme (side-car) — all</option></select>
      <select id="f-reason"><option value="">refusal reason — all</option></select>
    </div>
    <div class="list" id="list"></div>
  </div>
  <div class="detail" id="detail"><div class="empty">Select a building.</div></div>
</div>
<script>
const DATA = {payload_json};
const listEl = document.getElementById('list');
const detailEl = document.getElementById('detail');
let selected = null;

function fmtNum(x, d) {{ return (x === null || x === undefined) ? '—' : Number(x).toFixed(d === undefined ? 1 : d); }}

function bbox(rings) {{
  let minx=Infinity, miny=Infinity, maxx=-Infinity, maxy=-Infinity;
  for (const ring of rings) for (const [x,y] of ring) {{
    if (x<minx) minx=x; if (x>maxx) maxx=x; if (y<miny) miny=y; if (y>maxy) maxy=y;
  }}
  if (minx===Infinity) return [0,0,1,1];
  return [minx, miny, maxx, maxy];
}}

function niceScale(widthM) {{
  const target = widthM / 4;
  const steps = [1,2,5,10,20,50,100,200,500];
  let best = steps[0];
  for (const s of steps) if (s <= target) best = s;
  return best;
}}

function zoneFill(kind) {{
  if (kind === 'dwelling') return 'var(--dwelling)';
  if (kind === 'circulation') return 'url(#hatch)';
  return 'var(--whole)';
}}

function renderStoreySvg(storey, opts) {{
  const allRings = [];
  for (const z of storey.zones) for (const r of z.rings) allRings.push(r);
  const [minx,miny,maxx,maxy] = bbox(allRings);
  const w = Math.max(maxx-minx, 1), h = Math.max(maxy-miny, 1);
  const pad = Math.max(w,h) * 0.12;
  const vb = `${{minx-pad}} ${{-(maxy+pad)}} ${{w+2*pad}} ${{h+2*pad}}`;
  let polys = '';
  for (const z of storey.zones) {{
    for (const ring of z.rings) {{
      const pts = ring.map(([x,y]) => `${{x}},${{-y}}`).join(' ');
      const cls = z.kind === 'circulation' ? 'zone-circulation' : (z.kind === 'dwelling' ? 'zone-dwelling' : 'zone-whole');
      polys += `<polygon points="${{pts}}" class="${{cls}}" fill="${{zoneFill(z.kind)}}" stroke="#0a0d12" stroke-width="${{Math.max(w,h)*0.004}}"/>`;
    }}
  }}
  let scaleGroup = '';
  if (opts !== false) {{
    const s = niceScale(w);
    const x0 = minx, y0 = maxy + pad*0.6;
    scaleGroup = `<g stroke="#e6edf3" stroke-width="${{Math.max(w,h)*0.003}}">
      <line x1="${{x0}}" y1="${{-y0}}" x2="${{x0+s}}" y2="${{-y0}}"/>
      <line x1="${{x0}}" y1="${{-y0-h*0.01}}" x2="${{x0}}" y2="${{-y0+h*0.01}}"/>
      <line x1="${{x0+s}}" y1="${{-y0-h*0.01}}" x2="${{x0+s}}" y2="${{-y0+h*0.01}}"/>
      <text x="${{x0}}" y="${{-y0+h*0.05}}" fill="#8b949e" font-size="${{Math.max(w,h)*0.035}}">${{s}} m</text>
    </g>
    <g transform="translate(${{maxx+pad*0.3}},${{-(maxy+pad*0.3)}})" fill="#e6edf3" font-size="${{Math.max(w,h)*0.04}}">
      <line x1="0" y1="0" x2="0" y2="${{-Math.max(w,h)*0.08}}" stroke="#e6edf3" stroke-width="${{Math.max(w,h)*0.004}}"/>
      <polygon points="0,${{-Math.max(w,h)*0.1}} ${{-Math.max(w,h)*0.02}},${{-Math.max(w,h)*0.08}} ${{Math.max(w,h)*0.02}},${{-Math.max(w,h)*0.08}}"/>
      <text x="${{Math.max(w,h)*0.03}}" y="${{-Math.max(w,h)*0.08}}">N</text>
    </g>`;
  }}
  return `<svg viewBox="${{vb}}">
    <defs><pattern id="hatch" width="2" height="2" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="0" y2="2" stroke="var(--circulation)" stroke-width="1"/></pattern></defs>
    ${{polys}}${{scaleGroup}}
  </svg>`;
}}

function buildThumb(b) {{
  const storey0 = b.storeys.find(s => s.storey === 0);
  if (!storey0) return '<svg></svg>';
  return renderStoreySvg(storey0, false);
}}

function populateSelect(id, values) {{
  const el = document.getElementById(id);
  const seen = new Set();
  for (const v of values) {{
    if (v === null || v === undefined || seen.has(v)) continue;
    seen.add(v);
    const opt = document.createElement('option');
    opt.value = v; opt.textContent = v;
    el.appendChild(opt);
  }}
}}

populateSelect('f-storeys', [...new Set(DATA.buildings.map(b => b.storey_count))].sort((a,b)=>a-b));
populateSelect('f-scheme', [...new Set(DATA.buildings.map(b => b.sidecar && b.sidecar.scheme))].filter(Boolean).sort());
populateSelect('f-reason', [...new Set(DATA.buildings.map(b => b.sidecar && b.sidecar.fallback_reason))].filter(Boolean).sort());

function matches(b) {{
  const q = document.getElementById('search').value.trim().toLowerCase();
  if (q && !b.building_id.toLowerCase().includes(q) && !b.stem.toLowerCase().includes(q)) return false;
  const fr = document.getElementById('f-ruled').value;
  if (fr === 'ruled' && !b.is_ruled) return false;
  if (fr === 'box' && b.is_ruled) return false;
  const fc = document.getElementById('f-core').value;
  if (fc === 'yes' && !b.has_core) return false;
  if (fc === 'no' && b.has_core) return false;
  const fs = document.getElementById('f-storeys').value;
  if (fs && String(b.storey_count) !== fs) return false;
  const fsch = document.getElementById('f-scheme').value;
  if (fsch && (!b.sidecar || b.sidecar.scheme !== fsch)) return false;
  const frr = document.getElementById('f-reason').value;
  if (frr && (!b.sidecar || b.sidecar.fallback_reason !== frr)) return false;
  return true;
}}

function renderList() {{
  listEl.innerHTML = '';
  for (const b of DATA.buildings) {{
    if (!matches(b)) continue;
    const row = document.createElement('div');
    row.className = 'item' + (selected === b ? ' selected' : '');
    row.innerHTML = buildThumb(b) + `<div class="label"><div class="id">${{b.building_id}}</div>
      <div class="sub">${{b.storey_count}} storeys · ${{b.dwelling_count}} dwellings · ${{b.is_ruled ? 'ruled' : 'box'}}</div></div>`;
    row.addEventListener('click', () => {{ selected = b; renderDetail(b); renderList(); }});
    listEl.appendChild(row);
  }}
}}

function renderDetail(b) {{
  let badges = `<span class="badge ${{b.is_ruled ? 'ruled' : 'box'}}">${{b.is_ruled ? 'ruled' : 'massing box'}}</span>`;
  if (b.has_core) badges += `<span class="badge core">core / corridor</span>`;
  if (b.divergent) badges += `<span class="badge divergent">side-car / IDF divergent</span>`;
  if (b.sidecar && b.sidecar.circulation_outside_ruled_absolute_band) badges += `<span class="badge out-of-band">circulation outside 12.0-25.0 m² (side-car)</span>`;

  let refusedNote = '';
  if (!b.is_ruled) {{
    const reason = (b.sidecar && b.sidecar.fallback_reason) ? b.sidecar.fallback_reason : b.geometry_outcome;
    refusedNote = `<p class="refused">Refused: ${{reason}}. simulated as one undivided zone per floor</p>`;
  }}

  let divergentNote = '';
  if (b.divergent) {{
    const sc = b.sidecar ? (b.sidecar.geometry_outcome || '(no side-car)') : '(no side-car)';
    divergentNote = `<p class="note">side-car says ${{sc}}, IDF says ${{b.geometry_outcome}}</p>`;
  }}

  const schemeLine = b.sidecar ? `<div class="m"><div class="k">scheme (side-car)</div><div class="v">${{b.sidecar.scheme || '—'}}</div></div>` : '';

  const storeysHtml = b.storeys.map(s => `<div class="storey">
      <h3>storey ${{s.storey}}${{s.facade_contact_min_m !== null ? ' · min facade contact ' + fmtNum(s.facade_contact_min_m, 2) + ' m' : ''}}</h3>
      ${{renderStoreySvg(s)}}
    </div>`).join('');

  detailEl.innerHTML = `
    <h2>${{b.building_id}} <span class="note">(${{b.stem}})</span></h2>
    <div>${{badges}}</div>
    ${{refusedNote}}${{divergentNote}}
    <div class="metrics">
      <div class="m"><div class="k">geometry_outcome</div><div class="v">${{b.geometry_outcome}}</div></div>
      <div class="m"><div class="k">storeys</div><div class="v">${{b.storey_count}}</div></div>
      <div class="m"><div class="k">dwellings</div><div class="v">${{b.dwelling_count}}</div></div>
      ${{schemeLine}}
      <div class="m"><div class="k">gross area</div><div class="v">${{fmtNum(b.gross_area_m2)}} m²</div></div>
      <div class="m"><div class="k">conditioned area</div><div class="v">${{fmtNum(b.conditioned_area_m2)}} m²</div></div>
      <div class="m"><div class="k">circulation share</div><div class="v">${{b.circulation_pct !== null ? b.circulation_pct + '%' : '—'}}</div></div>
    </div>
    ${{storeysHtml}}
  `;
}}

document.getElementById('search').addEventListener('input', renderList);
for (const id of ['f-ruled','f-core','f-storeys','f-scheme','f-reason']) document.getElementById(id).addEventListener('change', renderList);
renderList();
</script>
</body></html>
"""


def _index_html(district_summaries: list[dict]) -> str:
    rows = "".join(
        f"<tr><td><a href='PLANS_{html.escape(d['district'])}.html'>{html.escape(d['district'])}</a></td>"
        f"<td>{d['totals']['total']}</td><td>{d['totals']['ruled']}</td>"
        f"<td>{d['totals']['ruled_pct']}%</td><td>{d['totals']['cored']}</td></tr>"
        for d in district_summaries
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"/><title>European locations — plans</title>
<style>{CSS}
table {{ border-collapse: collapse; margin: 16px; }}
td, th {{ border: 1px solid var(--line); padding: 6px 12px; text-align: left; }}
a {{ color: var(--dwelling); }}
</style></head>
<body>
<header><h1>European locations — floor-plan atlas</h1>
<div class="meta">Geometry read from the emitted IDFs. No simulated output, no run id, no weather is shown anywhere in this atlas.</div></header>
<table>
<tr><th>district</th><th>buildings</th><th>ruled</th><th>ruled %</th><th>with a core</th></tr>
{rows}
</table>
</body></html>
"""


def emit_plan_pages(districts: list[str] | None = None, evidence_roots: dict[str, Path] | None = None) -> None:
    targets = districts if districts is not None else sorted(DISTRICTS)
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []
    for district in targets:
        root = (evidence_roots or {}).get(district, district_paths(district))
        plans = read_district(district, root)
        records = [_building_record(plan, root) for plan in plans]
        total = len(records)
        ruled = sum(1 for r in records if r["is_ruled"])
        cored = sum(1 for r in records if r["has_core"])
        totals = {
            "total": total,
            "ruled": ruled,
            "ruled_pct": round(100.0 * ruled / total, 2) if total else 0.0,
            "cored": cored,
        }
        build_date = _district_build_date(root)
        page = _page_html(district, str(root.relative_to(ROOT)), build_date, records, totals)
        out_path = PLANS_DIR / f"PLANS_{district}.html"
        out_path.write_text(page, encoding="utf-8")
        size_mb = out_path.stat().st_size / (1024 * 1024)
        print(f"{district}: {out_path} ({size_mb:.2f} MB), {total} buildings, {ruled} ruled ({totals['ruled_pct']}%), {cored} cored")
        summaries.append({"district": district, "totals": totals})

    (PLANS_DIR / "index.html").write_text(_index_html(summaries), encoding="utf-8")
    print(f"index.html written: {PLANS_DIR / 'index.html'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EU-18a T02 / EU-18b T12: emit the plans3D pages.")
    parser.add_argument("--district", action="append", choices=sorted(DISTRICTS), default=None)
    parser.add_argument(
        "--evidence-root",
        action="append",
        default=None,
        help="DISTRICT=path override (T12: point at the EU-17 rebuild tree).",
    )
    args = parser.parse_args()

    roots = {}
    for entry in args.evidence_root or []:
        district, _, path = entry.partition("=")
        roots[district] = Path(path)

    emit_plan_pages(args.district, roots or None)

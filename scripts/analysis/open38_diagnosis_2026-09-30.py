import csv, math, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TMP = Path.home() / "AppData/Local/Temp/ubem_validation/open38_rerun_2026-09-29"
DIAG = TMP / "diag"
SRC = ROOT / "openubem/outputs/comparisons/open38_rerun_2026-09-29.csv"
OUT = ROOT / "openubem/outputs/comparisons/open38_diagnosis_2026-09-30.csv"

HVAC_TYPES = {"ZONEHVAC:EQUIPMENTCONNECTIONS"}


def parse_idf(path):
    objs, cur = [], []
    for line in path.read_text(errors="replace").splitlines():
        code = line.split("!")[0]
        if not code.strip():
            continue
        cur.append(code)
        if ";" in code:
            txt = " ".join(cur)
            cur = []
            parts = [p.strip() for p in txt.rsplit(";", 1)[0].split(",")]
            objs.append((parts[0].upper(), parts[1:]))
    return objs


def newell_area(vs):
    sx = sy = sz = 0.0
    n = len(vs)
    for i in range(n):
        x1, y1, z1 = vs[i]
        x2, y2, z2 = vs[(i + 1) % n]
        sx += (y1 - y2) * (z1 + z2)
        sy += (z1 - z2) * (x1 + x2)
        sz += (x1 - x2) * (y1 + y2)
    return 0.5 * math.sqrt(sx * sx + sy * sy + sz * sz)


def num(s):
    try:
        return float(s)
    except ValueError:
        return 0.0


def first_severe(err):
    lines = err.read_text(errors="replace").splitlines() if err.exists() else []
    for i, l in enumerate(lines):
        if re.search(r"\*\* +Severe +\*\*", l):
            msg = [l.split("**")[-1].strip()]
            for k in lines[i + 1:i + 6]:
                if "~~~" in k:
                    msg.append(k.split("**")[-1].strip())
            return " | ".join(msg), lines
    return "", lines


def eio_zones(eio):
    hdr, zones = None, {}
    if not eio.exists():
        return zones
    for l in eio.read_text(errors="replace").splitlines():
        if l.startswith("! <Zone Information>"):
            hdr = [h.strip() for h in l.split(",")]
        elif l.startswith(" Zone Information,") and hdr:
            f = [x.strip() for x in l.split(",")]
            d = dict(zip(hdr, f))
            zones[f[1].upper()] = dict(
                vol=num(d.get("Volume {m3}", "0")),
                floor=num(d.get("Floor Area {m2}", "0")),
                bb=[num(d.get(k, "0")) for k in (
                    "Minimum X {m}", "Maximum X {m}", "Minimum Y {m}",
                    "Maximum Y {m}", "Minimum Z {m}", "Maximum Z {m}")],
            )
    return zones


def analyse(idf, zone, surf, eio_z):
    objs = parse_idf(idf)
    surfaces, hvac, gains, shades = {}, set(), Counter(), []
    zfloor = eio_z.get(zone.upper(), {}).get("floor", 0.0)
    uz = zone.upper()
    for typ, f in objs:
        if typ == "BUILDINGSURFACE:DETAILED":
            si = next(i for i, x in enumerate(f) if x.lower() in ("sunexposed", "nosun"))
            co = f[si + 4:]
            vs = [tuple(num(x) for x in co[3 * k:3 * k + 3]) for k in range(len(co) // 3)]
            surfaces[f[0].upper()] = dict(type=f[1], cons=f[2], zone=f[3].upper(),
                                          bc=f[si - 2], bco=f[si - 1].upper(), area=newell_area(vs))
        elif typ == "ZONEHVAC:EQUIPMENTCONNECTIONS" or typ.startswith("HVACTEMPLATE:ZONE:"):
            hvac.add(f[0].upper())
        elif typ in ("LIGHTS", "ELECTRICEQUIPMENT", "GASEQUIPMENT", "OTHEREQUIPMENT"):
            if f[1].upper() == uz:
                method = f[3].lower()
                if method in ("equipmentlevel", "lightinglevel"):
                    gains[typ] += num(f[4])
                elif "area" in method:
                    gains[typ] += num(f[5]) * zfloor
        elif typ.startswith("SHADING:") and typ.endswith(":DETAILED"):
            shades.append([num(x) for x in f[3:]])
    s = surfaces.get(surf.upper())
    tot = sum(gains.values())
    r = dict(zone_hvac=int(uz in hvac), gain_w=round(tot, 1),
             gain_w_m2=round(tot / zfloor, 2) if zfloor else "",
             gas_w=round(gains["GASEQUIPMENT"], 1))
    if s:
        r.update(surf_type=s["type"], surf_area_m2=round(s["area"], 3),
                 surf_cons=s["cons"], surf_bc=s["bc"])
        if s["bco"]:
            p = surfaces.get(s["bco"])
            if p:
                r["adj_partner_zone"] = p["zone"]
                r["adj_area_ratio"] = round(p["area"] / s["area"], 3) if s["area"] else ""
                r["adj_mismatch"] = int(abs(p["area"] - s["area"]) > 0.01 * max(s["area"], 1e-9)
                                        or p["bco"] != surf.upper() or p["zone"] == s["zone"])
            else:
                r["adj_partner_zone"] = "MISSING"
                r["adj_mismatch"] = 1
        else:
            r["adj_mismatch"] = 0
    z = eio_z.get(uz)
    if z and shades:
        bb, dmin = z["bb"], 1e9
        for c in shades:
            for i in range(0, len(c) - 2, 3):
                x, y, zz = c[i:i + 3]
                d = math.sqrt(max(bb[0] - x, 0, x - bb[1]) ** 2 + max(bb[2] - y, 0, y - bb[3]) ** 2
                              + max(bb[4] - zz, 0, zz - bb[5]) ** 2)
                dmin = min(dmin, d)
        r["shade_min_dist_m"] = round(dmin, 2)
    return r


def build():
    out = []
    for r in csv.DictReader(open(SRC, newline="")):
        stem = r["osm_id"].replace("/", "_")
        d = DIAG / f"{r['mode']}__{r['cell']}__{stem}"
        sev, lines = first_severe(d / "eplusout.err")
        fatal = any(re.search(r"[*][*] +Fatal +[*][*]", l) for l in lines)
        zm = re.search(r'zone="([^"]+)"', sev)
        sm = re.search(r'surface="([^"]+)"', sev)
        zone, surf = (zm.group(1) if zm else ""), (sm.group(1) if sm else "")
        tm = re.search(r"temperature of (-?[\d.]+) C|\[(-?[\d.]+)\]|\(([\d.]+)\]", sev)
        eio_z = eio_zones(d / "eplusout.eio")
        z = eio_z.get(zone.upper(), {})
        rec = dict(case=d.name, cell=r["cell"], mode=r["mode"], osm_id=r["osm_id"],
                   new_status=r["new_status"], fatal=int(fatal), zone=zone, surface=surf,
                   temp_c=next((g for g in (tm.groups() if tm else []) if g), ""),
                   zone_vol_m3=z.get("vol", ""), zone_floor_m2=z.get("floor", ""),
                   first_severe=sev[:200])
        if zone:
            rec.update(analyse(TMP / r["cell"] / r["mode"] / "idfs" / f"{stem}.idf", zone, surf, eio_z))
        out.append(rec)
    return out


def classify(rec):
    if rec["new_status"] == "oom_killed":
        return "E_out_of_memory"
    if "non-convex" in rec["first_severe"]:
        return "D_nonconvex_shading" if rec["fatal"] else "D_nonconvex_shading_survived"
    if not rec["fatal"]:
        return "Z_completed"
    if rec["zone"] == "LAUNDRYROOMFLR1":
        return "A_laundry_gas_dryer_unconditioned"
    if not rec.get("zone_hvac") and num(rec.get("gain_w_m2") or 0) > 100:
        return "A_laundry_gas_dryer_unconditioned" if rec["zone"] == "LAUNDRYROOMFLR1" else "A2_unconditioned_high_gain"
    if num(rec.get("gain_w_m2") or 0) > 1000:
        return "B_conditioned_core_zone_with_huge_gas_load"
    if num(rec.get("zone_floor_m2") or 0) < 2:
        return "C1_sliver_perimeter_zone_under_2m2"
    return "C2_ordinary_gains_diverges_in_sizing_no_column_explains"


if __name__ == "__main__":
    recs = build()
    for r in recs:
        r["cause_class"] = classify(r)
    keys = []
    for r in recs:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(recs)
    print(len(recs), "rows")
    for k, v in sorted(Counter(r["cause_class"] for r in recs).items()):
        print(k, v)

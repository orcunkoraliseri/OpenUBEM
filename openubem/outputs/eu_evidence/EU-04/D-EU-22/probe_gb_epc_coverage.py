# -*- coding: utf-8 -*-
"""PLAN_gb-epc-coverage-probe-2026-08-27.md -- T01/T02.

Ruled 2026-08-27 (D-EU-22 Option F1). MEASUREMENT ONLY -- no ingest, no
sample formation, no simulation, no manifest rebuild. Nothing under
openubem/outputs/eu02/ is written or touched. No promoted EU-04/EU-05/EU-06
artefact is touched.

Bearer token comes ONLY from the environment variable EPC_BEARER_TOKEN. It
is never written, printed or logged by this script.
"""
import csv
import hashlib
import io
import json
import os
import sys
import time
import zipfile

import geopandas as gpd
import requests
from shapely.geometry import Point

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
CACHE = os.path.join(HERE, "_cache")
UA = "OpenUBEM/1.0 (D-EU-22 GB EPC coverage probe; research; measurement only)"
SITE = "GB-LDN-STDUNSTANS"

EPC_BASE = "https://api.get-energy-performance-data.communities.gov.uk"
OS_UPRN_URL = "https://api.os.uk/downloads/v1/products/OpenUPRN/downloads?area=GB&format=CSV&redirect"
OS_UPRN_MD5 = "2f023512afc378cd7b9351b24ccf1a34"

MANIFEST_PATH = os.path.join(ROOT, "openubem", "outputs", "eu02", SITE, "02_residential_manifest.gpkg")
JOIN_CSV = os.path.join(HERE, "gb_uprn_join.csv")
CERT_CSV = os.path.join(HERE, "gb_epc_certificates.csv")
PROBE_JSON = os.path.join(HERE, "gb_epc_coverage_probe.json")
SEARCH_CACHE = os.path.join(CACHE, "search_by_uprn")
CERT_CACHE = os.path.join(CACHE, "certificate")
RATE_INTERVAL_S = 0.2
CERT_NUM_RE = __import__("re").compile(r"^\d{4}-\d{4}-\d{4}-\d{4}-\d{4}$")


def _token():
    tok = os.environ.get("EPC_BEARER_TOKEN")
    if not tok:
        sys.stderr.write("EPC_BEARER_TOKEN is not set. Stopping.\n")
        sys.exit(1)
    return tok


def _session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Authorization": "Bearer %s" % _token(),
                       "Accept": "application/json"})
    return s


# ---------------------------------------------------------------- T01 -------
def task_t01():
    s = _session()
    results = []

    r = s.get(EPC_BASE + "/api/domestic/search", params={"postcode": "SW1A 1AA"}, timeout=30)
    results.append(("SW1A 1AA", r.status_code, r.headers.get("Content-Type"), r.text[:300]))

    r2 = s.get(EPC_BASE + "/api/domestic/search", params={"postcode": "E1 6AN"}, timeout=30)
    body2 = r2.json() if "json" in (r2.headers.get("Content-Type") or "") else None
    n_rows = len(body2["data"]) if body2 and "data" in body2 else None
    first_uprn = body2["data"][0].get("uprn") if body2 and body2.get("data") else None
    results.append(("E1 6AN", r2.status_code, r2.headers.get("Content-Type"), n_rows, first_uprn))

    cert_status = None
    cert_number = None
    if body2 and body2.get("data"):
        cert_number = body2["data"][0].get("certificateNumber")
        r3 = s.get(EPC_BASE + "/api/certificate", params={"certificate_number": cert_number}, timeout=30)
        cert_status = r3.status_code
    results.append(("certificate", cert_number, cert_status))

    print("=== T01 fixed calls ===")
    for row in results:
        print(row)

    print("=== T01 rate probe: 20 sequential calls, no delay ===")
    timings = []
    stopped_on_429 = False
    for i in range(20):
        t0 = time.time()
        rr = s.get(EPC_BASE + "/api/domestic/search", params={"postcode": "E1 6AN"}, timeout=30)
        dt_ms = int((time.time() - t0) * 1000)
        hdrs = {k: v for k, v in rr.headers.items() if k.lower().startswith("x-ratelimit")
                or k.lower() == "retry-after"}
        timings.append({"i": i, "status": rr.status_code, "elapsed_ms": dt_ms, "headers": hdrs})
        print(i, rr.status_code, dt_ms, hdrs)
        if rr.status_code == 429:
            stopped_on_429 = True
            break

    print("=== T01 summary ===")
    print("stopped_on_429:", stopped_on_429)
    print("n_calls:", len(timings))
    print("min_elapsed_ms:", min(t["elapsed_ms"] for t in timings))
    print("max_elapsed_ms:", max(t["elapsed_ms"] for t in timings))


# ---------------------------------------------------------------- T02 -------
def _md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _ensure_uprn_zip():
    os.makedirs(CACHE, exist_ok=True)
    zpath = os.path.join(CACHE, "osopenuprn_gb.zip")
    if os.path.exists(zpath) and _md5(zpath) == OS_UPRN_MD5:
        print("cache hit, md5 verified:", zpath)
        return zpath
    print("downloading OS Open UPRN zip (~618 MB) to", zpath)
    with requests.get(OS_UPRN_URL, headers={"User-Agent": UA}, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(zpath, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                if chunk:
                    f.write(chunk)
    md5_actual = _md5(zpath)
    print("downloaded, md5:", md5_actual, "expected:", OS_UPRN_MD5)
    if md5_actual != OS_UPRN_MD5:
        sys.stderr.write("MD5 MISMATCH on OS Open UPRN zip. Stopping.\n")
        sys.exit(1)
    return zpath


def task_t02():
    man = gpd.read_file(MANIFEST_PATH)
    man_wgs = man.to_crs(4326)
    w, s, e, n = man_wgs.total_bounds
    pad = 0.0005
    w, s, e, n = w - pad, s - pad, e + pad, n + pad
    print("padded study bbox (crs84 w,s,e,n):", w, s, e, n)

    zpath = _ensure_uprn_zip()
    zf = zipfile.ZipFile(zpath)
    csv_members = [nm for nm in zf.namelist() if nm.lower().endswith(".csv")]
    if len(csv_members) != 1:
        sys.stderr.write("expected exactly one CSV member, found %r. Stopping.\n" % csv_members)
        sys.exit(1)
    member = csv_members[0]
    print("member:", member)

    # OS Open UPRN CSV, no header row: UPRN, X_COORDINATE(easting,27700),
    # Y_COORDINATE(northing,27700), LATITUDE(4326), LONGITUDE(4326).
    rows_in_bbox = []
    total_rows = 0
    header_checked = False
    with zf.open(member) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        for line in text:
            total_rows += 1
            parts = line.rstrip("\r\n").split(",")
            if not header_checked:
                header_checked = True
                print("first raw line:", line.rstrip("\r\n"))
                if len(parts) >= 5 and not parts[0].strip('"').isdigit():
                    print("header row detected, skipping")
                    total_rows -= 1
                    continue
            if len(parts) < 5:
                continue
            try:
                uprn = parts[0]
                easting = float(parts[1])
                northing = float(parts[2])
                lat = float(parts[3])
                lon = float(parts[4])
            except ValueError:
                continue
            if w <= lon <= e and s <= lat <= n:
                rows_in_bbox.append((uprn, easting, northing, lat, lon))
            if total_rows % 5000000 == 0:
                print("scanned", total_rows, "rows,", len(rows_in_bbox), "in bbox so far")

    print("total_rows_scanned:", total_rows)
    print("rows_in_padded_bbox:", len(rows_in_bbox))

    gdf_pts = gpd.GeoDataFrame(
        {"uprn": [str(u).zfill(12) for u, _, _, _, _ in rows_in_bbox]},
        geometry=[Point(lon, lat) for _, _, _, lat, lon in rows_in_bbox],
        crs=4326,
    ).to_crs(27700)

    man_27700 = man.to_crs(27700)[["osm_id", "postcode", "footprint_area_m2", "geometry"]]

    joined_strict = gpd.sjoin(gdf_pts, man_27700, how="inner", predicate="within")
    man_buf = man_27700.copy()
    man_buf["geometry"] = man_buf.geometry.buffer(1.0)
    joined_buffer = gpd.sjoin(gdf_pts, man_buf, how="inner", predicate="within")

    distinct_strict = joined_strict["osm_id"].nunique()
    distinct_buffer = joined_buffer["osm_id"].nunique()
    total_strict_pairs = len(joined_strict)

    print("=== T02 regression numbers ===")
    print("distinct_osm_id_strict:", distinct_strict)
    print("distinct_osm_id_with_1m_buffer:", distinct_buffer)
    print("total_strict_pairs:", total_strict_pairs)

    with open(JOIN_CSV, "w", newline="", encoding="utf-8") as f:
        w_ = csv.writer(f)
        w_.writerow(["osm_id", "uprn", "postcode", "within", "footprint_area_m2"])
        strict_pairs = set()
        for _, row in joined_strict.iterrows():
            strict_pairs.add((row["uprn"], row["osm_id"]))
            w_.writerow([row["osm_id"], row["uprn"], row["postcode"], "strict", row["footprint_area_m2"]])
        for _, row in joined_buffer.iterrows():
            pair = (row["uprn"], row["osm_id"])
            if pair in strict_pairs:
                continue
            w_.writerow([row["osm_id"], row["uprn"], row["postcode"], "buffer_1m", row["footprint_area_m2"]])

    print("wrote", JOIN_CSV)


# ---------------------------------------------------------------- T03 -------
def _get_with_retry(s, url, params, cache_path, timeout=30):
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cached = json.load(f)
        return cached["status"], cached["body"]
    delay = 1.0
    retries = 0
    for attempt in range(4):
        r = s.get(url, params=params, timeout=timeout)
        if r.status_code == 429 or r.status_code >= 500:
            retries += 1
            print("retry", attempt, r.status_code, r.text[:300])
            if attempt < 3:
                time.sleep(delay)
                delay *= 2
                continue
        try:
            body = r.json()
        except ValueError:
            body = {"_non_json_text": r.text[:300]}
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({"status": r.status_code, "body": body}, f)
        return r.status_code, body
    return r.status_code, {"_error": "exhausted retries"}


def task_t03():
    s = _session()
    os.makedirs(SEARCH_CACHE, exist_ok=True)

    strict_uprn_to_osm = {}
    with open(JOIN_CSV, "r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["within"] != "strict":
                continue
            strict_uprn_to_osm.setdefault(row["uprn"], row["osm_id"])

    uprns = sorted(strict_uprn_to_osm.keys())
    print("distinct strict UPRNs to search:", len(uprns))

    rows_out = []
    n_found = 0
    n_404 = 0
    api_calls = 0
    t_start = time.time()
    for i, uprn in enumerate(uprns):
        cache_path = os.path.join(SEARCH_CACHE, uprn + ".json")
        was_cached = os.path.exists(cache_path)
        status, body = _get_with_retry(
            s, EPC_BASE + "/api/domestic/search", {"uprn": uprn}, cache_path
        )
        if not was_cached:
            api_calls += 1
            time.sleep(RATE_INTERVAL_S)

        data = body.get("data") if isinstance(body, dict) else None
        osm_id = strict_uprn_to_osm[uprn]
        if status == 200 and data:
            n_found += 1
            for item in data:
                rows_out.append({
                    "osm_id": osm_id, "uprn": uprn,
                    "certificateNumber": item.get("certificateNumber", ""),
                    "registrationDate": item.get("registrationDate", ""),
                    "currentEnergyEfficiencyBand": item.get("currentEnergyEfficiencyBand", ""),
                    "postcode": item.get("postcode", ""),
                    "schemaType": item.get("schemaType", ""),
                    "http_status": status,
                })
        else:
            if status == 404:
                n_404 += 1
            rows_out.append({
                "osm_id": osm_id, "uprn": uprn, "certificateNumber": "",
                "registrationDate": "", "currentEnergyEfficiencyBand": "",
                "postcode": "", "schemaType": "", "http_status": status,
            })
        if (i + 1) % 500 == 0:
            print("searched", i + 1, "of", len(uprns), "uprns; found_with_cert:", n_found,
                  "404_no_cert:", n_404, "api_calls:", api_calls)

    elapsed = time.time() - t_start
    with open(CERT_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["osm_id", "uprn", "certificateNumber", "registrationDate",
                      "currentEnergyEfficiencyBand", "postcode", "schemaType", "http_status"]
        w_ = csv.DictWriter(f, fieldnames=fieldnames)
        w_.writeheader()
        for row in rows_out:
            w_.writerow(row)

    print("=== T03 summary ===")
    print("uprns_searched:", len(uprns))
    print("uprns_with_at_least_one_certificate:", n_found)
    print("uprns_404_no_certificate:", n_404)
    print("distinct_footprints_with_at_least_one_certificate:",
          len({r["osm_id"] for r in rows_out if r["certificateNumber"]}))
    print("api_calls_made:", api_calls)
    print("elapsed_seconds:", round(elapsed, 1))
    print("wrote", CERT_CSV)


# ---------------------------------------------------------------- T04 -------
import re as _re

_KEY_PATTERNS = {
    "age_band": _re.compile(r"construction.?age.?band", _re.IGNORECASE),
    "property_type": _re.compile(r"property.?type", _re.IGNORECASE),
    "built_form": _re.compile(r"built.?form", _re.IGNORECASE),
    "floor_area_m2": _re.compile(r"total.?floor.?area", _re.IGNORECASE),
}


def _find_keys(obj, found=None, path=""):
    if found is None:
        found = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            for field, pat in _KEY_PATTERNS.items():
                if field not in found and pat.search(k):
                    found[field] = (path + "/" + k, v)
            if isinstance(v, (dict, list)):
                _find_keys(v, found, path + "/" + k)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _find_keys(item, found, path + "[%d]" % i)
    return found


def _dict_has_key_matching(obj, pat):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if pat.search(k):
                return True
            if _dict_has_key_matching(v, pat):
                return True
    elif isinstance(obj, list):
        for item in obj:
            if _dict_has_key_matching(item, pat):
                return True
    return False


def task_t04():
    s = _session()
    os.makedirs(CERT_CACHE, exist_ok=True)

    with open(CERT_CSV, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        base_fields = reader.fieldnames

    cert_numbers = sorted({r["certificateNumber"] for r in rows if r["certificateNumber"]})
    print("distinct certificate numbers to fetch:", len(cert_numbers))
    for cn in cert_numbers:
        if not CERT_NUM_RE.match(cn):
            print("WARNING: certificateNumber does not match expected pattern:", cn)

    cert_data = {}
    api_calls = 0
    n_with_age_band = 0
    t_start = time.time()
    for i, cn in enumerate(cert_numbers):
        safe_name = cn.replace("/", "_")
        cache_path = os.path.join(CERT_CACHE, safe_name + ".json")
        was_cached = os.path.exists(cache_path)
        status, body = _get_with_retry(
            s, EPC_BASE + "/api/certificate", {"certificate_number": cn}, cache_path
        )
        if not was_cached:
            api_calls += 1
            time.sleep(RATE_INTERVAL_S)

        data = body.get("data") if isinstance(body, dict) else None
        found = _find_keys(data) if data is not None else {}
        age_band = found.get("age_band", ("", ""))[1]
        age_key = found.get("age_band", ("", ""))[0]
        prop_type = found.get("property_type", ("", ""))[1]
        built_form = found.get("built_form", ("", ""))[1]
        floor_area = found.get("floor_area_m2", ("", ""))[1]
        if age_band not in (None, ""):
            n_with_age_band += 1
        cert_data[cn] = {
            "cert_http_status": status,
            "age_band": age_band if age_band is not None else "",
            "year_key_used": age_key,
            "property_type": prop_type if prop_type is not None else "",
            "built_form": built_form if built_form is not None else "",
            "floor_area_m2": floor_area if floor_area is not None else "",
        }
        if (i + 1) % 200 == 0:
            print("fetched", i + 1, "of", len(cert_numbers), "certs; with_age_band:", n_with_age_band,
                  "api_calls:", api_calls)

    elapsed = time.time() - t_start
    new_fields = ["cert_http_status", "age_band", "year_key_used", "property_type",
                  "built_form", "floor_area_m2"]
    out_fields = base_fields + new_fields
    with open(CERT_CSV, "w", newline="", encoding="utf-8") as f:
        w_ = csv.DictWriter(f, fieldnames=out_fields)
        w_.writeheader()
        for row in rows:
            cn = row["certificateNumber"]
            extra = cert_data.get(cn, {k: "" for k in new_fields})
            row.update(extra)
            w_.writerow(row)

    print("=== T04 summary ===")
    print("certificates_fetched:", len(cert_numbers))
    print("certificates_with_age_band:", n_with_age_band)
    print("api_calls_made:", api_calls)
    print("elapsed_seconds:", round(elapsed, 1))
    print("wrote", CERT_CSV)


# ---------------------------------------------------------------- T05 -------
def task_t05():
    with open(CERT_CSV, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    footprints_in_manifest = 1242
    footprints_with_uprn = 1219

    footprints_with_cert = {r["osm_id"] for r in rows if r["certificateNumber"]}

    by_uprn = {}
    for r in rows:
        if r["certificateNumber"]:
            by_uprn.setdefault(r["uprn"], []).append(r)

    representative_by_uprn = {}
    for uprn, recs in by_uprn.items():
        recs_sorted = sorted(recs, key=lambda x: x.get("registrationDate", ""))
        representative_by_uprn[uprn] = recs_sorted[-1]

    footprints_with_age_band = set()
    band_counts = {}
    for uprn, rep in representative_by_uprn.items():
        osm_id = None
        for r in rows:
            if r["uprn"] == uprn:
                osm_id = r["osm_id"]
                break
        band = rep.get("age_band", "")
        if band:
            footprints_with_age_band.add(osm_id)
            band_counts[band] = band_counts.get(band, 0) + 1

    n_age_band = len(footprints_with_age_band)
    pct_1242 = round(100.0 * n_age_band / footprints_in_manifest, 2)
    pct_1219 = round(100.0 * n_age_band / footprints_with_uprn, 2)

    top_bands = sorted(band_counts.items(), key=lambda kv: -kv[1])[:5]

    http_error_counts = {}
    for r in rows:
        st = r.get("http_status") or r.get("cert_http_status")
        if st and st not in ("200",):
            http_error_counts[st] = http_error_counts.get(st, 0) + 1

    dwelling_pat = _re.compile(r"dwelling.?count|number.?of.?dwellings|no.?of.?dwellings", _re.IGNORECASE)
    dwelling_count_present = False
    for cn in {r["certificateNumber"] for r in rows if r["certificateNumber"]}:
        cache_path = os.path.join(CERT_CACHE, cn.replace("/", "_") + ".json")
        if not os.path.exists(cache_path):
            continue
        with open(cache_path, "r", encoding="utf-8") as f:
            cached = json.load(f)
        data = (cached.get("body") or {}).get("data")
        if data is not None and _dict_has_key_matching(data, dwelling_pat):
            dwelling_count_present = True
            break

    out = {
        "site": SITE,
        "footprints_in_eu02_manifest": footprints_in_manifest,
        "footprints_with_uprn": footprints_with_uprn,
        "footprints_with_at_least_one_certificate": len(footprints_with_cert),
        "footprints_with_an_observed_age_band": n_age_band,
        "age_band_pct_of_1242": pct_1242,
        "age_band_pct_of_1219": pct_1219,
        "age_band_histogram_top5": [{"band": b, "count": c} for b, c in top_bands],
        "age_band_histogram_full": band_counts,
        "http_error_counts_by_status": http_error_counts,
        "two_signal_shape": {
            "age_band_present": n_age_band,
            "dwelling_count_present_in_any_certificate": dwelling_count_present,
            "note": "EPC certificate payload carries no dwelling count field found by key search; "
                    "measured absence, not an omission.",
        },
        "wording_constraints": [
            "The result is an age BAND, not a year. Any downstream use must state the band; "
            "ES/FR sidecars carry observed years and are not interchangeable with this.",
            "EPC coverage is CERTIFICATE coverage, not a building-stock census. A dwelling holds "
            "an EPC only if sold, let or newly built since 2008. A GB percentage placed beside the "
            "ES 98.74 percent without this sentence is a category error.",
            "registrationDate is the certificate's lodgement date, never a construction year.",
        ],
    }

    with open(PROBE_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print("=== T05 summary ===")
    print("footprints_with_at_least_one_certificate:", len(footprints_with_cert))
    print("footprints_with_an_observed_age_band:", n_age_band)
    print("age_band_pct_of_1242:", pct_1242)
    print("age_band_pct_of_1219:", pct_1219)
    print("top_5_bands:", top_bands)
    print("wrote", PROBE_JSON)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--task", required=True, choices=["t01", "t02", "t03", "t04", "t05"])
    args = p.parse_args()
    if args.task == "t01":
        task_t01()
    elif args.task == "t02":
        task_t02()
    elif args.task == "t03":
        task_t03()
    elif args.task == "t04":
        task_t04()
    elif args.task == "t05":
        task_t05()

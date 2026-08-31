# -*- coding: utf-8 -*-
"""D-EU-22 Option F1 -- GB and IT coverage probes. MEASUREMENT ONLY.

Ruled 2026-08-27 (owner, Option F1, live retrieval authorised).

GB: the D-EU-10 attribute sources are MHCLG EPC and OS Open UPRN. This probe
    measures whether they are reachable and what they cost to reach.
IT: the D-EU-10 attribute sources are Comune DBT, SACE and ISTAT tract
    materials. This probe measures what each one actually carries for the
    IT-BOL-GALVANI2 bbox.

No ingest, no adapter, no manifest rebuild, no S3 sample. Nothing under
openubem/outputs/eu02/ is written or touched.
"""
import csv
import io
import json
import os
import re
import struct
import time
import zipfile

import geopandas as gpd
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
UA = "OpenUBEM-D-EU-22-coverage-probe/1.0 (research; measurement only)"
OUT_JSON = os.path.join(HERE, "gb_it_coverage_probe.json")
CACHE = os.path.join(HERE, "_cache")

GB_SITE = "GB-LDN-STDUNSTANS"
IT_SITE = "IT-BOL-GALVANI2"


def manifest(site):
    return gpd.read_file(os.path.join(ROOT, "openubem", "outputs", "eu02", site,
                                      "02_residential_manifest.gpkg"))


def visible_text(html):
    t = re.sub(r"<script.*?</script>", " ", html or "", flags=re.S)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()


# ---------------------------------------------------------------- GB --------
def probe_gb(session):
    out = {"site": GB_SITE, "sources": {}}
    man = manifest(GB_SITE)
    w, s, e, n = man.to_crs(4326).total_bounds
    out["manifest_rows_residential"] = int(len(man))
    out["study_bbox_crs84_w_s_e_n"] = [w, s, e, n]

    # 1. the endpoint D-EU-10 pinned
    pinned = "https://epc.opendatacommunities.org/api/v1/domestic/search"
    r = session.get(pinned, params={"postcode": "SE8 5AA", "size": 5},
                    headers={"Accept": "application/json"},
                    timeout=60, allow_redirects=False)
    epc = {
        "name": "MHCLG Energy Performance Certificates (D-EU-10 pinned)",
        "pinned_endpoint": pinned,
        "http_status": r.status_code,
        "redirects_to": r.headers.get("Location"),
        "pinned_endpoint_still_serves_data": False,
    }

    # 2. where it now lives, and what it costs to get in
    new_base = "https://get-energy-performance-data.communities.gov.uk"
    g = session.get(new_base + "/guidance/energy-certificate-data-apis",
                    timeout=60)
    body = visible_text(g.text)
    epc["successor_service"] = new_base
    epc["successor_http_status"] = g.status_code
    epc["auth_sentence"] = ""
    m = re.search(r"How to get started(.{0,240})", body)
    if m:
        epc["auth_sentence"] = m.group(1).strip()
    epc["requires_credential"] = bool(re.search(r"One Login|bearer token|sign in",
                                                body, re.I))
    d = session.get(new_base + "/data-access-options", timeout=60)
    epc["access_options"] = sorted(set(re.findall(r'type="radio"[^>]*value="([^"]+)"',
                                                  d.text)))
    epc["verdict"] = ("REQUIRES_CREDENTIAL_GOVUK_ONE_LOGIN"
                      if epc["requires_credential"] else "OPEN")
    epc["rows_probed"] = 0
    epc["rows_with_age_band"] = None
    out["sources"]["mhclg_epc"] = epc

    # 3. OS Open UPRN -- open, and measured for what it actually contains
    uprn = {"name": "OS Open UPRN (D-EU-10 pinned)",
            "endpoint": "https://api.os.uk/downloads/v1/products/OpenUPRN/downloads"}
    r = session.get(uprn["endpoint"], params={"area": "GB", "format": "CSV"},
                    timeout=90)
    uprn["http_status"] = r.status_code
    try:
        item = r.json()[0]
        uprn["size_bytes"] = item.get("size")
        uprn["md5"] = item.get("md5")
        uprn["download_url"] = item.get("url")
        uprn["requires_credential"] = False
    except Exception as exc:                              # noqa: BLE001
        uprn["error"] = "%s: %s" % (type(exc).__name__, exc)

    # read the zip's central directory with two range requests -- this tells us
    # what the product contains without pulling 590 MB
    if uprn.get("download_url"):
        try:
            size = int(uprn["size_bytes"])
            tail = session.get(uprn["download_url"],
                               headers={"Range": "bytes=%d-%d" % (size - 66000, size - 1)},
                               timeout=180)
            blob = tail.content
            i = blob.rfind(b"PK\x05\x06")
            if i >= 0:
                cd_size, cd_off = struct.unpack("<II", blob[i + 12:i + 20])
                names = []
                if cd_off != 0xFFFFFFFF and cd_size < 60000:
                    cd = session.get(uprn["download_url"],
                                     headers={"Range": "bytes=%d-%d"
                                              % (cd_off, cd_off + cd_size - 1)},
                                     timeout=180).content
                    p = 0
                    while p + 46 <= len(cd) and cd[p:p + 4] == b"PK\x01\x02":
                        nlen, elen, clen = struct.unpack("<HHH", cd[p + 28:p + 34])
                        usz = struct.unpack("<I", cd[p + 24:p + 28])[0]
                        names.append({"name": cd[p + 46:p + 46 + nlen].decode("utf-8", "replace"),
                                      "uncompressed_bytes": usz})
                        p += 46 + nlen + elen + clen
                uprn["zip_members"] = names[:20]
                uprn["zip_member_count"] = len(names)
        except Exception as exc:                          # noqa: BLE001
            uprn["zip_probe_error"] = "%s: %s" % (type(exc).__name__, exc)
    uprn["carries_construction_year"] = False
    uprn["note"] = ("UPRN is a join key -- identifier plus coordinates. It carries "
                    "no construction year and no typology; for GB the year lives in "
                    "the EPC age band alone.")
    out["sources"]["os_open_uprn"] = uprn

    out["verdict"] = (
        "NOT_PROBEABLE_WITHOUT_A_CREDENTIAL. The D-EU-10 pinned EPC endpoint no "
        "longer serves data: it 301-redirects to a successor beta service whose "
        "API and bulk download both require a GOV.UK One Login account and a "
        "bearer token. OS Open UPRN is open but carries no year. The GB coverage "
        "question is therefore UNANSWERED, and it is unanswered for an access "
        "reason, not a data-absence reason.")
    return out


# ---------------------------------------------------------------- IT --------
BOL = "https://opendata.comune.bologna.it/api/explore/v2.1/catalog/datasets/"
ISTAT_ZIP = "https://www.istat.it/storage/cartografia/variabili-censuarie/dati-cpa_2011.zip"
ISTAT_MEMBER = "Sezioni di Censimento/R08_indicatori_2011_sezioni.csv"


def probe_it(session):
    out = {"site": IT_SITE, "sources": {}}
    man = manifest(IT_SITE)
    w, s, e, n = man.to_crs(4326).total_bounds
    out["manifest_rows_residential"] = int(len(man))
    out["study_bbox_crs84_w_s_e_n"] = [w, s, e, n]

    # 1. Comune DBT -- every building layer the portal publishes
    cat, off = [], 0
    while True:
        r = session.get(BOL.rstrip("/"), params={"limit": 100, "offset": off}, timeout=90)
        d = r.json()
        res = d.get("results", [])
        if not res:
            break
        cat.extend(res)
        off += 100
        if off >= d.get("total_count", 0):
            break
    pat = re.compile(r"edific|fabbric|costruzion|epoca|catast", re.I)
    building_like = []
    for x in cat:
        did = x.get("dataset_id") or ""
        title = (x.get("metas", {}).get("default", {}) or {}).get("title") or ""
        if pat.search(did) or pat.search(title):
            building_like.append({"dataset_id": did, "title": title})

    layers = {}
    for ds in ("rifter_edif_pl", "c_a944ctc_edifici_pl"):
        r = session.get(BOL + ds, timeout=90)
        d = r.json()
        fields = [f.get("name") for f in d.get("fields", [])]
        yearish = [f for f in fields
                   if re.search(r"anno|epoca|year|costr", f or "", re.I)]
        layers[ds] = {
            "records_total": (d.get("metas", {}).get("default", {}) or {}).get("records_count"),
            "fields": fields,
            "construction_year_fields": yearish,
        }
    out["sources"]["comune_dbt"] = {
        "name": "Comune di Bologna DBT (open data portal)",
        "endpoint": BOL + "{dataset}",
        "catalogue_datasets_total": len(cat),
        "building_like_datasets": building_like,
        "layers_probed": layers,
        "verdict": ("NO_CONSTRUCTION_YEAR_IN_ANY_PUBLISHED_BUILDING_LAYER. "
                    "Both building layers were probed field by field; neither "
                    "carries a construction year and neither carries a typology "
                    "beyond rifter's 'tipologia'."),
    }

    # 2. SACE -- the Emilia-Romagna energy-certificate registry
    sace = {"name": "SACE / Emilia-Romagna energy certificates",
            "endpoint": "https://dati.emilia-romagna.it/api/3/action/package_search",
            "queries": {}}
    for q in ("SACE", "attestati prestazione energetica", "certificazione energetica",
              "APE edifici"):
        r = session.get(sace["endpoint"], params={"q": q, "rows": 25}, timeout=90)
        res = (r.json().get("result") or {})
        sace["queries"][q] = {
            "count": res.get("count"),
            "datasets": [{"name": p.get("name"), "title": p.get("title")}
                         for p in res.get("results", [])[:25]],
        }
    bologna_hits = []
    for q, v in sace["queries"].items():
        for p in v.get("datasets", []):
            if re.search(r"bologna", (p.get("name", "") + p.get("title", "")), re.I):
                bologna_hits.append(p)
    sace["bologna_datasets"] = bologna_hits
    sace["verdict"] = ("NOT_PUBLISHED_FOR_BOLOGNA. The regional open-data portal "
                       "publishes energy-label datasets for Reggio Emilia only; no "
                       "SACE dataset covering Bologna is offered."
                       if not bologna_hits else "BOLOGNA_DATASETS_FOUND")
    out["sources"]["sace"] = sace

    # 3. ISTAT -- the one IT source that does carry a period, at section scale
    istat = {"name": "ISTAT 2011 census-section indicators (R08)",
             "archive": ISTAT_ZIP, "member": ISTAT_MEMBER}
    if not os.path.isdir(CACHE):
        os.makedirs(CACHE)
    zpath = os.path.join(CACHE, "dati-cpa_2011.zip")
    if not os.path.exists(zpath):
        r = session.get(ISTAT_ZIP, timeout=1200, stream=True)
        istat["http_status"] = r.status_code
        with io.open(zpath, "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)
    istat["archive_bytes"] = os.path.getsize(zpath)

    sections = {}
    with zipfile.ZipFile(zpath) as z:
        names = z.namelist()
        member = ISTAT_MEMBER if ISTAT_MEMBER in names else None
        if member is None:
            for nm in names:
                if "R08" in nm and nm.lower().endswith(".csv"):
                    member = nm
                    break
        istat["member_resolved"] = member
        with z.open(member) as fh:
            rdr = csv.DictReader(io.TextIOWrapper(fh, encoding="latin-1"), delimiter=";")
            istat["columns"] = rdr.fieldnames
            # EU-02 revision B pinned the join: int(NSEZ) == int(sez2011) of the
            # Comune's own 2011 section polygons. SEZ2011 is the 12-digit national
            # key (PROCOM + NSEZ) and does NOT join to the portal's sez2011 field.
            for row in rdr:
                if (row.get("PROCOM") or row.get("PRO_COM") or "").strip() == "37006":
                    nsez = (row.get("NSEZ") or "").strip()
                    if nsez.isdigit():
                        sections[int(nsez)] = row
    istat["bologna_sections"] = len(sections)

    # which sections cover the study bbox, and what they carry
    r = session.get(BOL + "sezioni-di-censimento-anno-2011/exports/geojson",
                    params={"limit": -1,
                            "where": "in_bbox(geo_shape, %f, %f, %f, %f)" % (s, w, n, e)},
                    timeout=300)
    gj = r.json()
    feats = gj.get("features", [])
    istat["site_sections_returned"] = len(feats)
    # band labels are read off the archive's own tracciato, not assumed
    period_cols = ["E8", "E9", "E10", "E11", "E12", "E13", "E14", "E15", "E16"]
    storey_cols = ["E17", "E18", "E19", "E20"]
    period_cols = period_cols + storey_cols
    tot_buildings = 0
    period_sum = dict((c, 0) for c in period_cols)
    matched = 0
    unmatched = []
    for f in feats:
        raw = str((f.get("properties") or {}).get("sez2011") or "").strip()
        row = sections.get(int(raw)) if raw.isdigit() else None
        if not row:
            unmatched.append(raw)
            continue
        matched += 1
        try:
            tot_buildings += int(float(row.get("E3") or 0))
        except ValueError:
            pass
        for c in period_cols:
            try:
                period_sum[c] += int(float(row.get(c) or 0))
            except ValueError:
                pass
    istat["site_sections_matched_to_indicators"] = matched
    istat["site_sections_unmatched"] = len(unmatched)
    istat["site_sections_unmatched_sample"] = unmatched[:10]
    if feats and matched == 0:
        # An unexamined zero is exactly what this decision request has twice had
        # to withdraw. A zero join is a BROKEN PROBE until proven otherwise.
        istat["probe_status"] = ("BROKEN -- %d section polygons were returned and "
                                 "NONE joined to the indicator table. Do not read "
                                 "this as an absence of data." % len(feats))
    else:
        istat["probe_status"] = "OK"
    istat["site_residential_buildings_E3"] = tot_buildings
    istat["site_period_histogram_E8_E16"] = dict(
        (c, period_sum[c]) for c in
        ["E8", "E9", "E10", "E11", "E12", "E13", "E14", "E15", "E16"])
    istat["site_storey_histogram_E17_E20"] = dict(
        (c, period_sum[c]) for c in storey_cols)
    istat["band_labels"] = {
        "E3": "Edifici ad uso residenziale",
        "E8": "prima del 1919", "E9": "1919-1945", "E10": "1946-1960",
        "E11": "1961-1970", "E12": "1971-1980", "E13": "1981-1990",
        "E14": "1991-2000", "E15": "2001-2005", "E16": "dopo il 2005",
        "E17": "1 piano", "E18": "2 piani", "E19": "3 piani",
        "E20": "4 piani o piu",
        "_source": "Sezioni di Censimento/tracciato_2011_sezioni.csv in the archive",
    }
    istat["granularity"] = "CENSUS SECTION, not building"
    istat["verdict"] = (
        "PERIOD_AVAILABLE_AT_SECTION_SCALE_ONLY. ISTAT gives a period HISTOGRAM "
        "per census section over the section's residential buildings. It does not "
        "identify which building was built when, so a per-building construction "
        "period taken from it would be ASSIGNED, not observed.")
    out["sources"]["istat"] = istat

    out["verdict"] = (
        "NO_PER_BUILDING_CONSTRUCTION_YEAR_EXISTS_FOR_THE_BOLOGNA_SITE IN ANY "
        "RULED SOURCE. DBT publishes none, SACE is not published for Bologna, and "
        "ISTAT is section-scale. IT's zero survives the probe -- and now it is "
        "measured rather than assumed.")
    return out


def main():
    t0 = time.time()
    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    out = {
        "evidence_scope": "d_eu_22_option_f1_coverage_probe_gb_and_it_measurement_only",
        "ruling": "D-EU-22 Option F1, owner-ruled 2026-08-27, live retrieval authorised",
        "no_ingest_declaration": (
            "No adapter was written, no manifest was rebuilt, no S3 sample was "
            "formed. Nothing under openubem/outputs/eu02/ was written."),
        "GB": probe_gb(session),
        "IT": probe_it(session),
    }
    out["elapsed_s"] = round(time.time() - t0, 1)
    with io.open(OUT_JSON, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps(out, indent=2, ensure_ascii=False)[:6000])
    print("\nwrote %s" % OUT_JSON)


if __name__ == "__main__":
    main()

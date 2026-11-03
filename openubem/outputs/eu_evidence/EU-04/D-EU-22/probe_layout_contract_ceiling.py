# -*- coding: utf-8 -*-
"""D-EU-22 -- the second ceiling: how many footprints the layout contract can accept.

MEASUREMENT ONLY, and entirely OFFLINE. No live retrieval, no ingest.

Why this exists. D-EU-22 asks whether the ruled attribute sources cover the study
bboxes, because the year and the typology are what excluded ES/GB/IT. But a
recovered year does not make a building formable: Lyon proved that separately,
where 297 rows were layout-ready on ATTRIBUTES and only 18 emitted a dwelling
layout, the rest refused by the GEOMETRIC half of the ruled contract. A ruling on
S3 composition that counts only attribute recovery would over-count the same way.

This census applies the project's OWN predicates -- imported from
openubem.geometry.european_residential, never re-implemented here -- to every
site's existing residential manifest, and reports the population that clears the
geometric half: convex, courtyard-free, and at least NARROW_FOOTPRINT_THRESHOLD_M
wide. It is an UPPER BOUND on dwelling-layout emission, not a prediction: the
contract also requires 2.5 m of facade contact per dwelling, which needs the
dwelling count this probe deliberately does not ingest.
"""
import io
import json
import os

import pandas as pd

from openubem.geometry.european_residential import (
    NARROW_FOOTPRINT_THRESHOLD_M,
    audit_real_footprint_manifest,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
EU02 = os.path.join(ROOT, "openubem", "outputs", "eu02")
OUT_JSON = os.path.join(HERE, "layout_contract_ceiling.json")

SITES = ["ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES",
         "GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2"]


def main():
    out = {
        "evidence_scope": "d_eu_22_geometric_layout_ceiling_offline_measurement_only",
        "predicate_source": "openubem.geometry.european_residential.audit_real_footprint_manifest",
        "narrow_threshold_m": float(NARROW_FOOTPRINT_THRESHOLD_M),
        "is_an_upper_bound_because": (
            "the ruled contract also requires 2.5 m of facade contact per dwelling, "
            "which needs a dwelling count this probe does not ingest. Lyon's own "
            "numbers show the gap: 79 convex footprints of 530, 297 attribute-ready, "
            "18 actually emitted."),
        "sites": {},
    }
    for site in SITES:
        path = os.path.join(EU02, site, "02_residential_manifest.gpkg")
        frame, audit = audit_real_footprint_manifest(path, neighbourhood_id=site)
        clear = frame[(~frame["is_non_convex"])
                      & (~frame["has_courtyard"])
                      & (~frame["fallback_required"])]
        out["sites"][site] = {
            "footprints": int(audit.footprint_count),
            "non_convex": int(audit.non_convex_count),
            "with_courtyard": int(audit.courtyard_count),
            "narrow_lt_8m": int(audit.narrow_fallback_count),
            "clears_geometric_half": int(len(clear)),
            "clears_pct": round(100.0 * len(clear) / max(1, audit.footprint_count), 1),
            "source_sha256": audit.source_sha256,
            "projected_crs": audit.projected_crs,
        }
        print("%-26s %5d footprints -> %4d clear the geometric half (%.1f%%)"
              % (site, audit.footprint_count, len(clear),
                 100.0 * len(clear) / max(1, audit.footprint_count)))

    total = sum(v["clears_geometric_half"] for v in out["sites"].values())
    out["all_four_sites_clearing"] = total
    out["s3_target"] = 96

    # --- calibration against the one site where emission was actually measured
    census = os.path.join(ROOT, "openubem", "outputs", "eu_evidence", "EU-04",
                          "s1_layout_reachability_census.csv")
    cal = {"source": "openubem/outputs/eu_evidence/EU-04/s1_layout_reachability_census.csv"}
    if os.path.exists(census):
        c = pd.read_csv(census)
        clear = c[(c["is_convex"]) & (~c["has_courtyard"])
                  & (c["layout_reason"].fillna("") != "NARROW_FOOTPRINT_LT_8M")]
        emitted = int((c["layout_status"] == "DWELLING_LAYOUT_EMITTED").sum())
        cal.update({
            "attribute_ready_rows": int(len(c)),
            "convex_and_courtyard_free": int(((c["is_convex"]) & (~c["has_courtyard"])).sum()),
            "clears_geometric_half": int(len(clear)),
            "emitted": emitted,
            "partition_audit_failed": int((c["layout_reason"].fillna("")
                                           == "PARTITION_AUDIT_FAILED").sum()),
            "survival_rate_of_geometric_clearers": round(emitted / max(1, len(clear)), 3),
            "note": ("clearing the geometric half is NOT emission: the ruled contract "
                     "also runs a partition audit and a 2.5 m facade-contact test. "
                     "Lyon is the only site where emission has been measured, so its "
                     "survival rate is the only calibration that exists."),
        })
        rate = emitted / max(1, len(clear))
        proj = {}
        for site, v in out["sites"].items():
            proj[site] = int(round(v["clears_geometric_half"] * rate))
        cal["projection_if_lyon_rate_holds"] = proj
        cal["projection_caveat"] = (
            "a projection from ONE site's rate onto three unmeasured urban forms. "
            "It is a planning figure, never a result, and it must be replaced by a "
            "measured census the moment any other site's attributes are ingested.")
    out["calibration"] = cal
    with io.open(OUT_JSON, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=2, ensure_ascii=False))
    print("\nall four sites: %d footprints clear the geometric half; S3 asks for 96."
          % total)
    if "survival_rate_of_geometric_clearers" in cal:
        print("Lyon calibration: %d of %d geometric clearers actually emitted (%.1f%%)"
              % (cal["emitted"], cal["clears_geometric_half"],
                 100.0 * cal["survival_rate_of_geometric_clearers"]))
        print("projection at that rate: %s" % cal["projection_if_lyon_rate_holds"])
    print("wrote %s" % OUT_JSON)


if __name__ == "__main__":
    main()

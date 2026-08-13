# FIX — OPEN-47 T06: erratum, full citation audit, and corrected code comment

**Task:** T06 (Legs A, B, C), `docs/docs_ACTIVE/openings/implemenation/PLAN_three-new-items-2026-08-12.md`.
**Executor:** C. **Date:** 2026-08-12. **Order actually run:** Leg A research + Leg B research,
then T07 (separate report: `RESEARCH_open-47_threshold-provenance.md`), then Leg A/B write-up
(informed by T07's result — see note below), then Leg C.

**Deviation from the plan's literal erratum content, disclosed per hard rule 12:** §3 decision 5 of
the plan anticipates the erratum will say the Table 2 thresholds are "not externally corroborated."
T07 (run after this leg's research but before this file was written) found a real, Crossref-verified
corroborating source that is different from the one `RESULT_I02` cites. Writing "not corroborated"
into a permanent erratum after already knowing that is false would repeat the failure mode this arc
exists to catch. The erratum below states what was actually found, with the same evidence standard
applied throughout this task, and flags the disagreement with the plan's anticipatory text
explicitly rather than silently overriding it.

---

## Leg A — the erratum text (appended to `RESULT_I02`)

The full appended block is reproduced in "Erratum text" below and was appended, unmodified, to the
end of
`docs/docs_DONE/BUGS/input-framework/deepResearch/RESULT_I02_archetype_classification_cascade.md`.
No original line in that file was struck, rewritten, or deleted — confirmed by re-reading the file
after the append; lines 1–117 are byte-identical to before.

## Leg B — citation audit of every reference `RESULT_I02` carries

Method: every document below was downloaded to the scratchpad
(`...\scratchpad\open47\`) and searched with a script or, for DOIs, resolved directly against
`https://api.crossref.org/works/<doi>`. No verdict below is asserted without a retrieval artifact
in that directory. "Unverified" and "fabricated" are recorded as different verdicts per hard rule 10.

| # | `RESULT_I02` reference | Verdict | Evidence |
|---|---|---|---|
| 1 | Deru, M., et al. (2011). *U.S. DOE Commercial Reference Building Models…* NREL/TP-5500-46861. Cited throughout Table 1 as "Section 3.1.1 / 3.1.3 / 3.1.13 / 3.1.15, **Table 3-1**, p. 9" | **Document real; numbers real; citation locator wrong on every row.** | Downloaded via OSTI (`osti.gov/servlets/purl/1009264`, `doi:10.2172/1009264`; the report's own NREL/OSTI URLs are dead — see note below). Author list matches exactly (Deru, Field, Studer, Benne, Griffith, Torcellini + PNNL/LBNL co-authors). All eight Table-1 floor-area figures attributed to Deru (SmallOffice 5,500 ft²/511 m², MediumOffice 53,628/4,982, LargeOffice 498,588/46,320, PrimarySchool 73,960/6,871, SecondarySchool 210,887/19,592, MidriseApartment 33,740/3,135, SmallHotel 43,200/4,013, LargeHotel 122,120/11,345) match the report's real **Table 13 "Reference Building Form Assignments"** (printed p. 19, PDF page 28 of the downloaded copy) exactly, digit-for-digit, confirmed by `pdftotext -f 28 -l 28` (raw, non-`-layout` extraction, to avoid a column-misalignment artifact `-layout` produces on this table). **But "Section 3.1.1" and "Table 3-1" do not exist anywhere in this document.** The report's actual structure is flat: sections `1.0`–`8.0`, tables `Table 1`–`Table 42` sequentially numbered, confirmed against the document's own table of contents (`grep` for `"Table 3-1"` and `"Section 3.1.1"` in the full extraction: 0 hits both). The real location of the floor-area data is **Section 5.2, Table 13, p. 19.** |
| 2 | PNNL (2014). Report PNNL-23269. Cited only for HighriseApartment: "84,360 ft² (~7,837 m²), 10 stories… Section 3.2.1, Table 3." | **Document real (after finding a live mirror); the specific content cited is not in it.** | The URL `RESULT_I02` gives (`energycodes.gov/sites/default/files/2021-07/901_PrototypeBuildingModelEnhancements.pdf`) is **dead (404)**. Retrieved instead from `pnnl.gov/main/publications/external/technical_reports/PNNL-23269.pdf` (200). The document is real and is about window-to-wall-ratio, vestibule, and lighting enhancements to existing 90.1 prototypes — it does not tabulate archetype floor areas at all. Search for `84,360`, `7,837`, and `3.2.1`: **0 hits**. The document's own section numbering (confirmed from its table of contents) is `2.1`, `2.1.2`, `2.2.2`, … — it never reaches a `3.2.1`. Verdict is **unverified, not fabricated**: the 84,360 ft² figure may be correct data drawn from a different PNNL prototype document (not exhaustively searched given the scope of this task), but it is not in the document `RESULT_I02` names, and neither is the section/table locator. |
| 3 | Hong, T., et al. (2015). *Commercial Building Energy Saver…* Applied Energy, 100, 290-302. DOI `10.1016/j.enbuild.2015.04.035` | **Fabricated DOI, independently reconfirmed.** | `https://api.crossref.org/works/10.1016/j.enbuild.2015.04.035` (fetched fresh, this session) resolves to: `{"DOI":"10.1016/j.enbuild.2015.04.035","title":["A combined passive-active sensor fault detection and isolation approach for air handling units"],"author":[{"given":"Miguel","family":"Padilla"},{"given":"Daniel","family":"Choinière"}],"container-title":["Energy and Buildings"],"volume":"99","page":"214-219"}` — an unrelated HVAC fault-detection paper. The title/authors `RESULT_I02` states ("Commercial Building Energy Saver…", Hong et al.) describe a **real** paper, found independently via Crossref bibliographic search: `{"DOI":"10.1016/j.apenergy.2015.09.002","title":["Commercial Building Energy Saver: An energy retrofit analysis toolkit"],"author":["Tianzhen Hong","Mary Ann Piette","Yixing Chen","Sang Hoon Lee","Sarah C. Taylor-Lange","Rongpeng Zhang","Kaiyu Sun","Phillip Price"],"container-title":["Applied Energy"],"volume":"159","page":"298-309"}`. Note `RESULT_I02`'s stated journal/volume/page ("Applied Energy, 100, 290-302") also do not match either the fabricated-DOI paper or the real one (100/290-302 is neither Energy and Buildings 99/214-219 nor Applied Energy 159/298-309) — the reference-list entry is internally inconsistent on top of the wrong DOI. |
| 4 | Sun, K., Luo, N., Luo, X., & Hong, T. (2021). *Prototype energy models for data centers.* Energy and Buildings, Vol. 231, 110586. DOI `10.1016/j.enbuild.2020.110586` | **Fabricated/wrong DOI, found independently — a second instance in the same document, not previously flagged.** | `https://api.crossref.org/works/10.1016/j.enbuild.2020.110586` → **404**. `https://doi.org/10.1016/j.enbuild.2020.110586` → **404** (does not resolve at all, not even to an unrelated paper). Crossref bibliographic search for the stated title + authors finds the real record: `{"DOI":"10.1016/j.enbuild.2020.110603","title":["Prototype energy models for data centers"],"author":["Kaiyu Sun","Na Luo","Xuan Luo","Tianzhen Hong"],"container-title":["Energy and Buildings"],"volume":"231","page":"110603"}` — same title, same four authors in the same order, same journal and volume; only the article number (110586 vs. the real 110603) and hence the DOI are wrong. Downloaded the real paper (`eta-publications.lbl.gov/sites/default/files/prototype_energy_models_for_data_centers.pdf`) and confirmed the specific numbers `RESULT_I02`'s Table 1 attributes to it are genuinely in it: p. 11, "Size, in ft2 (m2) 600 (55.7) 6,000 (557.4)" — matches "Small: 600 ft² (~55.7 m²), Large: 6,000 ft² (~557.4 m²)" exactly. So: **content correctly transcribed, DOI/article-number wrong.** |
| 5 | New, J., et al. (2021). AutoBEM software suite. ORNL. `ornl.gov/project/autobem` | **Real project; cited URL dead (link rot, not fabrication).** | Cited URL → 404 ("Page Not Found \| ORNL"). Live resource found at `ornl.gov/content/automatic-building-energy-modeling-autobem` (200), confirms the AutoBEM project is real and led by Joshua New, matching "New, J., et al." The specific behavioral claim in Table 2 ("no intermediate floor area bins are used by default… assigns nearest matching DOE archetype") was not independently re-verified against page text within this task's time budget — reported as unverified on that specific sentence, verified on project existence and lead author. |
| 6 | NREL (2020). URBANopt Schema Documentation. `docs.urbanopt.net/geojson-gem/building_properties.json` | **Real resource; cited URL dead (link rot).** | Cited URL → 404 ("Page not found · GitHub Pages"). Current resource found at `docs.urbanopt.net/urbanopt-geojson-gem/schemas/building-properties.html` (200), topically the correct "Building Properties" schema page. It is a JS-rendered documentation site; a static fetch returns only navigation chrome, so the specific claim ("user-specified `building_type` property… no automated classification") was **not** independently confirmed against body text — reported as unverified on that sentence, verified on the resource's existence and topic. |
| — | CTBUH Heights Database (Table 3, not in the numbered reference list) | **Verified.** | `ctbuh.org/resource/height` (live, 200): *"a building of 14 or more stories – or more than 50 meters (165 feet) in height – could typically be used as a threshold for a 'tall building'"*; *"a 'supertall' is a tall building 300 meters (984 feet) or taller."* Matches `RESULT_I02`'s claim (tall ≥50m, supertall ≥300m) closely; RESULT_I02's "~15 levels" is a rounding of CTBUH's stated "14 or more stories," and "~90 levels" for supertall is `RESULT_I02`'s own arithmetic (300 m ÷ ~3.3 m/level), not a number CTBUH states directly — both are reasonable, disclosed approximations, not fabrications. |
| — | Fonseca et al. (2016), City Energy Analyst docs (Table 2, not in the numbered reference list) | **Partially verified (existence only).** | `city-energy-analyst.readthedocs.io` live (200). Specific claim text not deep-checked against page content within the time budget. |
| — | MIT Sustainable Design Lab (2019), UMI documentation (Table 2, not in the numbered reference list) | **Partially verified (existence only).** | `web.mit.edu/sustainabledesignlab/projects/umi/index.html` live (200). Specific claim text not deep-checked against page content within the time budget. |

**Tally:** 2 fabricated/wrong DOIs (references 3 and 4 — reference 4 was not previously caught by
this arc), 1 systematic wrong-locator pattern spanning 8 table rows (reference 1 — document and
data are real, every section/table pointer is not), 1 reference whose specific cited content could
not be found in the cited document at all (reference 2), 2 references with dead links to otherwise
real resources (5, 6), 1 fully verified (CTBUH), 2 verified only on existence (Fonseca/CEA, MIT UMI).
**Zero of the eleven rows audited were both fully correct and fully retrievable exactly as cited.**

---

## Erratum text (as appended to `RESULT_I02`)

```markdown
---

## ERRATUM — 2026-08-12 (OPEN-47, T06)

This is an appended correction. Nothing above this line has been struck, rewritten, or deleted;
this block records what a downstream audit (plan `PLAN_three-new-items-2026-08-12.md`, T06/T07)
found when it re-verified this document's citations against the actual sources, one document
download and one Crossref lookup at a time.

**1. The DOI at line 113 is fabricated.** `10.1016/j.enbuild.2015.04.035` resolves (Crossref,
verified 2026-08-12) to Padilla, M. & Choinière, D., "A combined passive-active sensor fault
detection and isolation approach for air handling units," *Energy and Buildings* 99, 214–219 — an
unrelated HVAC fault-detection paper with no connection to office archetype classification.
Crossref record: `{"DOI":"10.1016/j.enbuild.2015.04.035","title":["A combined passive-active
sensor fault detection and isolation approach for air handling units"],"author":[{"given":"Miguel",
"family":"Padilla"},{"given":"Daniel","family":"Choinière"}],"container-title":["Energy and
Buildings"],"volume":"99","page":"214-219"}`.

**2. The real Hong et al. citation.** The paper this document actually meant to cite is Hong, T.,
Piette, M.A., Chen, Y., Lee, S.H., Taylor-Lange, S.C., Zhang, R., Sun, K. & Price, P. (2015),
"Commercial Building Energy Saver: An energy retrofit analysis toolkit," **Applied Energy 159,
298–309**, DOI `10.1016/j.apenergy.2015.09.002` (Crossref-verified 2026-08-12). This paper does
**not** contain the office size-tier thresholds attributed to it in Table 2 of this document — a
script-based search of its full text for `2322`, `2,322`, `9290`, `9,290`, `25,000`, `100,000`
returns zero hits (see `scripts/analysis/open47_threshold_search.py` output).

**3. A second, previously unflagged fabricated DOI.** Reference 4 (Sun, Luo, Luo & Hong, 2021,
"Prototype energy models for data centers") states DOI `10.1016/j.enbuild.2020.110586`. This DOI
**does not resolve** — 404 on both Crossref and `doi.org` directly. The real DOI, found by title
search, is `10.1016/j.enbuild.2020.110603` (same title, same four authors, same journal and
volume; only the article number differs). The Table 1 numbers attributed to this paper (small data
center 600 ft²/55.7 m², large 6,000 ft²/557.4 m²) were checked against the real paper's text and
are correct.

**4. Reference 1's citation locators do not exist in the cited document.** Every Table-1 row
sourced to Deru et al. (2011) cites "Table 3-1, p. 9" (with varying section numbers). The real
report (NREL/TP-5500-46861) uses flat sequential numbering — sections 1.0–8.0, Tables 1–42 — and
contains no "Section 3.1.x" and no "Table 3-1" anywhere. The floor-area figures themselves are
correct and are drawn from the report's real **Table 13, "Reference Building Form Assignments,"
p. 19** — the data was read correctly; only the citation pointer is fabricated.

**5. The Table 2 thresholds ARE traceable to a real, different, Crossref-verified source.**
T07 of the same plan (`scripts/analysis/open47_threshold_search.py`, non-vacuity-controlled search
across six candidate documents) found the exact `<2,322 m² / 2,322–9,290 m² / >9,290 m²` office
tiering — not in the paper cited above, but in **Chen, Y., Hong, T. & Piette, M.A. (2017),
"Automatic generation and simulation of urban building energy models based on city datasets for
city-scale building retrofit analysis," Applied Energy 205, 323–335, DOI
10.1016/j.apenergy.2017.07.128** (Crossref-verified), Table 1, manuscript p. 18: *"Small office
(<2322 m2 and <= 3 floors)"*, *"Medium office* (2322 to 9290 m2, <= 5 floors)"*, *"Large office
(>9290 m2 or >=6 Floors)"*. This table presents the numbers as CityBES's own classification used in
one specific case study (940 San Francisco buildings), not as a citation to an external standard —
it is a real, verifiable, definitional source for CityBES's own rule, but establishes CityBES
practice, not a DOE/PNNL/ASHRAE/CBECS standard. Full candidate-by-candidate search, including the
mandatory non-vacuity controls, is in
`docs/docs_ACTIVE/openings/extra/RESEARCH_open-47_threshold-provenance.md`.

**6. Full citation audit.** Every reference this document carries has been checked against a
downloaded copy or a Crossref resolution; see
`docs/docs_ACTIVE/openings/extra/FIX_open-47_citation-erratum.md` for the complete table. Summary:
2 fabricated/wrong DOIs, 1 reference whose cited content is not found in the cited document at all
(PNNL-23269, HighriseApartment row), 1 reference whose real data is correct but whose section/table
locators are fabricated throughout (Deru et al. 2011), 2 references with dead links to otherwise
real resources, 3 references verified.
```

---

## Leg C — the corrected code comment

**Waited for T07 before writing this**, per the plan. T07 found a real source, so the comment
states what was found rather than "untraced." Comment-only edit, `git diff` shows no executable
line changed:

`openubem/semantic/building_classifier.py` (line 159 in the live tree at the time of this edit —
the plan's line 143 is stale; the constant names `_OFFICE_SMALL_MAX_M2` / `_OFFICE_MEDIUM_MAX_M2`
immediately below it are the unambiguous anchor and were not touched):

Before:
```python
# E-R3-3: office size-tier bins (LBNL CBES 25,000 / 100,000 ft²; Hong et al. 2015)
```

After:
```python
# E-R3-3: office size-tier bins (25,000 / 100,000 ft² = 2,322 / 9,290 m²) match CityBES's
# office classification in Chen, Hong & Piette (2017), Applied Energy 205, 323-335, Table 1
# (DOI 10.1016/j.apenergy.2017.07.128) -- a case-study table, not a cited external standard.
# NOT Hong et al. (2015) as originally written here: that paper does not contain these numbers.
# See OPEN-47 erratum: docs/docs_DONE/BUGS/input-framework/deepResearch/RESULT_I02_archetype_classification_cascade.md
```

`_OFFICE_SMALL_MAX_M2 = 2322.0` and `_OFFICE_MEDIUM_MAX_M2 = 9290.0` are unchanged — they already
match the verified source exactly, so no numeric fix was needed, only the citation.

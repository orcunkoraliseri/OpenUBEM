# PLAN — EU-21 global rules: figure numbering, the LAW section, and the four new readings

**Slug:** `eu21-global-rules` · **Opened:** 2026-09-02 · **Director:** this session · **Executors:** fresh Sonnet, one per slice.
**Governing prompt:** `docs/docs_ACTIVE/europeanLocations/prompts/DIRECTOR_PROMPT_group_floor_planning_2026-09-01.md` (§2 the law, §3 how to run, §4 non-negotiables).
**Predecessor:** `PLAN_eu21-t07-2026-09-02.md` (CLOSED at `CP-3`, `DD-9`/`11`/`12`/`13` ratified, `DD-10` open).

## Owner's authorisation, 2026-09-02 — verbatim

> *"lets start with this one file:///…/TEST_01_three_per_group_2026-09-01.html, can we give numebrs for each thre
> examples under groups. '01 Courtyard': for the middle example, why we have complex corridor, also F4 zone do not have
> outside exposure rather inside the courtyard, so for all floor plans: please add this global rule of zoning, every
> flats needs to exposure to the sunlight and especailly to the outer facade exposures, courtyard exposure is not
> eanouhg. yes we are adding rules in here …/RULES_dwelling_layout_groups_2026-09-01.html, they can be also global
> rules. lets continue, right example, corridor looks good around the courtyard but why to add extra squares inside the
> F1 and F2 zones. '05 Corridor rectangle': i really like the example of right one, the one has long corridor. it is
> amazing. '09 L shape', '10 U or T shape': corridors are complex, instead of showing simply. for the corridors as
> global rule: corridor needs to touch to every flat zones, no need to sunglight exposure for corridors. '11 Complex
> multi-wing': middle and right example corridors are complex, also there is a narrow space problem for the right
> example. lets update the this document and add global rules as well in here
> …/RULES_dwelling_layout_groups_2026-09-01.html. thnk you. then lets re-evalaute later"*

**What that authorises, and nothing more:**

1. Number the example figures inside every test sheet, so a figure can be cited.
2. Write the global rules — the ones that hold in **every** group — into the RULES document as a new LAW section.
3. Add the readings that measure the two new laws whose threshold is not yet fixed, and measure them over all 550 plates.
4. **It does not authorise a cutter rewrite.** The owner asked for the rules to be written and then to re-evaluate.
   `scripts/eu21/05_group_cutters.py` is **read-only in this plan**. Fixing the plans that violate the new law is the
   next plan, and that plan is written from the census this one produces.

**Rulings in force:** `D-EU-64` (one core, flats + core = plate, simple outlines) · `D-EU-65` (ceiling 12 flats/floor) ·
`D-EU-66` (9–10 on `6x2`, engine only) · `D-EU-67` (courtyard cores joined into one zone) · `D-EU-68` (flats are basic
thermal zones) · `DD-1`…`DD-8`, `DD-9`, `DD-11`, `DD-12`, `DD-13` ratified · 🔴 `D-EU-55` (no EnergyPlus without the
owner's own sentence — nothing here runs one).

**New rulings opened by this plan:** `D-EU-69` … `D-EU-72` (§4). Next free after this plan: `D-EU-73` / `FINDING 229`.

---

## 1. Hard rules for the executor

- Edit **only** the file named in the task you are executing. No others, for any reason.
- **`scripts/eu21/05_group_cutters.py` is read-only in this plan.** You may read it and cite it. You may not change one
  character of it. If a law cannot be satisfied without changing it, that is the answer — record it, do not fix it.
- **A measurement task does not fix what it measures.** New readings report; they do not tune a constant until the
  owner has seen the distribution.
- **Never** `git add` / `commit` / `stash` / `restore` / `checkout` / `reset` / `clean`. The tree is dirty and is the owner's.
- **Never** write into `openubem/outputs/eu_evidence/EU-17/` or `EU-20/`. New evidence goes to `EU-21/rules_tests/`.
- **Never** edit `rules/RULES_dwelling_layout_scheme_2026-08-28.html` (frozen; read its CSS only).
- **No generated HTML is ever hand-edited** — `rules/RULES_dwelling_layout_groups_2026-09-01.html` only through `03`,
  `rules/tests/TEST_0N_*.html` only through `04`.
- No `.py` under `docs/`. Create nothing that is not asked for — no extra docs, boards or reports.
- Every solved error is registered in `docs/docs_ACTIVE/europeanLocations/debugs/DEBUG_REFERENCES_european_locations.md`
  ch. 1, house format, **before the task closes**.
- Append one progress-log entry per task under §8 of this file: `#### TXX — <title> — completed YYYY-MM-DD` with
  Artifacts / Deviations / Test status / Notes.
- Do not propose alternatives — execute. If the plan is ambiguous, STOP and quote the conflict.
- Run everything from the repo root with `.venv\Scripts\python.exe` and `PYTHONIOENCODING=utf-8`. A bare `python` is the
  Windows Store stub and exits 49.

---

## 2. File layout

| File | Role in this plan |
|---|---|
| `scripts/eu21/03_build_rules_html.py` | **T02 writes here.** Generator of the RULES document. |
| `scripts/eu21/04_group_tests.py` | **T01 and T03 write here.** Generator of the five TEST sheets and the census. |
| `scripts/eu21/05_group_cutters.py` | **read-only.** The cutter. Cite it; never edit it. |
| `docs/…/rules/RULES_dwelling_layout_groups_2026-09-01.html` | regenerated by `03`. Never hand-edited. |
| `docs/…/rules/tests/TEST_0{1..5}_*.html` | regenerated by `04`. Never hand-edited. |
| `openubem/outputs/eu_evidence/EU-21/rules_tests/` | census JSON. |
| this file §8 | progress log. |

---

## 3. How to run

```
cd C:\Users\o_iseri\Desktop\OpenUBEM
set PYTHONIOENCODING=utf-8
.venv\Scripts\python.exe scripts\eu21\04_group_tests.py --test all   # all five tests + census
.venv\Scripts\python.exe scripts\eu21\03_build_rules_html.py     # the RULES document
```

---

## 4. Dependency decisions — pinned

No new dependency. Everything below uses Shapely 2.x, already imported by `04_group_tests.py`.

**`D-EU-69` — outer-façade exposure.** Every dwelling zone must meet the plate's **outer** perimeter over at least
`2.50` m. Frontage on a courtyard, a light-well or any interior void does **not** count towards it. The circulation zone
is **exempt**: a corridor needs no daylight and may be entirely interior.

**`D-EU-70` — the corridor reaches every flat.** The single circulation zone must share at least `ACCESS_MIN_M = 1.00` m
of boundary with **every** dwelling zone. No flat is reached through another flat.

**`D-EU-71` — the corridor stays simple. Threshold fixed by the owner 2026-09-02 at `CP-2`: at most `16` corner
points.** The circulation zone is one band of near-constant width, not a blob with spurs. Owner's words: *"if possible it
can be lower than that, because mostly corridors are simple shapes"* — the director had recommended 24 and lowered it to
the floor the evidence allows. **Why 16 and not 12:** the four regular groups (`SQUARE`, `RECTANGLE`, `TRIANGLE`,
`TRAPEZOID`) never exceed 12, so 12 is what a genuinely simple corridor costs — but the plate the owner singled out as
the target (*"i really like … it is amazing"*, `CORRIDOR_RECTANGLE` / `i_shape_linear_gallery` on `TEST_01`) reads
**15**. A limit of 12 would condemn the reference shape itself, so 16 is the lowest defensible cap: one point of
headroom above the plate the law is written to protect. Cost measured over the 451 plates that have a circulation zone:
158 fail at 16, against 75 at 24 and 179 at 12. The four regular groups are untouched at any cap ≥ 12.

**`D-EU-72` — no narrow leftover space. Threshold fixed by the owner 2026-09-02 at `CP-2`: no zone narrower than
`2.00` m.** No zone contains only a sliver too thin to inhabit, measured as the largest width that still fits inside the
zone (`R3`). 12 of the 494 drawn plates fail it today.

**`D-EU-73` — how a corridor is drawn. Stated by the owner 2026-09-02 from three annotated images**
(`Screenshot_30.png`, `Screenshot_31.png`, and a hand-redrawn `L_SHAPE`/multi-wing plate). In the first two a red box
replaces a stepped, branched corridor with a single straight rectangle. In the third the owner redraws the whole
plate: three flats, each one entire limb of the footprint with outer façade on three sides, and a **short central
red band** at the waist where the limbs meet. Owner's words: *"red boundaries shows that we can propose simpler
corridors"*; *"corridor can be central, the flat zones needs to be exposed to the outside facades, and simple
design"*; *"the F2 proposal of yours was too complicated"*. Six clauses:

- **(a) One limb, one flat.** Each arm, wing or lobe of the footprint becomes one whole flat. A limb is never split
  lengthwise, and a flat never spans two limbs. This is what gives every flat outer façade on three sides
  (`D-EU-69`), and it is decided before any corridor is drawn.
- **(b) Central band, shortest that works.** The circulation zone is one straight rectangle of constant width
  `CORRIDOR_W` placed at the plate's **waist** — the junction where the limbs meet, or the mid-span of a single
  limb — bearing chosen so it touches every flat (`D-EU-70`). It is sized to the *minimum* length that achieves
  that, never run end to end for its own sake. The core sits against it.
- **(c) No spur.** The corridor never branches to reach a flat the band does not already touch. If a flat is out of
  reach, the band moves or changes bearing, or a flat boundary moves; a stub is never added.
- **(d) No step.** The band's two long edges are straight and parallel between its ends. A corner appears only where
  the outer boundary or a flat boundary clips an end.
- **(e) Chain, not tree.** Where one band provably cannot touch every flat — a courtyard ring, four or more limbs —
  the circulation is a *chain of straight bands joined end to end*, each obeying (b)–(d). The joints are the only
  added corners. Never a T, never a cross, never a comb.
- **(f) Corner budget.** 4 corner points per band, at most 2 more per clipped end, 4 more per additional band in the
  chain. This is what `D-EU-71`'s cap of 16 is rationing: one straight band costs 4–6, a two-band chain 8–10, a
  four-band courtyard ring 14–16.

`D-EU-73` is a **cutter** law, not a check: it says how the drawing is produced, where `D-EU-71` only measures the
result. It is written into the RULES document by this plan (T07) and implemented by the *next* plan. Reference cases:
TEST_01 `L_SHAPE` example 2 (Bologna 29718), `R1` = 23 today and 4–6 under (a)–(b); and the owner's redrawn plate,
where three limbs give three flats and one short waist band replaces a corridor that had been threaded through the
middle of a flat.

---

## 5. DESIGN facts, with line citations

Every fact below was verified by the director on 2026-09-02 against the files as they stand.

1. **`D-EU-69` is already half-implemented, and already written into a check.** `04_group_tests.py:336` computes
   `contacts = [sbuf(f, 0.05).intersection(fp.exterior).length for f in flats]`, where
   `fp = Polygon(rec["footprint"][0], rec["footprint"][1:])` (`:294`). `fp.exterior` is the **outer ring only**, so a
   courtyard — an interior ring — already contributes nothing to it. `C6` passes at `min_contact >= 2.50` (`:338`).
   **The law the owner asked for is `C6`.** What is missing is that it is written down nowhere as a law, and that it
   reads as a per-group detail rather than as something global.
2. **The owner's `COURTYARD` figure 2 already fails.** Madrid `relation/12765478`, scheme
   `wing_spine_decomposition+lightwell`, drawn at 6. Its chips read `C5 62` (bad — the cap is 40 at `:331`) and
   `C6 0.00 m` (bad). Both of the owner's complaints on that figure — the complex corridor, and F4 having no outer
   exposure — are already measured, and the plate is already `FAIL`. 🔴 **`FINDING 228`: the cutter draws plans that
   violate the law instead of refusing them.** The checks catch it afterwards; nothing stops it at generation time.
3. **The "extra squares inside F1 and F2" are the stair cores.** `05_group_cutters.py:678` sets
   `n_c_target = 1 if k == 1 else min(4, max(2, math.ceil(k / 3)))`, and `:685-694 core_box()` places each as a
   `CORE_MIN_SIDE = 2.40` m box (`:30`) just **outside** the gallery ring — i.e. inside the flat band — after which
   `_bridge` joins them to the ring (`:735`, `D-EU-67`). A floor with `k = 2` still gets `max(2, 1) = 2` cores, one
   square per flat. That is the owner's figure 3: Bologna `28651`, `courtyard_cores_gallery`, drawn at 2.
4. **`D-EU-70` is already computed, as an advisory only.** `04_group_tests.py:345` sets `C8` from
   `min(sbuf(f, 0.05).intersection(circ_shape).length for f in flats)` against `ACCESS_MIN_M = 1.0`
   (`05_group_cutters.py:38`), but classes it `info`/`warn` — it never enters the verdict, which counts `C1`–`C6` only
   (`:350`). Promoting `C8` to a hard check is exactly the owner's sentence *"corridor needs to touch to every flat zones"*.
5. **The reference corridor the owner named** is `CORRIDOR_RECTANGLE` figure 3 — Madrid `way/435927693`, 6 storeys,
   45 dwellings declared, 429 m², drawn at 8, scheme `i_shape_linear_gallery`, produced by `cut_convex` at
   `05_group_cutters.py:398`. *"i really like the example of right one, the one has long corridor. it is amazing."*
   `D-EU-71` exists to make the other groups look like this one.
6. **`CORRIDOR_W = 1.80`** (`05_group_cutters.py:28`). A straight gallery of width `w` and length `l` satisfies
   `2·area / perimeter → w` as `l ≫ w`; that is reading `R2` in T03.
7. **Figures cannot be cited today.** `card()` (`04_group_tests.py:374-397`) emits no ordinal, and a refused plate emits
   a shorter card (`:384`) — `L_SHAPE` in `TEST_01` shows 2 drawn plates and 1 refused, so "middle" is already ambiguous.
8. **The RULES document has four top-level sections**, each a `<section class="block">` opening with a
   `<div class="rulehead"><span class="num">…</span>`: `FILTER` (`03_build_rules_html.py:614`), `COVERAGE` (`:625`),
   `GROUPS` (`:653`), `READ` (`:658`). The new `LAW` section joins them.

---

## 6. Task list

### T01 — Number every example figure in the test sheets

**File:** `scripts/eu21/04_group_tests.py` **only.**

**What.** Give every figure inside a group an ordinal — `1`, `2`, `3`, … in the order the figures appear, restarting at
`1` in each group. The ordinal is rendered as a visible badge on the figure **and** repeated as the first token of the
caption, so the owner can write "COURTYARD 2" and mean exactly one plate.

**Why.** §5 fact 7 — today a figure has no name. The owner had to write "middle example" and "right example", and a
refused plate already shifts what "middle" means.

**How.**
- `card(rec, uid)` (`:374`) takes a new positional argument `idx` (1-based). Every call site passes it.
- Numbering counts **all** plates of the group, drawn and refused alike, in the order they are emitted.
- Badge: `<span class="fignum">{idx}</span>` as the **first** child of the `<div class="fig">`, in both the drawn branch
  (`:397`) and the refused branch (`:384`).
- Caption: prefix `cap1` with `<b>{idx}</b> &middot; `.
- CSS, appended to the existing style block near `:684`: `.fignum` — a small square badge at the top-left of the figure,
  `position:absolute` inside a `position:relative` `.fig`, using colour variables **already defined** in that block. Do
  not invent a new palette.

**How to test.**
```
.venv\Scripts\python.exe scripts\eu21\04_group_tests.py
```
Then, for each of the five sheets, the badge count must equal the figure count:
```
grep -o "class=\"fignum\"" <sheet> | wc -l
grep -o "class=\"fig\"" <sheet> | wc -l
```
`TEST_01` must give 33 and 33. Report the five pairs. Also report each sheet's tally line — it must be **unchanged**
from before the task. This is a presentation change and must move no verdict.

---

### T02 — Write the LAW section into the RULES document

**File:** `scripts/eu21/03_build_rules_html.py` **only.**

**What.** A new top-level `<section class="block">` with `<span class="num">LAW</span>` and the heading *"What is true on
every floor plan, in every group"*, inserted **before** the `GROUPS` section (`:653`). It states the global law once, so
it is not scattered across eleven sheets. It contains, in this order:

1. **Already law, restated** — the `D-EU-64` clauses that are global: exactly one circulation zone per plate (`SLIVER`
   excepted, zero); flats + circulation cover ≥ 99.9 % of the plate; drawn = claimed; every zone a simple polygon with
   no hole and no zone inside another; at most 40 corner points per zone.
2. **`D-EU-69` — every flat sees the outer façade.** Owner, 2026-09-02: *"every flat needs exposure to the sunlight and
   especially to the outer facade exposures, courtyard exposure is not enough."* At least `2.50` m of the flat's
   boundary lies on the plate's **outer** perimeter. A courtyard, a light-well or any interior void does **not** count.
   Measured by `C6`, which reads `footprint.exterior` only.
3. **`D-EU-69`, second clause — circulation is exempt.** Owner, 2026-09-02: *"no need to sunlight exposure for
   corridors."* The corridor may be entirely interior.
4. **`D-EU-70` — the corridor reaches every flat.** Owner, 2026-09-02: *"corridor needs to touch to every flat zones."*
   The single circulation zone shares at least `ACCESS_MIN_M` (1.00 m) of boundary with every dwelling zone; no flat is
   reached through another flat. Measured by `C8`, promoted to a hard check in T03.
5. **`D-EU-71` — the corridor stays simple.** One band of near-constant width; no spurs, no blobs. State plainly that
   **the threshold is not yet fixed**, that two readings are being measured over all 550 plates — `R1`, the corner
   points of the circulation zone, and `R2`, the effective width `2·area / perimeter` compared against
   `CORRIDOR_W` = 1.80 m — and that the reference the law aims at is sheet 05's `i_shape_linear_gallery`.
6. **`D-EU-72` — no narrow leftover space.** No zone is a sliver too thin to inhabit. State that the threshold is not
   yet fixed and that reading `R3` — the largest width that still fits inside the zone — is being measured.

Each law is one short paragraph: the rule, then the check or reading that measures it, then the ruling id. Where the law
comes from the owner's own sentence, quote the owner's words, in quotation marks, attributed to 2026-09-02.

Also: in each of the eleven group sheets, add one line under the sheet title — *"The global law applies to this sheet as
well — see LAW."* — linking to the new section's anchor. One line; do not restate the law there.

**Why.** The owner's sentence: *"please add this global rule of zoning … they can be also global rules … lets update the
this document and add global rules as well in here."*

**How.** Follow the existing section idiom exactly (`:613-625`). Reuse the existing CSS classes — `block`, `rulehead`,
`num`, `h2`. Do not add a stylesheet rule unless one is genuinely missing.

**How to test.**
```
.venv\Scripts\python.exe scripts\eu21\03_build_rules_html.py
grep -c "class=\"sheet\"" <rules html>      # must still be 11
grep -c "<svg class=\"plan\"" <rules html>  # must still be 22
grep -o "D-EU-69\|D-EU-70\|D-EU-71\|D-EU-72" <rules html> | sort | uniq -c
```
Report the three results and the new file size. The eleven sheets and the twenty-two figures must be untouched.

---

### T03 — The promoted check and the three new readings, measured over all 550 plates

**File:** `scripts/eu21/04_group_tests.py` **only.**

**What.**
- **Promote `C8` to a hard check** (`D-EU-70`): it passes when `access_min >= ACCESS_MIN_M`, and `"C8"` joins the
  verdict tuple at `:350`. Keep `n/a` — no circulation zone, i.e. `SLIVER` — a **pass**.
- **`C6` is unchanged.** It already *is* `D-EU-69`. Only its wording in `build_checks_html()` (`:437`) changes, to say
  that the contact is with the **outer** perimeter, that courtyard frontage does not count, and to cite `D-EU-69`.
- **Three new readings**, shown as chips like `C7` — class `info` / `warn`, and **never** entering the verdict:
  - **`R1` — circulation corner points.** `len(circ.exterior.coords) - 1` for the single circulation zone; `n/a` when
    there is none.
  - **`R2` — effective corridor width.** `2 * circ.area / circ.length`, in metres, to 2 dp.
  - **`R3` — narrowest zone.** For every zone (flats and circulation), the largest `w` in
    `{0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0}` for which `zone.buffer(-w/2)` is non-empty; report the **minimum** over
    the zones. Use the negative-buffer probe — do not add a dependency.
- Extend `build_checks_html()` so the sheet's own legend explains `R1`–`R3` and says in one line that they are readings,
  not checks.
- The census JSON in `openubem/outputs/eu_evidence/EU-21/rules_tests/` carries `R1`, `R2`, `R3` per plate.

**Why.** §5 facts 1, 4 and 6. `D-EU-70` is the owner's explicit rule and is already computed. `D-EU-71` and `D-EU-72`
are the owner's complaints — *"corridors are complex"*, *"there is a narrow space problem"* — and neither has a number
yet. The arc's method is to measure first and let the owner set the threshold.

**How to test.** Re-run `04` over the full universe, then report, in this order:
1. The **old** tally and the **new** tally of the 550-plate census — `PASS / FAIL / REFUSED / errors`. State how many
   plates changed verdict, and that every one of them changed because of `C8` alone.
2. Per group, the count of plates failing `C6` (`D-EU-69`) and the count failing `C8` (`D-EU-70`).
3. `R1` distribution: min, median, p90, max, and the count above 24.
4. `R2` distribution: min, median, p90, max, and the count outside `[1.0, 3.5]` m.
5. `R3` distribution: min, median, p10, and the count below 2.0 m.
6. The five badge/figure count pairs from T01 again, to prove T01 survived.

Report numbers, not files. The director re-derives anything load-bearing.

---

### T05 — Write the two fixed thresholds into the RULES document

**What.** In `scripts/eu21/03_build_rules_html.py`, the `LAW` section (lines 654-687) still says the two thresholds are
open. Replace the `<div class="callout warn">` block for `D-EU-71` and the one for `D-EU-72` with `callout` blocks that
state the numbers the owner fixed: corridor at most **16** corner points, no zone narrower than **2.00 m**. Drop both
`<span class="tag acc">threshold not yet fixed</span>` tags. Update the `lede` at the top of the section: it currently
reads *"Six clauses hold … Four are already coded and checked today; two are measured but not yet capped — the owner
fixes those numbers at `CP-2`."* — all six are now capped and checked. Name `C9` and `C10` (T06) as the measurements,
the way `D-EU-69` names `C6` and `D-EU-70` names `C8`. Quote the owner once, verbatim: *"if possible it can be lower
than that, because mostly corridors are simple shapes"*. State the reason for 16 rather than 12 in one sentence — the
reference plate `i_shape_linear_gallery` reads 15.

**Why.** A law with an open threshold is not a law. The owner has now closed both.

**How.** Edit `03_build_rules_html.py` only, then run it (§3). Do not hand-edit the generated HTML.

**How to test.** The regenerated `RULES_dwelling_layout_groups_2026-09-01.html` must still contain exactly 11 sheets
(`grep -c 'class="rulehead"'` unchanged), 22 `<svg`, one `id="LAW"` and 11 `#LAW` cross-references; `grep -c
'threshold not yet fixed'` must be **0**; `grep -c 'D-EU-71'` and `grep -c 'D-EU-72'` must each be ≥ 1. Report the byte
size. `05_group_cutters.py` and `04_group_tests.py` must not be touched.

### T06 — Promote the two readings into hard checks and re-measure all 550 plates

**What.** In `scripts/eu21/04_group_tests.py`: turn reading `R1` into check **`C9`** (circulation corner points ≤ `16`)
and reading `R3` into check **`C10`** (narrowest zone ≥ `2.00` m). Define the two limits as module constants
`CORRIDOR_MAX_POINTS = 16` and `ZONE_MIN_WIDTH_M = 2.00` next to the existing constants, and cite `D-EU-71` / `D-EU-72`
beside them. `C9` is `n/a` and passes when the plate has no circulation zone (`SLIVER`); `C10` is always computed.
Both take the same `{"pass": …, "class": "ok"/"bad", "show": …}` shape as `C8` and both enter the verdict tuple, which
becomes `C1`–`C6`, `C8`, `C9`, `C10`. Keep `R2` as a reading (it is `D-EU-71`'s second, uncapped half) and keep `C7`
advisory. Extend `commonest_failed_check()` to include `"C9"` and `"C10"`. Add a `<li>` for each in the checks
documentation, in the same house style as the `C6` and `C8` items, sourced to `D-EU-71` / `D-EU-72` and naming the
owner's `CP-2` ruling of 2026-09-02. Update the READ-section legend line that enumerates which checks gate the verdict.

**Why.** This is the measurement the next plan — the one that changes the cutter — will be written from. Nothing is
repaired here.

**How.** `04_group_tests.py` only, then run it with `--test all` (§3).

**How to test.** Report, from the five current census files `EU-21/rules_tests/test_0N.json` **only** (the `.cap8`,
`.cap12`, `.postpass` and `.t06` siblings in that folder are history — never glob `test_0*.json`): the verdict tally
over all 550, and the per-group count of failing `C9` and failing `C10`. Report the badge/figure pair for each of the
five sheets (must stay 33/132/55/220/110). Confirm `05_group_cutters.py` is byte-identical (54,729 B, mtime 08:48).
**Expected shape, not a target:** `C9` should fail on about 158 plates and `C10` on about 12; `PASS` will drop well
below 436. A drop is the correct result — do not tune anything to prevent it.

### T07 — Write the corridor-design law `D-EU-73` into the RULES document

**What.** In `scripts/eu21/03_build_rules_html.py`, extend the LAW section with a seventh callout for `D-EU-73`,
in the same house style as `D-EU-69`–`D-EU-72`. Reproduce the six clauses (a)–(f) exactly as §4 of this plan states
them, quote the owner's sentence, and say plainly that this clause is **not measured by a check** — it constrains the
cutter, and `D-EU-71`/`C9` is the measurement of its result. Update the section lede so the count of clauses is right.

**Why.** The owner's red boxes are a design instruction, not a threshold. Written down now, implemented next.

**How.** `03_build_rules_html.py` only, then run it (§3). No hand-editing of the generated HTML.

**How to test.** Report from the regenerated `RULES_dwelling_layout_groups_2026-09-01.html`: the byte size, and the
counts of `class="sheet` (must be 11), `<svg` (22), `id="LAW"` (1), `D-EU-73` (≥1), and the six clause labels
`(a)`–`(f)` present inside the LAW section. Confirm `05_group_cutters.py` is byte-identical (54,729 B, mtime 08:48).

## 7. Stop-and-report points

- **`CP-1` — after T01 and T02.** The owner can cite a figure by number, and the law is written down. The director
  verifies the badge counts, that the 11 sheets and 22 figures are still intact in the RULES document, and that
  `05_group_cutters.py` has not been touched (mtime + size).
- **`CP-3` — after T05, T06 and T07.** The six clauses are all written with their numbers and all measured. The director
  verifies the sheet/figure counts, the two new checks' per-group split, and that the cutter is untouched; then writes
  the next plan — the one that repairs the plans the law now catches.
- **`CP-2` — after T03.** The census numbers are on the table. **This is where the owner fixes the two open
  thresholds** — `D-EU-71` (corridor simplicity) and `D-EU-72` (narrow space) — and where the next plan, the one that
  changes the cutter, is written. Nothing in the cutter is fixed before this point.

---

## 8. Progress log

#### T02 — Write the LAW section into the RULES document — completed 2026-09-02

**Artifacts.** `scripts/eu21/03_build_rules_html.py` — new `<section class="block" id="LAW">` inserted before `GROUPS`
(lines 654-687), and one cross-reference line added to each of the eleven sheet titleblocks (line 551 in the sheet
template, emitted 11 times). Regenerated
`docs/docs_ACTIVE/europeanLocations/rules/RULES_dwelling_layout_groups_2026-09-01.html` (135,139 bytes) by running
`03_build_rules_html.py` once.

**Deviations.** None. Followed the task's six-item order exactly; owner quotes taken verbatim from T02's own quoted
text (§6, items 2-4). Reused existing classes only (`block`, `rulehead`, `num`, `h2`, `lede`, `callout warn`, `tag
acc`, `code`, `sub`, and the base `a{color:var(--accent)}` rule already in the frozen CSS) — no new stylesheet rule
added.

**Test status.** Sheet count 11 (unchanged), SVG count 22 (unchanged), `D-EU-69`/`70`/`71`/`72` occurrences 2/1/1/1,
file size 135,139 bytes, `see LAW` cross-reference present on all 11 sheets. `scripts/eu21/04_group_tests.py` and
`scripts/eu21/05_group_cutters.py` were not opened for writing in this task.

**Notes.** No error encountered against the codebase; no `DEBUG_REFERENCES` entry needed.

#### T01 — Number every example figure in the test sheets — completed 2026-09-02

**Artifacts.** `scripts/eu21/04_group_tests.py`: `card()` (`:374`) takes new `idx` param; caption `cap1`
(`:377`) prefixed `<b>{idx}</b> &middot; `; `badge` (`:380`) `<span class="fignum">{idx}</span>` prepended
as first child of `<div class="fig">` in both the refused and drawn branches; call site (`:576-583`) adds
a `fig_idx` counter reset to `0` at the top of each group's loop body and incremented once per `card()`
call across all panes of that group, so numbering restarts at `1` per group and spans size buckets in
`TEST_02`/`TEST_04`. CSS (`:695-696`): `.fig` gained `position:relative`; new `.fignum` rule (absolute,
top-left, `var(--ink)`/`var(--sheet)` — no new palette). Regenerated all five sheets via
`.venv\Scripts\python.exe scripts\eu21\04_group_tests.py --test all`.

**Deviations.** None from §6. Note: plan §3's run command (`04_group_tests.py` with no flags) does not
match the script's pre-existing `argparse` (`--test` is `required=True`); used `--test all`, which is the
documented equivalent ("all five tests + census") and pre-dates this task — not touched here.

**Test status.** Badge/figure pairs: TEST_01 33/33, TEST_02 132/132, TEST_03 55/55, TEST_04 220/220,
TEST_05 110/110 — all five equal, TEST_01 matches the required 33/33. All five sheets' tally lines
(`pass N &middot; fail N &middot; refused N`) are byte-identical to the pre-edit capture — no verdict
moved. `05_group_cutters.py` and `03_build_rules_html.py` untouched (not written this session).

**Notes.** No errors encountered; no `DEBUG_REFERENCES_european_locations.md` entry required.

#### T03 — The promoted check and the three new readings, measured over all 550 plates — completed 2026-09-02

**Artifacts.** `scripts/eu21/04_group_tests.py`: new `NARROW_PROBES_M` constant and `widest_fit(zone)`
helper (`:293-300`, the negative-buffer probe for `R3`) ahead of `run_checks()`. Inside `run_checks()`
(`:350-371`): the `C8` branch now sets `"pass": True` for the no-circulation (`n/a`) case and
`"pass": access_min >= ACCESS_MIN_M` in the circulation case (`:351`, `:357-358`); `R1` (`len(circ.exterior
.coords) - 1`, `n/a` when no circulation, `:352`/`:360`) and `R2` (`2*circ.area/circ.length`, `n/a` when
no circulation, `:353`/`:361-362`) are set alongside `C8` in the same branch; `R3` (`min(widest_fit(z) for
z in flats+cores)`, always computed, `:364-366`) is set once after the branch. All three readings carry
only `"class": "info"` (never `"warn"`) and no `"pass"` key -- no threshold is fixed for `D-EU-71`/`D-EU-72`
per the plan's own hard rule ("a measurement task does not fix what it measures"), so they cannot enter
the verdict tuple, which now reads `("C1","C2","C3","C4","C5","C6","C8")` (`:371`). `card()` (`:419-421`)
appends `R1`/`R2`/`R3` chips after the existing `C8` chip, using each reading's own `"class"`/`"show"`,
unchanged rendering style from `C7`/`C8`. `build_checks_html()`: the `C6` `<li>` (`:468-473`) now states the
contact is with the plate's **outer** perimeter only, that a courtyard/light-well/interior void does not
count, and cites `D-EU-69`; four new `<li>` items appended after the existing `C8` item (`:487-501`) -- one
summary line stating `R1`-`R3` are readings, not checks, that never enter the verdict, then one item each
for `R1`, `R2`, `R3` citing `D-EU-71`/`D-EU-71`/`D-EU-72`. File grew `767 -> 807` lines, `41128` bytes.
Regenerated all five sheets and the five census JSONs via `--test all`.

**Deviations.** None from the letter of §6 T03. One judgment call, recorded here rather than acted on
silently: `build_checks_html()`'s pre-existing `C8` `<li>` (`:481-486` before this edit) still opens
"(report only, never pass/fail)" -- now stale given the promotion -- and the `READ` section's `C8` chip
examples in `build_html()` (`:673-674`, untouched, outside `build_checks_html()`) still read "report only,
access...". §6 T03 names `build_checks_html()` and, within it, only the `C6` wording as things to edit;
it is silent on `C8`'s own wording in either location. Left both untouched, favouring the letter of the
task list over inferring a consistency fix not asked for -- flagged here for the owner/director rather than
invented. `commonest_failed_check()` (`:415-426`, unedited) still loops `C1`-`C6` only, not `C8` -- same
reasoning: not named in §6 T03. Checked empirically: this does not misreport on the 550-plate census (see
Test status) because every plate whose verdict changed also already had a `C1`-`C6` cause visible via `C6`
in three of the eleven groups, or was already `FAIL` before `C8`'s promotion in the fourth case (Madrid
`relation/12765478`, `COURTYARD`, `C6` and `C8` both fail, unchanged verdict) -- so the column is not
observed to go stale on the current data, but it is not structurally guaranteed against a future run.

**Test status.** 550-plate census (494 drawn, 56 refused, 0 cutter errors -- unchanged from before this
task): old tally `PASS 440 / FAIL 54 / REFUSED 56`; new tally `PASS 436 / FAIL 58 / REFUSED 56`. 4 plates
changed verdict, all `PASS -> FAIL`; confirmed programmatically for all 4 that `C1`-`C6` still pass and
only `C8` newly fails -- no other check's `"pass"` value changed on any of the 550 plates. Per group,
count failing `C6` / count failing `C8` (of 494 drawn): `COURTYARD` 4/3, `SLIVER` 0/0, `SQUARE` 0/0,
`RECTANGLE` 0/0, `CORRIDOR_RECTANGLE` 0/0, `SLAB` 0/0, `TRIANGLE` 0/0, `TRAPEZOID` 0/0, `L_SHAPE` 4/1,
`U_OR_T_SHAPE` 3/1, `COMPLEX_MULTI_WING` 11/0 (totals 22 / 5 -- the 5th `C8` fail is Madrid
`relation/12765478`, already `FAIL` on `C6`, so it does not add to the 4 newly changed). `R1`
(circulation corner points, n=451 plates with a circulation zone, 43 `n/a`): min 4, median 12, p90 30,
max 128, 75 above 24. `R2` (effective width m, n=451): min 0.82, median 1.83, p90 2.0, max 3.86, 6 outside
`[1.0, 3.5]`. `R3` (narrowest zone m, n=494, always computed): min 1.0, median 3.0, p10 2.5, 12 below 2.0.
Badge/figure pairs, all equal, T01 numbering intact: `TEST_01` 33/33, `TEST_02` 132/132, `TEST_03` 55/55,
`TEST_04` 220/220, `TEST_05` 110/110. `03_build_rules_html.py` and `05_group_cutters.py` untouched (not
written this session).

**Notes.** No errors encountered; no `DEBUG_REFERENCES_european_locations.md` entry required.


#### T04 (unplanned, wording only) — `C8` described as advisory after its promotion — completed 2026-09-02

**Artifacts.** `scripts/eu21/04_group_tests.py` (41,158 B, 10:34, then the two chip-class lines below);
all five `TEST_0*.html` and all five `test_0*.json` regenerated 10:37.

**Why.** T03 promoted `C8` into the verdict but, being a measurement task, deliberately did not touch the
prose describing it. Four strings still read *"report only, never pass/fail"* — on the very sheet the owner
asked to have updated. A documentation defect, not a runtime one.

**Deviations.** Two changes beyond the dispatched brief, both made by the director directly:
`04_group_tests.py:351` and `:358` set the `C8` chip class to `ok`/`bad` instead of `info`/`warn`, so the
per-plate chips match the legend the same sheet now prints. Presentational only; no `"pass"` value moved.

**Test status.** Re-derived by the director from the five current census files (`test_0N.json` only — the
`.cap8` / `.cap12` / `.postpass` / `.t06` snapshots in the same folder are history and must not be globbed
in): **`PASS` 436 / `FAIL` 58 / `REFUSED` 56 / `ERROR` 0, total 550** — unchanged. `C6` fails 22
(`COMPLEX_MULTI_WING` 11, `COURTYARD` 4, `L_SHAPE` 4, `U_OR_T_SHAPE` 3); `C8` fails 5 (`COURTYARD` 3,
`L_SHAPE` 1, `U_OR_T_SHAPE` 1). `grep -c "report only"` on `TEST_01` = 3, all three `C7`'s own text.
Failing `C8` chips now render `bad`: 0/0/1/2/2 across the five sheets = 5, matching the check.
Figure numbering intact (33/132/55/220/110). `05_group_cutters.py` untouched, 54,729 B, 08:48.

**`CP-1` — signed by the director, 2026-09-02.** Badge counts equal on all five sheets; RULES document
still 11 sheets / 22 figures with one `#LAW` section and 11 cross-references; cutter untouched.

**`CP-2` — open.** The census is on the table and was put to the owner; `D-EU-71` and `D-EU-72` are
waiting on the owner's two numbers. Director's recommendation, anchored on the plate the owner praised
(`i_shape_linear_gallery`, `R1` 15, `R2` 1.78 m, `R3` 2.5 m): `D-EU-71` corridor at most **24** corner
points (75 of 451 plates fail today), `D-EU-72` no zone narrower than **2.0 m** (12 of 494 fail today).
Nothing in the cutter is touched until those two numbers are fixed.

#### T05 — Write the two fixed thresholds into the RULES document — completed 2026-09-02

**Artifacts.** `scripts/eu21/03_build_rules_html.py` — `id="LAW"` section (:654-687) edited only: the
`lede` (:656-658) now reads "All six are now coded, checked and capped — the owner fixed the last two
numbers at `CP-2`, 2026-09-02." (was "Four are already coded ... two are measured but not yet capped").
The `D-EU-71` `<div class="callout warn">` (:674-680) and `D-EU-72` `<div class="callout warn"
style="margin-top:14px">` (:681-685) both lost the `warn` modifier (now plain `class="callout"`, the
existing non-alert variant already defined at `RULES_dwelling_layout_scheme_2026-08-28.html:80-81`, no
new CSS) and both `<span class="tag acc">threshold not yet fixed</span>` tags were dropped. `D-EU-71`
now states "at most 16 corner points", quotes the owner verbatim once ("if possible it can be lower than
that, because mostly corridors are simple shapes"), gives the one-sentence reason for 16 over 12 (the
reference plate `i_shape_linear_gallery` reads 15 corner points), names `C9` as the measurement, and
keeps `R2` as an uncapped reading. `D-EU-72` now states "no zone narrower than 2.00 m" and names `C10`.
Regenerated `docs/docs_ACTIVE/europeanLocations/rules/RULES_dwelling_layout_groups_2026-09-01.html`
(135,377 bytes, was 135,139) by running `03_build_rules_html.py` once.

**Deviations.** None from §6 T05. Judgment call, recorded rather than acted on silently: the task says
"Replace ... with `callout` blocks" (not `callout warn` blocks); read as instructing the drop of the
`warn` modifier since the frozen CSS (`RULES_dwelling_layout_scheme_2026-08-28.html:80-81`) already
defines a plain `.callout` alongside `.callout.warn`, and a law with a number fixed is no longer a
warning. No new class or rule invented.

**Test status.** `class="rulehead"` count 5 (FILTER, COVERAGE, LAW, GROUPS, READ — unchanged from T02's
state); `<svg` count 22; `id="LAW"` count 1; `#LAW` cross-reference count 11; `threshold not yet fixed`
count 0; `D-EU-71` count 1; `D-EU-72` count 1; `C9` count 1; `C10` count 1. File size 135,377 bytes.
`scripts/eu21/05_group_cutters.py` unchanged, 54,729 B, mtime 08:48. `scripts/eu21/04_group_tests.py`
not written this task (mtime 10:37, predates this task's 10:54 run of `03_build_rules_html.py`).

#### T06 — Promote the two readings into hard checks and re-measure all 550 plates — completed 2026-09-02

**Artifacts.** `scripts/eu21/04_group_tests.py` only (42,146 bytes, 820 lines, mtime 10:57). Two new
module constants (`:55-56`) `CORRIDOR_MAX_POINTS = 16` and `ZONE_MIN_WIDTH_M = 2.00`, each commented with
its `D-EU-71`/`D-EU-72` citation and the `CP-2` ruling date. In `run_checks()` (`:305`): the no-circulation
branch (`:352-355`) now also sets `checks["C9"] = {"pass": True, "class": "ok", "show": "n/a"}`; the
circulation branch (`:357-364`) computes `r1` as before and sets `checks["C9"]` from
`c9_pass = r1 <= CORRIDOR_MAX_POINTS`, same `{"pass","class","show"}` shape as `C8`; `checks["R1"]` is
gone (its computation feeds `C9` instead). After the branch (`:367-370`), `checks["C10"]` replaces the old
`checks["R3"]`, using the existing `widest_fit()` reading and `c10_pass = r3 >= ZONE_MIN_WIDTH_M`, always
computed (no `n/a` case). `checks["R2"]` is unchanged, still `"class": "info"` only, in both branches. The
verdict tuple (`:378-379`) is now `("C1","C2","C3","C4","C5","C6","C8","C9","C10")`. `card()` (`:400`)
chip order after `C8` is now `C9`, `R2`, `C10` (`:424-429`), replacing the old
`for rid in ("R1","R2","R3")` loop. `commonest_failed_check()` (`:434`) loop extended to
`("C1",...,"C6","C8","C9","C10")` (`:441`). `build_checks_html()` (`:471`): two new `<li>` items for `C9`
and `C10` in the same house style as `C6`/`C8`, each citing `D-EU-71`/`D-EU-72` and naming the owner's
`CP-2` ruling of 2026-09-02 (`:496-508`); the old `<li>` items for readings `R1` and `R3` are gone (those
readings no longer exist — they were turned into `C9`/`C10`), and the readings-intro `<li>` was reworded
from "R1-R3 are readings, not checks" to name only `R2`. The READ-section legend line enumerating gating
checks (`:664`) now reads `C1&ndash;C6, C8, C9 and C10 pass; C7 report only` (was `...C6 and C8 pass...`).
Ran `.venv\Scripts\python.exe scripts\eu21\04_group_tests.py --test all`, regenerating all five
`TEST_0N_*.html` sheets and all five `test_0N.json` census files.

**Deviations.** None from the letter of §6 T06. Two judgment calls, recorded rather than acted on
silently, following the precedent T03/T04 set for undirected staleness in this same file: (1) the `CHECKS`
section `<h2>` still reads "The eight checks, C1&ndash;C8" (`:672`, unedited) — now stale at ten named
checks — left untouched because T06's "How" names only the `<li>` items and "the READ-section legend line"
(singular) as things to update, not this heading. (2) The `k`-label "All six checks passed" (`:663`,
unedited, already stale before this task since `C8`'s T03 promotion made it seven) was likewise left
untouched for the same reason — not named in T06's scope. Both flagged here for the owner/director rather
than invented. Removing the `R1`/`R3` `<li>` items (rather than merely adding `C9`/`C10` ones) was treated
as required, not optional: leaving them would have described chips (`R1`, `R3`) that no longer render
anywhere in the sheet, which is a stronger defect than an undercounted heading.

**Test status.** Full run, no errors (`python -c` exit clean, no traceback). 550-plate census (494 drawn,
56 refused, 0 cutter errors — unchanged from before this task) read from
`openubem/outputs/eu_evidence/EU-21/rules_tests/test_01.json` … `test_05.json` only. Verdict tally: `PASS`
321 / `FAIL` 173 / `REFUSED` 56 / `ERROR` 0, total 550 (was `PASS` 436 / `FAIL` 58 / `REFUSED` 56 before
this task — a large `PASS` drop, expected and correct per the plan). `C9` fails 158 of 550, per group:
`COURTYARD` 15, `CORRIDOR_RECTANGLE` 12, `SLAB` 17, `L_SHAPE` 33, `U_OR_T_SHAPE` 36, `COMPLEX_MULTI_WING`
45 (all other groups 0). `C10` fails 12 of 550, per group: `COURTYARD` 4, `L_SHAPE` 2, `U_OR_T_SHAPE` 6
(all other groups 0). Both land on the plan's expected shape (~158 / ~12). Badge/figure pairs, all equal,
T01 numbering intact: `TEST_01` 33/33, `TEST_02` 132/132, `TEST_03` 55/55, `TEST_04` 220/220, `TEST_05`
110/110. `scripts/eu21/05_group_cutters.py` confirmed byte-identical and unedited: 54,729 B, mtime 08:48.
`scripts/eu21/03_build_rules_html.py` not opened for writing this task.

**Notes.** No error encountered against the codebase; no `DEBUG_REFERENCES_european_locations.md` entry
needed.

**Notes.** No error encountered against the codebase; no `DEBUG_REFERENCES` entry needed.

#### T07 — Write the corridor-design law D-EU-73 into the RULES document — completed 2026-09-02

**Artifacts.** `scripts/eu21/03_build_rules_html.py` — LAW section lede (`:656-659`) reworded from "Six clauses
hold across all eleven groups... All six are now coded, checked and capped" to "Seven clauses hold... Six are
coded, checked and capped... The seventh, `D-EU-73`, is not itself checked: it constrains how the cutter draws a
corridor, and `D-EU-71`/`C9` measure its result." New `<div class="callout" style="margin-top:14px">` (`:690-723`)
appended after the `D-EU-72` callout, inside `<section id="LAW">`: one paragraph stating the owner's three-image
framing (`Screenshot_30.png`, `Screenshot_31.png`, the hand-redrawn `L_SHAPE`/multi-wing plate) and the three
quoted sentences, one paragraph per clause `(a)`-`(f)` reproduced verbatim from plan §4, and a closing paragraph
stating `D-EU-73` is a cutter law, not a check, and that `D-EU-71`/`C9` measure its result. Regenerated
`docs/docs_ACTIVE/europeanLocations/rules/RULES_dwelling_layout_groups_2026-09-01.html` (138,959 bytes) by running
`03_build_rules_html.py` once.

**Deviations.** None from §6 T07.

**Test status.** `class="sheet` = 11, `<svg` = 22, `id="LAW"` = 1, `D-EU-73` = 3 occurrences, all six clause labels
`(a)` through `(f)` present exactly once each inside the LAW section. `scripts/eu21/05_group_cutters.py` confirmed
byte-identical and unedited: 54,729 B, mtime 08:48. `scripts/eu21/04_group_tests.py` not opened for writing this
task.

**Notes.** No error encountered against the codebase; no `DEBUG_REFERENCES_european_locations.md` entry needed.

#### `CP-3` — director sign-off — 2026-09-02

Verified by the director, not taken from an executor's report. Census read from `EU-21/rules_tests/test_01.json`
… `test_05.json` only: **550 = 321 PASS / 173 FAIL / 56 REFUSED / 0 ERROR**. `C9` fails 158
(`COMPLEX_MULTI_WING` 45, `U_OR_T_SHAPE` 36, `L_SHAPE` 33, `SLAB` 17, `COURTYARD` 15, `CORRIDOR_RECTANGLE` 12; the
four regular groups 0). `C10` fails 12 (`U_OR_T_SHAPE` 6, `COURTYARD` 4, `L_SHAPE` 2). Drawn figures per sheet
32 / 115 / 53 / 191 / 103 = 494, exactly 550 − 56 refused. RULES document 138,959 B with `class="sheet` 11,
`<svg` 22, `id="LAW"` 1, `D-EU-73` 3, and all six clause labels present. `05_group_cutters.py` unchanged at
54,729 B / mtime 08:48. Two stale strings the T06 executor flagged but correctly did not touch — "All six checks
passed" (`04_group_tests.py:663`) and "The eight checks, C1–C8" (`:672`) — were fixed by the director to "All nine
checks passed" and "The ten checks, C1–C10", and all five sheets regenerated.

**Plan CLOSED at `CP-3`.** T01–T07 complete. Owed next: the cutter plan that implements `D-EU-73` and repairs the
173 failing plans.

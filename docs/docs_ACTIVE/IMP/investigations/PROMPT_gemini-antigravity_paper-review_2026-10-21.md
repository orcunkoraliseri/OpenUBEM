# PROMPT — Gemini in Antigravity (local repository access) — OpenUBEM paper review — 2026-10-21

Copy everything below the line into a new Antigravity session opened on `C:\Users\o_iseri\Desktop\OpenUBEM`.

---

You are a reviewer and research assistant for **OpenUBEM**, an open-source urban building energy modelling (UBEM) platform. You have read access to the repository at `C:\Users\o_iseri\Desktop\OpenUBEM`. Your job is to tell us **how to make the OpenUBEM journal paper as strong as two published example papers**, using only evidence you can find in the repository.

## Hard rules

1. **Read only.** Do not edit, move, rename or delete any existing file. The only file you may create is the output file named in "Output" below.
2. **No git commands** that change anything (no commit, add, reset, checkout, push).
3. **No cluster access**, no `ssh`, no job submission, no simulations.
4. **No network calls to the UK energy-certificate API.** The PDF `docs/resources/UK/Energy certificate data APIs – GOV.UK.pdf` contains a personal access token: never copy, print or use that token, and never paste it into your output.
5. If you run Python, use `.venv\Scripts\python.exe` (plain `python` may be a different install). Reading PDFs: `pypdf` is installed.
6. Large files: read in ranges. Do not dump whole files into your context.
7. **Every claim about OpenUBEM must cite a file path (and line number where possible).** If you cannot find evidence, write "not found in repo" — never guess a number.
8. A number in this repo may be **superseded**. A value followed by "superseded" or inside `~~strikethrough~~` must not be used. The current adopted U.S. fleet figure is **171.38 kWh/m² over 8,139 buildings, carbon 1,146,454 t CO₂e** (2026-09-30). The current international district results are in `docs/docs_ACTIVE/europeanLocations/results/` (`EU11_results_2026-10-08_summary.csv` and `EU22_results_*_summary.csv`).

## Read these, in this order

1. `README.md` — what OpenUBEM does and the numbers it publishes (sections "Status & Validation" and "European & International Locations" first).
2. `docs/docs_ACTIVE/IMP/INVESTIGATION_paper-improvement_2026-10-21.md` — our own first-pass review. Your job is to check it, correct it and go deeper, not to repeat it.
3. `docs/examples/main.pdf` — CityEL (Song et al., Sustainable Cities and Society 2025).
4. `docs/examples/1-s2.0-S2210670726005834-main.pdf` — AutoBEM (Li et al., Sustainable Cities and Society 2026).
5. `docs/examples/alternatives.txt` — other tools to compare against (links only; you may open them if your environment has web access).
6. `docs/resources/UK/Energy certificate data APIs – GOV.UK.pdf` — what UK certificate data exists (domestic EPC, non-domestic EPC, DEC). Remember rule 4.
7. Only as needed for evidence: `docs/docs_EXPLANATION/` (plain-language explainers), `docs/docs_REPORTS/`, `docs/docs_VALIDATION/`, `docs/docs_ACTIVE/europeanLocations/BRIEF_european_locations_v5.md`, `openubem/data/scenarios/measures.json`.

## Tasks

1. **Example papers.** For each of the two examples, list its section structure, its stated contributions, how it validates, its key figures and tables, and the three things a reviewer would most likely praise.
2. **Check our investigation.** For every row of the table in §3 of our investigation, say: agree / disagree / change, with one sentence why and the evidence path.
3. **What we missed.** Up to 8 further improvements the examples suggest that our investigation does not list. Same format: improvement, which example, effort (S = writing only, M = small analysis on existing results, L = new simulations or data), evidence that OpenUBEM can or cannot do it today.
4. **Related-work table.** Draft the comparison table of UBEM platforms (at least CityEL, AutoBEM, CityBES, UMI, City Energy Analyst, TEASER, SimStock, and the tools in `alternatives.txt`). Columns: simulation engine, zoning (single / multi-zone / per dwelling), scale, countries covered, validated against measured energy (yes / no / partly), fitted or calibrated parameters (yes / no), open source, data licence. Mark every cell you are unsure of with "?".
5. **UK certificate data.** Say what an EPC/DEC comparison could and could not prove for the London district, keeping in mind that EPC construction year is already an OpenUBEM input for London (search for "FINDING 256" in `docs/docs_ACTIVE/europeanLocations/`).
6. **Draft text.** Write a first draft of (a) the "Research gaps and contributions" section (≤ 350 words) and (b) the "Intended users and limits of use" paragraph (≤ 150 words), using only facts you cited.

## Output

Create exactly one file: `docs/docs_ACTIVE/IMP/RESULT_gemini-antigravity_paper-review_2026-10-21.md`, with these headings in this order:

```
# RESULT — Gemini (Antigravity) paper review — 2026-10-21
## 1. Example papers
## 2. Check of our investigation (row by row)
## 3. What we missed
## 4. Related-work table (draft)
## 5. UK certificate data — what it can and cannot prove
## 6. Draft text
## 7. Evidence list (every file you cited)
## 8. Open questions for the owner (max 5)
```

Plain English, short sentences. Then stop and report the output path. Do not start writing the paper itself.

# Territory Sheets Generator — Design Spec

**Date:** 2026-09-04  
**Status:** Approved

---

## Overview

A single Python script (`generate_sheets.py`) that reads two CSV exports from Territory Helper and produces one `.xlsx` workbook per territory. Each workbook has one tab per unique street in that territory, pre-structured for field use with a notes area and columns for Address, Name, and Phone.

---

## Input Files

| File | Purpose |
|------|---------|
| `Cedar Ridge Territories.csv` | Master list of territories with `TerritoryID`, `CategoryCode`, `Number`, `Category`, etc. |
| `Cedar Ridge Territory Addresses.csv` | All address rows, each linked to a territory via `TerritoryID`. Contains `CategoryCode`, `Category`, `TerritoryAddressID` (building-level), `TerritoryAddressApartmentID` (unit-level), `ApartmentNumber`, `Number`, `Street`, `Name`, `Phone`. |

Both files are UTF-8 with BOM (`utf-8-sig`).

---

## Output

- **Directory:** `output/` (created if absent; gitignored)
- **Filename per territory:** `{CategoryCode}{Number}.xlsx` (e.g. `A12.xlsx`, `R5.xlsx`, `G3.xlsx`)
- `TerritoryID` is internal only — it never appears in any output filename or file content.
- Territories with zero address rows are silently skipped.

---

## Data Loading & Joining

1. Read `Cedar Ridge Territories.csv` → dict keyed by `TerritoryID` → `{CategoryCode, Number, Category}`.
2. Read `Cedar Ridge Territory Addresses.csv` → group rows by `TerritoryID`.
3. Join on `TerritoryID` for data-integrity; use `CategoryCode + Number` only for the output filename.
4. Skip territories with no matching address rows (44 of 153 in the current dataset).

---

## Address Processing Logic

For each territory, rows are grouped by building (`Number` + `Street`):

1. **Split each building group:**
   - `building_rows` — `TerritoryAddressApartmentID` is empty (building-level record)
   - `apartment_rows` — `TerritoryAddressApartmentID` is populated (individual unit)

2. **Emit rules:**
   - If `apartment_rows` exist → emit one row per apartment as `{Number} {Street} #{ApartmentNumber}`; **omit** the building-level row.
   - If no `apartment_rows` → emit the building-level row as `{Number} {Street}` (standalone building, e.g. a leasing office).

3. **Group emitted rows by `Street`** → one tab per unique street name.

4. **Sort order within each tab:** numeric sort on `Number`, then numeric sort on `ApartmentNumber` where present.

5. `Name` and `Phone` values are taken directly from the CSV fields (may be empty; users fill them in).

---

## Excel Sheet Layout

**Tab names:** The street name verbatim (e.g. `East 94th Pl`). Tabs are ordered alphabetically. Excel enforces a 31-character tab-name limit; names exceeding this are truncated with a printed warning.

**Layout per sheet:**

| Row | A | B | C |
|-----|---|---|---|
| 1 | `{CategoryCode}{Number} - {Area}` *(merged A1:C1)* | — | — |
| 2 | `Notes:` *(merged A2:C2)* | — | — |
| 3 | **Address** | **Name** | **Phone** |
| 4+ | e.g. `2935 East 94th Pl #101` | *(CSV value or blank)* | *(CSV value or blank)* |

- Row 1: single merged cell with the territory title, e.g. `A12 - Bandon Trails`. If the territory's `Area` field is empty, render just `A12` with no hyphen.
- Row 2: single merged cell, pre-labelled `Notes:` for user entry.
- Row 3: bold header row.
- Columns auto-sized to fit content.

---

## Script Behaviour

- **Entry point:** `python3 generate_sheets.py` from repo root.
- **Dependency:** `openpyxl` only (`pip install openpyxl`).
- **Console output:** one summary line per territory written, e.g.:
  ```
  ✓ A12  →  output/A12.xlsx  (4 streets, 87 addresses)
  ```
  Followed by a final line: `Skipped N territories with no addresses.`
- **No overwrite guard needed** — the `output/` dir is generated/throwaway; re-running regenerates all files.

---

## .gitignore Change

Add `output/` to the repo's `.gitignore`.

---

## Out of Scope

- No GUI or interactive prompts.
- No filtering by territory type/status.
- No styling beyond bold headers, merged notes cell, and column auto-sizing.
- No deduplication of addresses within a territory (assumed clean input data).

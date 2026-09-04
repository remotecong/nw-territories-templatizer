# Territory Sheets Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a script `generate_sheets.py` that reads `Cedar Ridge Territories.csv` and `Cedar Ridge Territory Addresses.csv` and generates formatted Excel workbooks per territory in an `output/` folder, organized with one tab per street.

**Architecture:** A lightweight modular pipeline: CSV loading and joining (`load_data`), address transformation and grouping logic (`process_addresses`), and Excel formatting/export using `openpyxl` (`export_excel`), orchestrated via `generate_sheets.py`.

**Tech Stack:** Python 3 (stdlib `csv`, `pathlib`), `openpyxl`, `pytest`

**Spec:** [`docs/superpowers/specs/2026-09-04-territory-sheets-design.md`](file:///Users/dillon/git/scheduler-checker/docs/superpowers/specs/2026-09-04-territory-sheets-design.md)

## Global Constraints

- Output directory is `output/` and must be ignored in `.gitignore`.
- CSV files are UTF-8 with BOM (`utf-8-sig`).
- Output workbook naming: `{CategoryCode}{Number}.xlsx` (e.g. `A12.xlsx`). Never expose internal `TerritoryID` to output filenames or content.
- Row 1: Merged A1:C1 showing `{CategoryCode}{Number} - {Area}` (or `{CategoryCode}{Number}` if Area is blank/empty).
- Row 2: Merged A2:C2 showing `Notes:`.
- Row 3: Bold headers `Address`, `Name`, `Phone`.
- Row 4+: Address entries formatted as `{Number} {Street} #{ApartmentNumber}` (if apartment units exist), or `{Number} {Street}` (if standalone building). If apartment units exist at that building address, skip the building-level row.
- Tabs: One tab per unique street, sorted alphabetically, truncated to 31 chars if needed.
- Dependencies: `openpyxl` only (plus `pytest` for tests).

---

### Task 1: Environment & .gitignore Configuration

**Files:**
- Modify: `.gitignore`

**Interfaces:**
- Produces: `output/` ignored in git

- [ ] **Step 1: Check existing .gitignore content**

Run: `cat .gitignore`

- [ ] **Step 2: Add `output/` to `.gitignore`**

Append `output/` to `.gitignore`.

- [ ] **Step 3: Verify git status ignores test output folder**

Run: `mkdir -p output && touch output/test.tmp && git status --porcelain`
Expected: `output/test.tmp` does NOT appear in untracked files. Remove `output/test.tmp`.

- [ ] **Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore output directory in gitignore"
```

---

### Task 2: Data Loading & Joining Modules

**Files:**
- Create: `src/territory_loader.py`
- Test: `tests/test_territory_loader.py`

**Interfaces:**
- Produces:
  - `load_territories(filepath: str) -> dict[str, dict]` mapping `TerritoryID` -> `{"TerritoryID": str, "CategoryCode": str, "Number": str, "Area": str, "Category": str}`
  - `load_addresses(filepath: str) -> dict[str, list[dict]]` mapping `TerritoryID` -> list of address row dicts

- [ ] **Step 1: Write the failing tests**

Create `tests/test_territory_loader.py`:
```python
import io
import pytest
from src.territory_loader import load_territories, load_addresses

def test_load_territories():
    csv_data = (
        "\ufeffTerritoryID,CategoryCode,Category,Number,Area\n"
        "1001,A,Apartment,12,Bandon Trails\n"
        "1002,R,Residential,5,\n"
    )
    f = io.StringIO(csv_data)
    result = load_territories(f)
    assert "1001" in result
    assert result["1001"]["CategoryCode"] == "A"
    assert result["1001"]["Number"] == "12"
    assert result["1001"]["Area"] == "Bandon Trails"
    assert result["1002"]["Area"] == ""

def test_load_addresses():
    csv_data = (
        "\ufeffTerritoryID,Number,Street,TerritoryAddressApartmentID,ApartmentNumber,Name,Phone\n"
        "1001,2935,East 94th Pl,,,,\n"
        "1001,2935,East 94th Pl,999,101,John Doe,555-1234\n"
    )
    f = io.StringIO(csv_data)
    result = load_addresses(f)
    assert "1001" in result
    assert len(result["1001"]) == 2
    assert result["1001"][1]["ApartmentNumber"] == "101"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_territory_loader.py`
Expected: FAIL (ModuleNotFoundError or ImportError)

- [ ] **Step 3: Implement data loader**

Create `src/territory_loader.py`:
```python
import csv
from typing import TextIO, Union
from pathlib import Path

def load_territories(source: Union[str, Path, TextIO]) -> dict[str, dict]:
    """Reads Territories CSV and returns a dict keyed by TerritoryID."""
    if isinstance(source, (str, Path)):
        f = open(source, mode="r", encoding="utf-8-sig")
        should_close = True
    else:
        f = source
        should_close = False

    try:
        reader = csv.DictReader(f)
        territories = {}
        for row in reader:
            tid = row.get("TerritoryID", "").strip()
            if tid:
                territories[tid] = {
                    "TerritoryID": tid,
                    "CategoryCode": row.get("CategoryCode", "").strip(),
                    "Number": row.get("Number", "").strip(),
                    "Area": row.get("Area", "").strip(),
                    "Category": row.get("Category", "").strip(),
                }
        return territories
    finally:
        if should_close:
            f.close()

def load_addresses(source: Union[str, Path, TextIO]) -> dict[str, list[dict]]:
    """Reads Addresses CSV and returns a dict keyed by TerritoryID with list of rows."""
    if isinstance(source, (str, Path)):
        f = open(source, mode="r", encoding="utf-8-sig")
        should_close = True
    else:
        f = source
        should_close = False

    try:
        reader = csv.DictReader(f)
        addresses_by_tid = {}
        for row in reader:
            tid = row.get("TerritoryID", "").strip()
            if tid:
                addresses_by_tid.setdefault(tid, []).append(row)
        return addresses_by_tid
    finally:
        if should_close:
            f.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_territory_loader.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/territory_loader.py tests/test_territory_loader.py
git commit -m "feat: implement territory and address CSV loader"
```

---

### Task 3: Address Processing and Grouping Logic

**Files:**
- Create: `src/address_processor.py`
- Test: `tests/test_address_processor.py`

**Interfaces:**
- Consumes: address rows from `load_addresses`
- Produces:
  - `process_territory_addresses(rows: list[dict]) -> dict[str, list[dict]]`
    Returns a dict mapping `street_name` -> list of formatted records `[{"address": str, "name": str, "phone": str, "raw_number": str, "raw_apt": str}]`
    Streets and address records are sorted numerically by house number then apartment.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_address_processor.py`:
```python
import pytest
from src.address_processor import process_territory_addresses

def test_omit_building_row_when_apartments_exist():
    rows = [
        {"Number": "2935", "Street": "East 94th Pl", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "", "Phone": ""},
        {"Number": "2935", "Street": "East 94th Pl", "TerritoryAddressApartmentID": "11", "ApartmentNumber": "101", "Name": "Alice", "Phone": "111"},
        {"Number": "2935", "Street": "East 94th Pl", "TerritoryAddressApartmentID": "12", "ApartmentNumber": "102", "Name": "Bob", "Phone": "222"},
    ]
    result = process_territory_addresses(rows)
    assert "East 94th Pl" in result
    entries = result["East 94th Pl"]
    assert len(entries) == 2
    assert entries[0]["address"] == "2935 East 94th Pl #101"
    assert entries[0]["name"] == "Alice"
    assert entries[1]["address"] == "2935 East 94th Pl #102"

def test_standalone_building_included_without_suffix():
    rows = [
        {"Number": "2900", "Street": "East 94th Pl", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "Clubhouse", "Phone": "999"},
    ]
    result = process_territory_addresses(rows)
    entries = result["East 94th Pl"]
    assert len(entries) == 1
    assert entries[0]["address"] == "2900 East 94th Pl"
    assert entries[0]["name"] == "Clubhouse"

def test_sort_order_numeric():
    rows = [
        {"Number": "100", "Street": "Main St", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "", "Phone": ""},
        {"Number": "20", "Street": "Main St", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "", "Phone": ""},
        {"Number": "2", "Street": "Main St", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "", "Phone": ""},
    ]
    result = process_territory_addresses(rows)
    addresses = [e["address"] for e in result["Main St"]]
    assert addresses == ["2 Main St", "20 Main St", "100 Main St"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_address_processor.py`
Expected: FAIL

- [ ] **Step 3: Implement address processing**

Create `src/address_processor.py`:
```python
import re
from collections import defaultdict

def _sort_key(num_str: str):
    """Parse numeric and non-numeric portions for natural sorting."""
    if not num_str:
        return (0, "")
    match = re.match(r"^(\d+)(.*)$", num_str.strip())
    if match:
        return (int(match.group(1)), match.group(2).lower())
    return (float("inf"), num_str.lower())

def process_territory_addresses(rows: list[dict]) -> dict[str, list[dict]]:
    """
    Groups addresses by building (Number + Street).
    If apartment units exist, omits the building-level row and formats each unit as {Number} {Street} #{ApartmentNumber}.
    If no apartment units exist, emits the building-level row as {Number} {Street}.
    Returns a dict of street -> sorted list of entry dicts:
        {"address": str, "name": str, "phone": str}
    """
    # Group by (Street, Number)
    buildings = defaultdict(list)
    for row in rows:
        street = row.get("Street", "").strip()
        number = row.get("Number", "").strip()
        if not street:
            continue
        buildings[(street, number)].append(row)

    streets = defaultdict(list)

    for (street, number), b_rows in buildings.items():
        apt_rows = [r for r in b_rows if r.get("TerritoryAddressApartmentID", "").strip()]
        b_only_rows = [r for r in b_rows if not r.get("TerritoryAddressApartmentID", "").strip()]

        if apt_rows:
            # Sort apartments numerically
            apt_rows.sort(key=lambda r: _sort_key(r.get("ApartmentNumber", "")))
            for r in apt_rows:
                apt_num = r.get("ApartmentNumber", "").strip()
                addr_text = f"{number} {street} #{apt_num}" if apt_num else f"{number} {street}"
                streets[street].append({
                    "address": addr_text,
                    "name": r.get("Name", "").strip(),
                    "phone": r.get("Phone", "").strip(),
                    "raw_number": number,
                    "raw_apt": apt_num,
                })
        else:
            for r in b_only_rows:
                streets[street].append({
                    "address": f"{number} {street}".strip(),
                    "name": r.get("Name", "").strip(),
                    "phone": r.get("Phone", "").strip(),
                    "raw_number": number,
                    "raw_apt": "",
                })

    # Sort each street's addresses by house number then apartment number
    for street in streets:
        streets[street].sort(
            key=lambda item: (_sort_key(item["raw_number"]), _sort_key(item["raw_apt"]))
        )

    # Return sorted by street name alphabetically
    return dict(sorted(streets.items(), key=lambda x: x[0].lower()))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_address_processor.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/address_processor.py tests/test_address_processor.py
git commit -m "feat: implement address processing and grouping logic"
```

---

### Task 4: Excel Workbook Generation Module

**Files:**
- Create: `src/excel_writer.py`
- Test: `tests/test_excel_writer.py`

**Interfaces:**
- Consumes:
  - `territory`: `dict` (`CategoryCode`, `Number`, `Area`)
  - `street_addresses`: `dict[str, list[dict]]`
  - `output_path`: `Path`
- Produces: Valid Excel `.xlsx` workbook on disk matching spec layout

- [ ] **Step 1: Write failing test for Excel creation**

Create `tests/test_excel_writer.py`:
```python
from pathlib import Path
import openpyxl
from src.excel_writer import create_territory_workbook

def test_create_territory_workbook(tmp_path: Path):
    territory = {"CategoryCode": "A", "Number": "12", "Area": "Bandon Trails"}
    street_data = {
        "East 94th Pl": [
            {"address": "2935 East 94th Pl #101", "name": "John Doe", "phone": "555-1111"},
            {"address": "2935 East 94th Pl #102", "name": "", "phone": ""},
        ]
    }
    out_file = tmp_path / "A12.xlsx"
    create_territory_workbook(territory, street_data, out_file)

    assert out_file.exists()
    wb = openpyxl.load_workbook(out_file)
    assert "East 94th Pl" in wb.sheetnames
    ws = wb["East 94th Pl"]

    # Check Row 1 Title
    assert ws["A1"].value == "A12 - Bandon Trails"
    # Check Row 2 Notes
    assert ws["A2"].value == "Notes:"
    # Check Row 3 Headers
    assert ws["A3"].value == "Address"
    assert ws["B3"].value == "Name"
    assert ws["C3"].value == "Phone"
    # Check Row 4 Data
    assert ws["A4"].value == "2935 East 94th Pl #101"
    assert ws["B4"].value == "John Doe"
    assert ws["C4"].value == "555-1111"

def test_create_territory_workbook_empty_area(tmp_path: Path):
    territory = {"CategoryCode": "R", "Number": "5", "Area": ""}
    street_data = {"Main St": [{"address": "100 Main St", "name": "", "phone": ""}]}
    out_file = tmp_path / "R5.xlsx"
    create_territory_workbook(territory, street_data, out_file)

    wb = openpyxl.load_workbook(out_file)
    ws = wb["Main St"]
    assert ws["A1"].value == "R5"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_excel_writer.py`
Expected: FAIL

- [ ] **Step 3: Implement Excel workbook generator**

Create `src/excel_writer.py`:
```python
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

def clean_sheet_title(title: str, existing_titles: set[str]) -> str:
    """Excel sheet names are max 31 chars and cannot contain: \ / ? * : [ ]"""
    invalid_chars = [':', '\\', '/', '?', '*', '[', ']']
    cleaned = title
    for ch in invalid_chars:
        cleaned = cleaned.replace(ch, '')
    cleaned = cleaned[:31].strip()
    if not cleaned:
        cleaned = "Street"

    base = cleaned
    counter = 1
    while cleaned in existing_titles:
        suffix = f"_{counter}"
        cleaned = f"{base[:31 - len(suffix)]}{suffix}"
        counter += 1
    existing_titles.add(cleaned)
    return cleaned

def create_territory_workbook(territory: dict, street_addresses: dict[str, list[dict]], output_path: Path) -> Path:
    """Generates an .xlsx workbook for a territory."""
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    cat_code = territory.get("CategoryCode", "").strip()
    num = territory.get("Number", "").strip()
    area = territory.get("Area", "").strip()
    title_text = f"{cat_code}{num} - {area}" if area else f"{cat_code}{num}"

    bold_font = Font(bold=True)
    existing_titles = set()

    for street_name, records in street_addresses.items():
        sheet_title = clean_sheet_title(street_name, existing_titles)
        ws = wb.create_sheet(title=sheet_title)

        # Row 1: Title
        ws.merge_cells("A1:C1")
        ws["A1"] = title_text
        ws["A1"].font = Font(bold=True, size=12)
        ws["A1"].alignment = Alignment(horizontal="left", vertical="center")

        # Row 2: Notes
        ws.merge_cells("A2:C2")
        ws["A2"] = "Notes:"
        ws["A2"].font = Font(italic=True)
        ws["A2"].alignment = Alignment(horizontal="left", vertical="top")
        ws.row_dimensions[2].height = 40  # Allow some height for notes

        # Row 3: Headers
        headers = ["Address", "Name", "Phone"]
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=col_idx, value=header)
            cell.font = bold_font

        # Row 4+: Data
        for row_idx, item in enumerate(records, start=4):
            ws.cell(row=row_idx, column=1, value=item.get("address", ""))
            ws.cell(row=row_idx, column=2, value=item.get("name", ""))
            ws.cell(row=row_idx, column=3, value=item.get("phone", ""))

        # Auto-fit columns
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                # Skip merged rows (1 and 2) for width calculation
                if cell.row in (1, 2):
                    continue
                if cell.value is not None:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 15)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    return output_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_excel_writer.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/excel_writer.py tests/test_excel_writer.py
git commit -m "feat: implement excel workbook formatting and export"
```

---

### Task 5: Script Orchestration & Verification

**Files:**
- Create: `generate_sheets.py`
- Test: Manual / End-to-end verification against real CSV data

**Interfaces:**
- Consumes: `Cedar Ridge Territories.csv`, `Cedar Ridge Territory Addresses.csv`
- Produces: Files in `output/` directory, stdout summary

- [ ] **Step 1: Write `generate_sheets.py`**

```python
import sys
from pathlib import Path
from src.territory_loader import load_territories, load_addresses
from src.address_processor import process_territory_addresses
from src.excel_writer import create_territory_workbook

def main():
    repo_dir = Path(__file__).resolve().parent
    territories_file = repo_dir / "Cedar Ridge Territories.csv"
    addresses_file = repo_dir / "Cedar Ridge Territory Addresses.csv"
    output_dir = repo_dir / "output"

    if not territories_file.exists() or not addresses_file.exists():
        print("Error: Input CSV files not found in the current directory.")
        sys.exit(1)

    print("Loading data...")
    territories = load_territories(territories_file)
    addresses_by_tid = load_addresses(addresses_file)

    output_dir.mkdir(parents=True, exist_ok=True)

    generated_count = 0
    skipped_count = 0

    for tid, terr in territories.items():
        addr_rows = addresses_by_tid.get(tid, [])
        if not addr_rows:
            skipped_count += 1
            continue

        cat_code = terr.get("CategoryCode", "").strip()
        num = terr.get("Number", "").strip()
        filename = f"{cat_code}{num}.xlsx"
        out_path = output_dir / filename

        street_data = process_territory_addresses(addr_rows)
        total_addrs = sum(len(records) for records in street_data.values())

        create_territory_workbook(terr, street_data, out_path)
        print(f"✓ {cat_code}{num:<4} -> {out_path.relative_to(repo_dir)} ({len(street_data)} streets, {total_addrs} addresses)")
        generated_count += 1

    print(f"\nDone! Generated {generated_count} workbooks. Skipped {skipped_count} territories with no addresses.")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run all test suites**

Run: `pytest -v`
Expected: ALL PASS

- [ ] **Step 3: Run `generate_sheets.py` on real data**

Run: `python3 generate_sheets.py`
Expected: Generates 109 Excel workbooks in `output/`, skips 44 empty territories.

- [ ] **Step 4: Verify generated Excel file contents**

Run:
```bash
python3 -c "
import openpyxl
wb = openpyxl.load_workbook('output/A12.xlsx')
print('Sheets:', wb.sheetnames)
ws = wb['East 94th Pl']
print('A1:', ws['A1'].value)
print('A2:', ws['A2'].value)
print('Row 3:', [c.value for c in ws[3]])
print('Row 4:', [c.value for c in ws[4]])
"
```
Verify:
- Sheet title: `A12 - Bandon Trails` (or appropriate area)
- Row 2: `Notes:`
- Row 3: `['Address', 'Name', 'Phone']`
- Row 4: address with apartment suffix `#101`

- [ ] **Step 5: Commit**

```bash
git add generate_sheets.py
git commit -m "feat: implement generate_sheets cli script"
```

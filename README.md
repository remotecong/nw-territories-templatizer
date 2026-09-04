# nw-territories-templatizer

A Python utility that generates structured, printable Excel (`.xlsx`) workbooks from congregation territory and address data.

For every territory that has assigned addresses, the generator produces a formatted workbook where:
- Each unique street has its own tab (with shortened street abbreviations for tab titles).
- A merged header displays the territory designation and area name (e.g., `A12 - Crown Chase Apts`).
- A designated blank Notes section is reserved at the top.
- Address rows are sorted logically and formatted into columns: **Address**, **Name**, and **Phone**.

---

## Data Source: NW Scheduler

The script processes data exported directly from **NW Scheduler**:
1. **Territories Export**: Master territory list including category codes, numbers, areas, and boundaries.
2. **Territory Addresses Export**: Address records including street numbers, street names, unit/apartment numbers, and optional resident names or phone numbers.

> [!WARNING]
> **Hardcoded Filenames Caveat:**  
> The script currently expects the two input CSV files in the repository root directory with these exact names:
> - `Cedar Ridge Territories.csv`
> - `Cedar Ridge Territory Addresses.csv`
>
> If your NW Scheduler export files use a different congregation name or date prefix, rename them to match the filenames above before running the script (or modify the filenames at the top of `generate_sheets.py`).
>
> Both `*.csv` and `output/` are gitignored to prevent accidental leaks of personal address data.

---

## Prerequisites

- Python 3.10+
- [`openpyxl`](https://openpyxl.readthedocs.io/)
- [`pytest`](https://docs.pytest.org/) (optional, for running tests)

You can install dependencies into a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install openpyxl pytest
```

---

## Usage

1. Place your exported CSV files into the repository root named:
   - `Cedar Ridge Territories.csv`
   - `Cedar Ridge Territory Addresses.csv`

2. Run the generator script to create Excel workbooks:
   ```bash
   python generate_sheets.py
   ```
   Generated `.xlsx` files will be saved in the `output/` directory (e.g., `output/A12 - Crown Chase Apts.xlsx`, `output/R5.xlsx`). Territories with no address rows are automatically skipped.

3. Alternatively, generate a summary CSV of territory address counts:
   ```bash
   python count_addresses.py
   ```
   This generates `output/territory_address_counts.csv` with a header row `Territory,Address Count` and each territory (including its area designation if present) alongside its unique address count.

---

## Running Tests

Run the test suite using `pytest`:

```bash
pytest
```

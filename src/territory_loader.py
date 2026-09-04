import csv
import re
from typing import TextIO, Union
from pathlib import Path

def _clean_row(row: dict) -> dict:
    return {k.lstrip('\ufeff').strip(): v for k, v in row.items() if k is not None}

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
        for raw_row in reader:
            row = _clean_row(raw_row)
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
        for raw_row in reader:
            row = _clean_row(raw_row)
            tid = row.get("TerritoryID", "").strip()
            if tid:
                addresses_by_tid.setdefault(tid, []).append(row)
        return addresses_by_tid
    finally:
        if should_close:
            f.close()

def get_territory_filename(terr: dict) -> str:
    """Generates an .xlsx filename based on CategoryCode, Number, and Area."""
    cat_code = terr.get("CategoryCode", "").strip()
    num = terr.get("Number", "").strip()
    area = terr.get("Area", "").strip()
    if not area or area.lower() in ("none", "null", "nil"):
        return f"{cat_code}{num}.xlsx"
    clean_area = re.sub(r'[\\/*?:\"<>|]', '-', area)
    clean_area = re.sub(r'-+', '-', clean_area).strip(' -')
    return f"{cat_code}{num} - {clean_area}.xlsx"

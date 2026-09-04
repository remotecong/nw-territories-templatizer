#!/usr/bin/env python3
import csv
import sys
from pathlib import Path
from typing import TextIO, Union

from src.territory_loader import load_territories, load_addresses, get_territory_display_name
from src.address_processor import count_unique_addresses, _sort_key

def _territory_sort_key(terr: dict):
    cat_code = terr.get("CategoryCode", "").strip()
    number = terr.get("Number", "").strip()
    return (cat_code, _sort_key(number))

def generate_territory_counts(
    territories: dict[str, dict],
    addresses_by_tid: dict[str, list[dict]],
    output_source: Union[str, Path, TextIO],
) -> int:
    """
    Generates a CSV listing each territory with its unique address count.
    Skipping territories with zero addresses.
    Returns the count of territory rows written.
    """
    if isinstance(output_source, (str, Path)):
        output_path = Path(output_source)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        f = open(output_path, mode="w", newline="", encoding="utf-8")
        should_close = True
    else:
        f = output_source
        should_close = False

    try:
        writer = csv.writer(f)
        writer.writerow(["Territory", "Address Count"])

        sorted_territories = sorted(territories.values(), key=_territory_sort_key)
        rows_written = 0

        for terr in sorted_territories:
            tid = terr.get("TerritoryID", "").strip()
            addr_rows = addresses_by_tid.get(tid, [])
            if not addr_rows:
                continue

            count = count_unique_addresses(addr_rows)
            if count == 0:
                continue

            display_name = get_territory_display_name(terr)
            writer.writerow([display_name, count])
            rows_written += 1

        return rows_written
    finally:
        if should_close:
            f.close()

def main():
    repo_dir = Path(__file__).resolve().parent
    territories_file = repo_dir / "Cedar Ridge Territories.csv"
    addresses_file = repo_dir / "Cedar Ridge Territory Addresses.csv"
    output_file = repo_dir / "output" / "territory_address_counts.csv"

    if not territories_file.exists() or not addresses_file.exists():
        print("Error: Input CSV files not found in the current directory.")
        sys.exit(1)

    print("Loading data...")
    territories = load_territories(territories_file)
    addresses_by_tid = load_addresses(addresses_file)

    print("Counting unique addresses per territory...")
    written_count = generate_territory_counts(territories, addresses_by_tid, output_file)

    print(f"\nDone! Wrote {written_count} territories to {output_file.relative_to(repo_dir)}.")

if __name__ == "__main__":
    main()

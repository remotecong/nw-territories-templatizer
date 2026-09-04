#!/usr/bin/env python3
import sys
from pathlib import Path
from src.territory_loader import load_territories, load_addresses, get_territory_filename
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
        filename = get_territory_filename(terr)
        out_path = output_dir / filename

        street_data = process_territory_addresses(addr_rows)
        total_addrs = sum(len(records) for records in street_data.values())

        create_territory_workbook(terr, street_data, out_path)
        print(f"✓ {cat_code}{num:<4} -> {out_path.name} ({len(street_data)} streets, {total_addrs} addresses)")
        generated_count += 1

    print(f"\nDone! Generated {generated_count} workbooks. Skipped {skipped_count} territories with no addresses.")

if __name__ == "__main__":
    main()

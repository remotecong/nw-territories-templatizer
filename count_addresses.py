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
    Generates a CSV listing territories side-by-side by category (R, G, A),
    each with Territory and Address Count columns separated by a blank column.
    Skipping territories with zero addresses.
    Returns the total count of territory rows included.
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

        # Primary categories in order: R, G, A, followed by any extras
        known_categories = ["R", "G", "A"]
        extra_categories = sorted(
            {
                terr.get("CategoryCode", "").strip()
                for terr in territories.values()
                if terr.get("CategoryCode", "").strip()
                and terr.get("CategoryCode", "").strip() not in known_categories
                and addresses_by_tid.get(terr.get("TerritoryID", "").strip())
            }
        )
        categories_order = known_categories + extra_categories

        category_items: dict[str, list[tuple[str, int]]] = {}
        total_territories_count = 0

        for cat in categories_order:
            cat_terrs = [
                t for t in territories.values()
                if t.get("CategoryCode", "").strip() == cat
            ]
            cat_terrs.sort(key=lambda t: _sort_key(t.get("Number", "").strip()))

            items = []
            for terr in cat_terrs:
                tid = terr.get("TerritoryID", "").strip()
                addr_rows = addresses_by_tid.get(tid, [])
                if not addr_rows:
                    continue

                count = count_unique_addresses(addr_rows)
                if count == 0:
                    continue

                display_name = get_territory_display_name(terr)
                items.append((display_name, count))
                total_territories_count += 1

            category_items[cat] = items

        # Build header row: Territory, Address Count, "", Territory, Address Count, ...
        header = []
        for i, _ in enumerate(categories_order):
            if i > 0:
                header.append("")
            header.extend(["Territory", "Address Count"])
        writer.writerow(header)

        # Build data rows
        max_rows = max((len(items) for items in category_items.values()), default=0)
        for row_idx in range(max_rows):
            row = []
            for i, cat in enumerate(categories_order):
                if i > 0:
                    row.append("")  # Spacer column
                items = category_items[cat]
                if row_idx < len(items):
                    row.extend([items[row_idx][0], items[row_idx][1]])
                else:
                    row.extend(["", ""])
            writer.writerow(row)

        return total_territories_count
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

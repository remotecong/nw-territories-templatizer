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

def shorten_street(name: str) -> str:
    """
    Shortens cardinal directions (East -> E, West -> W, North -> N, South -> S)
    and street suffixes (Road -> Rd, Avenue -> Ave, Court -> Ct, Circle -> Cir,
    Boulevard -> Blvd, Street -> St, Parkway -> Pkwy, Place -> Pl, Drive -> Dr, Lane -> Ln).
    """
    replacements = [
        (r'\bEast\b', 'E'),
        (r'\bWest\b', 'W'),
        (r'\bNorth\b', 'N'),
        (r'\bSouth\b', 'S'),
        (r'\bRoad\b', 'Rd'),
        (r'\bAvenues?\b', 'Ave'),
        (r'\bAve\b', 'Ave'),
        (r'\bCourts?\b', 'Ct'),
        (r'\bCt\b', 'Ct'),
        (r'\bCircles?\b', 'Cir'),
        (r'\bCir\b', 'Cir'),
        (r'\bCr\b', 'Cir'),
        (r'\bBoulevards?\b', 'Blvd'),
        (r'\bBlvd\b', 'Blvd'),
        (r'\bBv\b', 'Blvd'),
        (r'\bStreets?\b', 'St'),
        (r'\bSt\b', 'St'),
        (r'\bParkways?\b', 'Pkwy'),
        (r'\bPkwy\b', 'Pkwy'),
        (r'\bPk\b', 'Pkwy'),
        (r'\bPlaces?\b', 'Pl'),
        (r'\bPl\b', 'Pl'),
        (r'\bDrives?\b', 'Dr'),
        (r'\bDr\b', 'Dr'),
        (r'\bLanes?\b', 'Ln'),
        (r'\bLn\b', 'Ln'),
    ]
    res = name
    for pattern, repl in replacements:
        res = re.sub(pattern, repl, res, flags=re.IGNORECASE)
    return ' '.join(res.split())

def process_territory_addresses(rows: list[dict]) -> dict[str, list[dict]]:
    """
    Groups addresses by building (Number + Street).
    If apartment units exist, omits the building-level row and formats each unit as {Number} {Street} #{ApartmentNumber}.
    If no apartment units exist, emits the building-level row as {Number} {Street}.
    Returns a dict of shortened_street -> sorted list of entry dicts:
        {"address": str, "name": str, "phone": str}
    """
    # Group by (shortened_street, Number)
    buildings = defaultdict(list)
    for row in rows:
        raw_street = row.get("Street", "").strip()
        number = row.get("Number", "").strip()
        if not raw_street:
            continue
        tab_street = shorten_street(raw_street)
        buildings[(tab_street, number)].append(row)

    streets = defaultdict(list)

    for (tab_street, number), b_rows in buildings.items():
        apt_rows = [r for r in b_rows if r.get("TerritoryAddressApartmentID", "").strip()]
        b_only_rows = [r for r in b_rows if not r.get("TerritoryAddressApartmentID", "").strip()]

        if apt_rows:
            apt_rows.sort(key=lambda r: _sort_key(r.get("ApartmentNumber", "")))
            for r in apt_rows:
                raw_street = r.get("Street", "").strip()
                apt_num = r.get("ApartmentNumber", "").strip()
                addr_text = f"{number} {raw_street} #{apt_num}" if apt_num else f"{number} {raw_street}"
                streets[tab_street].append({
                    "address": addr_text,
                    "name": r.get("Name", "").strip(),
                    "phone": r.get("Phone", "").strip(),
                    "raw_number": number,
                    "raw_apt": apt_num,
                })
        else:
            for r in b_only_rows:
                raw_street = r.get("Street", "").strip()
                streets[tab_street].append({
                    "address": f"{number} {raw_street}".strip(),
                    "name": r.get("Name", "").strip(),
                    "phone": r.get("Phone", "").strip(),
                    "raw_number": number,
                    "raw_apt": "",
                })

    for s in streets:
        streets[s].sort(
            key=lambda item: (_sort_key(item["raw_number"]), _sort_key(item["raw_apt"]))
        )

    return dict(sorted(streets.items(), key=lambda x: x[0].lower()))

def count_unique_addresses(rows: list[dict]) -> int:
    """Returns the count of unique formatted addresses for a territory."""
    street_data = process_territory_addresses(rows)
    unique_addrs = {
        entry["address"]
        for records in street_data.values()
        for entry in records
    }
    return len(unique_addrs)

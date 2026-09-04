import pytest
from src.address_processor import process_territory_addresses, shorten_street, count_unique_addresses

def test_shorten_street():
    assert shorten_street("East 108th Avenue") == "E 108th Ave"
    assert shorten_street("East 100th Street South") == "E 100th St S"
    assert shorten_street("Cedar Ridge Road") == "Cedar Ridge Rd"
    assert shorten_street("East 105th Court") == "E 105th Ct"
    assert shorten_street("West Circle Drive") == "W Cir Dr"
    assert shorten_street("North Boulevard Parkway") == "N Blvd Pkwy"
    assert shorten_street("South 88th Avenue East") == "S 88th Ave E"
    assert shorten_street("East 94th Pl") == "E 94th Pl"
    assert shorten_street("Birdie Lane") == "Birdie Ln"

def test_omit_building_row_when_apartments_exist():
    rows = [
        {"Number": "2935", "Street": "East 94th Pl", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "", "Phone": ""},
        {"Number": "2935", "Street": "East 94th Pl", "TerritoryAddressApartmentID": "11", "ApartmentNumber": "101", "Name": "Alice", "Phone": "111"},
        {"Number": "2935", "Street": "East 94th Pl", "TerritoryAddressApartmentID": "12", "ApartmentNumber": "102", "Name": "Bob", "Phone": "222"},
    ]
    result = process_territory_addresses(rows)
    assert "E 94th Pl" in result
    entries = result["E 94th Pl"]
    assert len(entries) == 2
    assert entries[0]["address"] == "2935 East 94th Pl #101"
    assert entries[0]["name"] == "Alice"
    assert entries[1]["address"] == "2935 East 94th Pl #102"

def test_standalone_building_included_without_suffix():
    rows = [
        {"Number": "2900", "Street": "East 94th Pl", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "Clubhouse", "Phone": "999"},
    ]
    result = process_territory_addresses(rows)
    entries = result["E 94th Pl"]
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

def test_groups_spelling_variations_under_shortened_name():
    rows = [
        {"Number": "10", "Street": "East Eagle Drive", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "A", "Phone": ""},
        {"Number": "20", "Street": "East Eagle Dr", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "B", "Phone": ""},
    ]
    result = process_territory_addresses(rows)
    assert list(result.keys()) == ["E Eagle Dr"]
    assert len(result["E Eagle Dr"]) == 2

def test_count_unique_addresses_empty():
    assert count_unique_addresses([]) == 0

def test_count_unique_addresses_standalone_and_duplicates():
    rows = [
        {"Number": "9414", "Street": "South Winston Avenue East", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "", "Phone": ""},
        {"Number": "9414", "Street": "South Winston Avenue East", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "", "Phone": ""},
        {"Number": "9416", "Street": "South Winston Avenue East", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "", "Phone": ""},
    ]
    # 9414 is duplicated, so 2 unique addresses total
    assert count_unique_addresses(rows) == 2

def test_count_unique_addresses_with_apartments():
    rows = [
        # Building header row (should not be counted separately when apartments exist)
        {"Number": "2935", "Street": "East 94th Pl", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "", "Phone": ""},
        # Apartment units
        {"Number": "2935", "Street": "East 94th Pl", "TerritoryAddressApartmentID": "1", "ApartmentNumber": "101", "Name": "", "Phone": ""},
        {"Number": "2935", "Street": "East 94th Pl", "TerritoryAddressApartmentID": "2", "ApartmentNumber": "102", "Name": "", "Phone": ""},
        # Duplicate apartment unit
        {"Number": "2935", "Street": "East 94th Pl", "TerritoryAddressApartmentID": "3", "ApartmentNumber": "102", "Name": "", "Phone": ""},
        # Standalone house
        {"Number": "2900", "Street": "East 94th Pl", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "", "Phone": ""},
    ]
    # 2935 #101, 2935 #102, 2900 -> 3 unique addresses total
    assert count_unique_addresses(rows) == 3

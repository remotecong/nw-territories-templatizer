import csv
import io
import pytest
from count_addresses import generate_territory_counts

def test_generate_territory_counts():
    territories = {
        "1": {"TerritoryID": "1", "CategoryCode": "A", "Number": "12", "Area": "Crown Chase Apts"},
        "2": {"TerritoryID": "2", "CategoryCode": "A", "Number": "2", "Area": "Bandon Trails"},
        "3": {"TerritoryID": "3", "CategoryCode": "R", "Number": "5", "Area": ""},
        "4": {"TerritoryID": "4", "CategoryCode": "R", "Number": "1", "Area": "North Oak"},
        "5": {"TerritoryID": "5", "CategoryCode": "G", "Number": "1", "Area": "Riverbend"},
        "6": {"TerritoryID": "6", "CategoryCode": "R", "Number": "99", "Area": "Empty Area"},
    }
    addresses_by_tid = {
        "1": [
            {"Number": "2935", "Street": "East 94th Pl", "TerritoryAddressApartmentID": "1", "ApartmentNumber": "101", "Name": "", "Phone": ""},
            {"Number": "2935", "Street": "East 94th Pl", "TerritoryAddressApartmentID": "2", "ApartmentNumber": "102", "Name": "", "Phone": ""},
        ],
        "2": [
            {"Number": "100", "Street": "Main St", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "", "Phone": ""},
        ],
        "3": [
            {"Number": "50", "Street": "Oak Ave", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "", "Phone": ""},
            {"Number": "50", "Street": "Oak Ave", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "", "Phone": ""},
        ],
        "4": [
            {"Number": "10", "Street": "First St", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "", "Phone": ""},
        ],
        "5": [
            {"Number": "500", "Street": "River Rd", "TerritoryAddressApartmentID": "", "ApartmentNumber": "", "Name": "", "Phone": ""},
        ],
    }

    out = io.StringIO()
    total_territories = generate_territory_counts(territories, addresses_by_tid, out)

    assert total_territories == 5
    out.seek(0)
    reader = list(csv.reader(out))

    # Header row with R, G, A sections separated by empty column
    assert reader[0] == ["Territory", "Address Count", "", "Territory", "Address Count", "", "Territory", "Address Count"]
    # Row 1
    assert reader[1] == ["R1 - North Oak", "1", "", "G1 - Riverbend", "1", "", "A2 - Bandon Trails", "1"]
    # Row 2 (G is exhausted, so its cells are empty)
    assert reader[2] == ["R5", "1", "", "", "", "", "A12 - Crown Chase Apts", "2"]
    assert len(reader) == 3

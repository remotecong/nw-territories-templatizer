import csv
import io
import pytest
from count_addresses import generate_territory_counts

def test_generate_territory_counts():
    territories = {
        "1": {"TerritoryID": "1", "CategoryCode": "A", "Number": "12", "Area": "Crown Chase Apts"},
        "2": {"TerritoryID": "2", "CategoryCode": "A", "Number": "2", "Area": "Bandon Trails"},
        "3": {"TerritoryID": "3", "CategoryCode": "R", "Number": "5", "Area": ""},
        "4": {"TerritoryID": "4", "CategoryCode": "R", "Number": "99", "Area": "Empty Area"},
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
    }

    out = io.StringIO()
    written_count = generate_territory_counts(territories, addresses_by_tid, out)

    assert written_count == 3
    out.seek(0)
    reader = list(csv.reader(out))
    
    assert reader[0] == ["Territory", "Address Count"]
    assert reader[1] == ["A2 - Bandon Trails", "1"]
    assert reader[2] == ["A12 - Crown Chase Apts", "2"]
    assert reader[3] == ["R5", "1"]
    assert len(reader) == 4

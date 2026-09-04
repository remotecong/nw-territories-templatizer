import io
import pytest
from src.territory_loader import load_territories, load_addresses, get_territory_filename

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

def test_get_territory_filename_with_area():
    terr = {"CategoryCode": "A", "Number": "12", "Area": "Crown Chase Apts"}
    assert get_territory_filename(terr) == "A12 - Crown Chase Apts.xlsx"

def test_get_territory_filename_sanitizes_slashes():
    terr = {"CategoryCode": "R", "Number": "10", "Area": "Berwick/Lakeside Villas"}
    assert get_territory_filename(terr) == "R10 - Berwick-Lakeside Villas.xlsx"

def test_get_territory_filename_without_area():
    terr1 = {"CategoryCode": "R", "Number": "5", "Area": ""}
    assert get_territory_filename(terr1) == "R5.xlsx"

    terr2 = {"CategoryCode": "R", "Number": "5", "Area": "None"}
    assert get_territory_filename(terr2) == "R5.xlsx"

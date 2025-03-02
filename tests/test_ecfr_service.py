import pytest
from app.retrieval.ecfr_service import ECFRService
from app.database.db import RegulationDAO
import sqlite3
import requests_mock

@pytest.fixture
def ecfr_service(tmp_path):
    """Fixture to create an ECFRService instance for testing.

    Args:
        tmp_path: Pytest fixture for a temporary directory.

    Returns:
        ECFRService: An instance of ECFRService.
    """
    db_file = tmp_path / "test_ecfr.db"  # Create a temporary database file.
    dao = RegulationDAO(db_file=str(db_file))  # Create a RegulationDAO instance.
    dao.create_tables()  # Create the necessary tables.
    return ECFRService(dao)  # Return an ECFRService instance.

def test_get_titles(ecfr_service: ECFRService):
    """Tests the get_titles method of ECFRService.

    Args:
        ecfr_service (ECFRService): The ECFRService fixture.
    """
    with requests_mock.Mocker() as m:  # Use requests_mock to mock API calls.
        m.get("https://www.ecfr.gov/api/versioner/v1/titles.json", json=[{"title": "Title1"}])  # Mock the API response.
        titles = ecfr_service.get_titles()  # Call the get_titles method.
        assert titles == [{"title": "Title1"}]  # Assert the response is as expected.

def test_get_versions(ecfr_service: ECFRService):
    """Tests the get_versions method of ECFRService.

    Args:
        ecfr_service (ECFRService): The ECFRService fixture.
    """
    with requests_mock.Mocker() as m:  # Use requests_mock to mock API calls.
        m.get("https://www.ecfr.gov/api/versioner/v1/versions/title-Title1.json", json=[{"version": "Section1"}])  # Mock the API response.
        versions = ecfr_service.get_versions("Title1")  # Call the get_versions method.
        assert versions == [{"version": "Section1"}]  # Assert the response is as expected.

def test_get_content(ecfr_service: ECFRService):
    """Tests the get_content method of ECFRService.

    Args:
        ecfr_service (ECFRService): The ECFRService fixture.
    """
    with requests_mock.Mocker() as m:  # Use requests_mock to mock API calls.
        m.get("https://www.ecfr.gov/api/versioner/v1/full/2023-01-01/title-Title1.xml", text="<xml>Content</xml>")  # Mock the API response.
        content = ecfr_service.get_content("Title1", "", "2023-01-01")  # Call the get_content method.
        assert content == "<xml>Content</xml>"  # Assert the response is as expected.

def test_calculate_hash(ecfr_service: ECFRService):
    """Tests the calculate_hash method of ECFRService.

    Args:
        ecfr_service (ECFRService): The ECFRService fixture.
    """
    hash_value = ecfr_service.calculate_hash("Content1")  # Call the calculate_hash method.
    assert isinstance(hash_value, str) and len(hash_value) > 0  # Assert the hash is a non-empty string.

def test_store_regulation(ecfr_service: ECFRService):
    """Tests the store_regulation method of ECFRService.

    Args:
        ecfr_service (ECFRService): The ECFRService fixture.
    """
    ecfr_service.store_regulation("Title1", "Section1", "2023-01-01", "Content1")  # Call the store_regulation method.
    hash_value = ecfr_service.regulation_dao.get_regulation_hash("Title1", "Section1")  # Retrieve the stored hash.
    assert hash_value is not None  # Assert the hash was stored.

def test_track_changes(ecfr_service: ECFRService):
    """Tests the track_changes method of ECFRService.

    Args:
        ecfr_service (ECFRService): The ECFRService fixture.
    """
    ecfr_service.store_regulation("Title1", "Section1", "2023-01-01", "Content1")  # Store an initial regulation.
    ecfr_service.track_changes("Title1", "Section1", "2023-01-02", "Content2")  # Track changes with new content.
    with sqlite3.connect(ecfr_service.regulation_dao.db_file) as conn:  # Connect to the database.
        cursor = conn.cursor()  # Create a cursor.
        cursor.execute("SELECT * FROM changes WHERE title = 'Title1'")  # Execute a query to retrieve changes.
        result = cursor.fetchone()  # Fetch the result.
        assert result is not None  # Assert a change was recorded.
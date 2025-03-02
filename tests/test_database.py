import pytest
import sqlite3

from app.database.db import RegulationDAO

@pytest.fixture
def regulation_dao(tmp_path):
    """Fixture to create a RegulationDAO instance for testing.

    Args:
        tmp_path: Pytest fixture for a temporary directory.

    Returns:
        RegulationDAO: An instance of RegulationDAO.
    """
    db_file = tmp_path / "test_ecfr.db"  # Create a temporary database file.
    dao = RegulationDAO(db_file=str(db_file))  # Create a RegulationDAO instance.
    dao.create_tables()  # Create the necessary tables.
    return dao  # Return the RegulationDAO instance.

def test_create_tables(regulation_dao: RegulationDAO):
    """Tests the create_tables method of RegulationDAO.

    Args:
        regulation_dao (RegulationDAO): The RegulationDAO fixture.
    """
    with sqlite3.connect(regulation_dao.db_file) as conn:  # Connect to the database.
        cursor = conn.cursor()  # Create a cursor object.
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")  # Execute a query to get table names.
        tables = [row[0] for row in cursor.fetchall()]  # Fetch the results.
        assert "regulations" in tables  # Assert the 'regulations' table exists.
        assert "changes" in tables  # Assert the 'changes' table exists.

def test_insert_regulation(regulation_dao: RegulationDAO):
    """Tests the insert_regulation method of RegulationDAO.

    Args:
        regulation_dao (RegulationDAO): The RegulationDAO fixture.
    """
    regulation_dao.insert_regulation("Title1", "Section1", "2023-01-01", "hash123", "Content1")  # Insert a regulation.
    with sqlite3.connect(regulation_dao.db_file) as conn:  # Connect to the database.
        cursor = conn.cursor()  # Create a cursor object.
        cursor.execute("SELECT * FROM regulations WHERE title = 'Title1'")  # Execute a query to retrieve the regulation.
        result = cursor.fetchone()  # Fetch the result.
        assert result is not None  # Assert the regulation was inserted.
        assert result[1] == "Title1"  # Assert the title is correct.

def test_get_regulation_hash(regulation_dao: RegulationDAO):
    """Tests the get_regulation_hash method of RegulationDAO.

    Args:
        regulation_dao (RegulationDAO): The RegulationDAO fixture.
    """
    regulation_dao.insert_regulation("Title2", "Section2", "2023-01-02", "hash456", "Content2")  # Insert a regulation.
    hash_value = regulation_dao.get_regulation_hash("Title2", "Section2")  # Get the hash of the regulation.
    assert hash_value == "hash456"  # Assert the hash is correct.

def test_insert_change(regulation_dao: RegulationDAO):
    """Tests the insert_change method of RegulationDAO.

    Args:
        regulation_dao (RegulationDAO): The RegulationDAO fixture.
    """
    regulation_dao.insert_change("Title3", "Section3", "2023-01-03", "old_hash", "new_hash")  # Insert a change record.
    with sqlite3.connect(regulation_dao.db_file) as conn:  # Connect to the database.
        cursor = conn.cursor()  # Create a cursor object.
        cursor.execute("SELECT * FROM changes WHERE title = 'Title3'")  # Execute a query to retrieve the change record.
        result = cursor.fetchone()  # Fetch the result.
        assert result is not None  # Assert the change record was inserted.
        assert result[1] == "Title3"  # Assert the title is correct.
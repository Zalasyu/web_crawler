import pytest
from app.retrieval.ecfr_service import ECFRService
from app.database.db import RegulationDAO
from app.analysis.ecfr_analyzer import eCFRAnalyzer
import requests_mock
from typing import List, Tuple, Dict, Any
import hashlib

@pytest.fixture
def integrated_services(tmp_path):
    """Fixture to create integrated service instances for testing.

    Args:
        tmp_path: Pytest fixture for a temporary directory.

    Returns:
        tuple: A tuple containing instances of RegulationDAO, ECFRService, and eCFRAnalyzer.
    """
    db_file = tmp_path / "test_ecfr.db"
    dao = RegulationDAO(db_file=str(db_file))
    dao.create_tables()
    ecfr_service = ECFRService(dao)
    analyzer = eCFRAnalyzer(dao)
    return dao, ecfr_service, analyzer
def test_full_integration(integrated_services):
    """Tests the full integration of data retrieval, storage, and analysis."""
    dao, ecfr_service, analyzer = integrated_services

    # Mock API responses
    with requests_mock.Mocker() as m:
        content1 = "<content><section>Old Section 1</section><section>Old Section 2</section></content>"
        content2 = "<content><section>New Section 1</section><section>Old Section 2</section><section>New Section 3</section></content>"
        m.get("https://www.ecfr.gov/api/versioner/v1/full/2023-01-01/title-12.xml", text=content1)
        m.get("https://www.ecfr.gov/api/versioner/v1/full/2023-01-02/title-12.xml", text=content2)
        m.get("https://www.ecfr.gov/api/versioner/v1/titles.json", json=[{"title": "12"}])
        m.get("https://www.ecfr.gov/api/versioner/v1/versions/title-12.json", json=[{"version": "v1"}])

        # 1. Test get_titles and get_versions
        titles = ecfr_service.get_titles()
        assert len(titles) == 1
        assert titles[0]["title"] == "12"

        versions = ecfr_service.get_versions("12")
        assert len(versions) == 1
        assert versions[0]["version"] == "v1"

        # 2. Fetch and store regulation content for the first date
        fetched_content1 = ecfr_service.get_content("12", "", "2023-01-01")
        assert fetched_content1 == content1
        ecfr_service.store_regulation("12", "v1", "2023-01-01", fetched_content1)

        # 3. Fetch and store regulation content for the second date
        fetched_content2 = ecfr_service.get_content("12", "", "2023-01-02")
        assert fetched_content2 == content2
        ecfr_service.store_regulation("12", "v1", "2023-01-02", fetched_content2)

        # 4. Track changes between the two dates
        ecfr_service.track_changes("12", "v1", "2023-01-02", fetched_content2)
        
        # 5. Analyze content (keywords)
        keywords = analyzer.keywords_analysis()
        assert isinstance(keywords, list)
        assert len(keywords) <= 10
        assert len(keywords) > 0
        assert all(isinstance(item, tuple) and len(item) == 2 for item in keywords)
        assert all(isinstance(item[0], str) and isinstance(item[1], int) for item in keywords)
        assert ("section", 5) in keywords  # "section" appears 5 times in text content

        # 6. Test historical changes over time
        changes = analyzer.historical_changes_over_time()
        assert isinstance(changes, list)
        assert len(changes) == 1  # One change recorded
        assert changes[0] == ("2023-01", 1)  # Change on 2023-01-02 groups to "2023-01"

        # 7. Test regulation complexity
        complexity = analyzer.regulation_complexity()
        assert isinstance(complexity, dict)
        assert "average_score" in complexity
        assert "individual_scores" in complexity
        assert isinstance(complexity["average_score"], float)
        assert isinstance(complexity["individual_scores"], list)
        assert len(complexity["individual_scores"]) == 2  # Two regulations
        assert all(isinstance(score, float) for score in complexity["individual_scores"])

        # 8. Test get_regulations
        regulations = dao.get_regulations()
        assert len(regulations) == 2
        assert regulations[0][1] == "12"
        assert regulations[0][2] == "v1"
        assert regulations[0][3] == "2023-01-01"
        assert regulations[0][4] == hashlib.sha256(content1.encode()).hexdigest()
        assert regulations[0][5] == content1
        assert regulations[1][3] == "2023-01-02"
        assert regulations[1][4] == hashlib.sha256(content2.encode()).hexdigest()
        assert regulations[1][5] == content2

def test_get_regulations(integrated_services):
    """Tests the get_regulations method of RegulationDAO."""
    dao, ecfr_service, _ = integrated_services

    # Insert regulations
    content1 = "Sample content one"
    content2 = "Different sample content"
    hash1 = hashlib.sha256(content1.encode()).hexdigest()
    hash2 = hashlib.sha256(content2.encode()).hexdigest()
    
    ecfr_service.store_regulation("Title1", "Version1", "2023-01-01", content1)
    ecfr_service.store_regulation("Title2", "Version2", "2023-01-02", content2)

    # Retrieve regulations
    regulations = dao.get_regulations()

    # Assertions
    assert len(regulations) == 2
    assert regulations[0][1] == "Title1"
    assert regulations[0][2] == "Version1"
    assert regulations[0][3] == "2023-01-01"
    assert regulations[0][4] == hash1
    assert regulations[0][5] == content1
    assert regulations[1][1] == "Title2"
    assert regulations[1][2] == "Version2"
    assert regulations[1][3] == "2023-01-02"
    assert regulations[1][4] == hash2
    assert regulations[1][5] == content2

def test_empty_database(integrated_services):
    """Tests behavior with an empty database."""
    dao, ecfr_service, analyzer = integrated_services

    # Test analysis methods with no data
    assert analyzer.keywords_analysis() == []
    assert analyzer.historical_changes_over_time() == []
    assert analyzer.regulation_complexity() == {"average_score": 0, "individual_scores": []}
    assert dao.get_regulations() == []

def test_track_changes_no_previous(integrated_services):
    """Tests track_changes when no previous regulation exists."""
    dao, ecfr_service, analyzer = integrated_services

    content = "Initial content"
    ecfr_service.track_changes("13", "v1", "2023-01-01", content)
    
    # No change should be recorded since there's no previous hash
    changes = analyzer.historical_changes_over_time()
    assert len(changes) == 0
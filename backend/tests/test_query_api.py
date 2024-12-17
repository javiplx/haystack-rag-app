from pathlib import Path
import sys

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from query.main import app, get_query_service
from common.models import SearchQuery, SearchResponse


client = TestClient(app)

@pytest.fixture
def mock_query_service():
    with patch("query.main.query_service") as mock:
        yield mock

# Test /search
def test_search(mock_query_service):
    app.dependency_overrides[get_query_service] = lambda: mock_query_service
    mock_query_service.search.return_value = "Mocked search result"

    response = client.post("/search", json={"query": "test query", "filters": None})
    mock_query_service.search.assert_called_once_with("test query", None)
    assert response.status_code == 200
    assert response.json() == {"results": ["Mocked search result"], "error": None}
    app.dependency_overrides.clear()

# Test /search with error
def test_search_error(mock_query_service):
    app.dependency_overrides[get_query_service] = lambda: mock_query_service
    mock_query_service.search.side_effect = Exception("Search error")

    response = client.post("/search", json={"query": "test query", "filters": None})
    assert response.status_code == 500
    assert "Search error" in response.json()["detail"]
    app.dependency_overrides.clear()

# Test /
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "documentation" in response.json()

# Test /health
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

from pathlib import Path
import sys

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
from unittest.mock import Mock, patch, mock_open
import os

from indexing.service import IndexingService, IndexingConfig
from query.service import QueryService, QueryConfig
from common.file_manager import FileManager
from common.document_store import initialize_document_store


@pytest.fixture
def document_store():
    return initialize_document_store()

@pytest.fixture
def indexing_service(document_store):
    with patch("indexing.service.create_indexing_pipeline"):
        service = IndexingService(document_store)
        service.file_manager = FileManager()
        yield service

def test_indexing_service_initialization(indexing_service):
    assert indexing_service.config is not None
    assert isinstance(indexing_service.config, IndexingConfig)
    assert indexing_service.pipeline is not None
    assert indexing_service.file_manager is not None

@patch('os.walk')
@patch('os.path.isfile')
def test_rescan_files_and_paths(mock_isfile, mock_walk, indexing_service):
    mock_walk.return_value = [
        ('/path/to/files', [], ['file1.txt', '.hidden_file', 'file2.pdf']),
        ('/path/to/files/uploads', [], ['file3.txt'])
    ]
    mock_isfile.return_value = True
    expected_files = ['file1.txt', 'file2.pdf', 'file3.txt']
    result = indexing_service.rescan_files_and_paths()
    assert result == expected_files
    assert indexing_service.file_manager.files == expected_files
    mock_walk.assert_called_once_with(indexing_service.file_manager.path_to_files)

@patch('os.path.exists')
@patch('builtins.open', new_callable=mock_open)
@patch('indexing.service.IndexingService.index_files')
def test_save_uploaded_file(mock_index_files, mock_open, mock_exists, indexing_service):
    mock_exists.return_value = False
    filename = "new_file.txt"
    contents = b"New content"
    expected_path = os.path.join(indexing_service.file_manager.path_to_uploads, filename)
    result = indexing_service.save_uploaded_file(filename, contents)
    assert result == expected_path
    mock_open.assert_called_once_with(expected_path, 'wb')
    mock_index_files.assert_called_once_with(expected_path)

@pytest.fixture
def query_service(document_store):
    with patch("query.service.create_query_pipeline"):
        yield QueryService(document_store)

def test_query_service_initialization(query_service):
    assert query_service.config is not None
    assert isinstance(query_service.config, QueryConfig)
    assert query_service.pipeline is not None

"""@patch("indexing.service.Pipeline.run")
def test_index_files(mock_run, indexing_service):
    indexing_service.file_manager.file_paths = ["/path/to/files/file1.txt", "/path/to/files/file2.txt"]
    indexing_service.index_files()
    assert mock_run.called, "Pipeline.run was not called"
    mock_run.assert_called_once()

@patch("query.service.Pipeline.run")
def test_search(mock_run, query_service):
    mock_run.return_value = {
        "answer_builder": {
            "answers": [Mock(data="Test reply")]
        }
    }
    result = query_service.search("test query")
    assert result == "Test reply"
    mock_run.assert_called_once()"""

# Add more tests ..

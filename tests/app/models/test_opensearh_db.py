"""
@file test_opensearh_db.py
@author naflashDev
@brief Unit tests for opensearh_db.py
@details Tests for OpenSearch integration logic (mocked, no real server required).
"""
import pytest
from unittest.mock import patch, MagicMock
from src.app.models import opensearh_db

def test_store_in_opensearch_success():
    '''
    @brief Should log success when storing data.
    '''
    data = {"text": "foo"}
    with patch("src.app.models.opensearh_db.OpenSearch") as mock_os, \
         patch("src.app.models.opensearh_db.logger") as mock_logger:
        mock_client = MagicMock()
        mock_client.index.return_value = {"result": "created"}
        mock_os.return_value = mock_client
        opensearh_db.store_in_opensearch(data, "localhost", 9200, "test-index")
        mock_logger.info.assert_any_call("Connecting to OpenSearch instance at localhost:9200.")
        mock_logger.info.assert_any_call("Document indexed successfully. Response: created")

def test_store_in_opensearsh_handles_exception():
    '''
    @brief Should log error if exception occurs.
    '''
    with patch("src.app.models.opensearh_db.OpenSearch", side_effect=Exception("fail")), \
         patch("src.app.models.opensearh_db.logger") as mock_logger:
        opensearh_db.store_in_opensearch({}, "localhost", 9200, "test-index")
        assert mock_logger.error.called

def test_text_exists_in_opensearch_true():
    '''
    @brief Should return True if document exists.
    '''
    with patch("src.app.models.opensearh_db.OpenSearch") as mock_os:
        mock_client = MagicMock()
        mock_client.search.return_value = {"hits": {"total": {"value": 1}}}
        mock_os.return_value = mock_client
        assert opensearh_db.text_exists_in_opensearch("foo", "localhost", 9200, "idx") is True

def test_text_exists_in_opensearch_false():
    '''
    @brief Should return False if document does not exist.
    '''
    with patch("src.app.models.opensearh_db.OpenSearch") as mock_os:
        mock_client = MagicMock()
        mock_client.search.return_value = {"hits": {"total": {"value": 0}}}
        mock_os.return_value = mock_client
        assert not opensearh_db.text_exists_in_opensearch("foo", "localhost", 9200, "idx")

def test_text_exists_in_opensearch_handles_exception():
    '''
    @brief Should return False if exception occurs.
    '''
    with patch("src.app.models.opensearh_db.OpenSearch", side_effect=Exception("fail")):
        assert not opensearh_db.text_exists_in_opensearch("foo", "localhost", 9200, "idx")

def test_ensure_index_exists_creates_index():
    '''
    @brief Should create index if not exists.
    '''
    with patch("src.app.models.opensearh_db.OpenSearch") as mock_os, \
         patch("src.app.models.opensearh_db.logger") as mock_logger:
        mock_client = MagicMock()
        mock_client.indices.exists.return_value = False
        mock_os.return_value = mock_client
        opensearh_db.ensure_index_exists("localhost", 9200, "idx")
        assert mock_client.indices.create.called
        assert mock_logger.info.called

def test_ensure_index_exists_handles_transport_error():
    '''
    @brief Should log error if TransportError occurs.
    '''
    with patch("src.app.models.opensearh_db.OpenSearch") as mock_os, \
         patch("src.app.models.opensearh_db.logger") as mock_logger:
        mock_client = MagicMock()
        mock_client.indices.exists.side_effect = Exception("fail")
        mock_os.return_value = mock_client
        opensearh_db.ensure_index_exists("localhost", 9200, "idx")
        assert mock_logger.error.called

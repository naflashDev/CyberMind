"""
@file test_models.py
@author naflashDev
@brief Tests unificados para los modelos de la capa app.models (OpenSearch y TinyTinyRSS PostgreSQL).
@details Incluye tests de integración y lógica de opensearh_db y ttrss_postgre_db, con mocks para dependencias externas.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.app.models import opensearh_db, ttrss_postgre_db
from app.models.pydantic import FeedCreateRequest, FeedResponse

# --- Tests opensearh_db ---
def test_store_in_opensearch_success():
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
    with patch("src.app.models.opensearh_db.OpenSearch", side_effect=Exception("fail")), \
         patch("src.app.models.opensearh_db.logger") as mock_logger:
        opensearh_db.store_in_opensearch({}, "localhost", 9200, "test-index")
        assert mock_logger.error.called

def test_text_exists_in_opensearch_true():
    with patch("src.app.models.opensearh_db.OpenSearch") as mock_os:
        mock_client = MagicMock()
        mock_client.search.return_value = {"hits": {"total": {"value": 1}}}
        mock_os.return_value = mock_client
        assert opensearh_db.text_exists_in_opensearch("foo", "localhost", 9200, "idx") is True

def test_text_exists_in_opensearch_false():
    with patch("src.app.models.opensearh_db.OpenSearch") as mock_os:
        mock_client = MagicMock()
        mock_client.search.return_value = {"hits": {"total": {"value": 0}}}
        mock_os.return_value = mock_client
        assert not opensearh_db.text_exists_in_opensearch("foo", "localhost", 9200, "idx")

def test_text_exists_in_opensearch_handles_exception():
    with patch("src.app.models.opensearh_db.OpenSearch", side_effect=Exception("fail")):
        assert not opensearh_db.text_exists_in_opensearch("foo", "localhost", 9200, "idx")

def test_ensure_index_exists_creates_index():
    with patch("src.app.models.opensearh_db.OpenSearch") as mock_os, \
         patch("src.app.models.opensearh_db.logger") as mock_logger:
        mock_client = MagicMock()
        mock_client.indices.exists.return_value = False
        mock_os.return_value = mock_client
        opensearh_db.ensure_index_exists("localhost", 9200, "idx")
        assert mock_client.indices.create.called
        assert mock_logger.info.called

def test_ensure_index_exists_handles_transport_error():
    with patch("src.app.models.opensearh_db.OpenSearch") as mock_os, \
         patch("src.app.models.opensearh_db.logger") as mock_logger:
        mock_client = MagicMock()
        mock_client.indices.exists.side_effect = Exception("fail")
        mock_os.return_value = mock_client
        opensearh_db.ensure_index_exists("localhost", 9200, "idx")
        assert mock_logger.error.called

# --- Tests ttrss_postgre_db ---
@pytest.mark.asyncio
async def test_get_feeds_from_db_returns_list():
    conn = AsyncMock()
    conn.fetch.return_value = [
        {"id": 1, "title": "t", "feed_url": "f", "site_url": "s", "owner_uid": 2, "cat_id": 3}
    ]
    feeds = await ttrss_postgre_db.get_feeds_from_db(conn, 1)
    assert isinstance(feeds, list)
    assert isinstance(feeds[0], FeedResponse)

@pytest.mark.asyncio
async def test_insert_feed_to_db_inserts_and_creates_category():
    conn = AsyncMock()
    conn.fetchrow.side_effect = [None, {"id": 1}]
    conn.fetchval.return_value = 1
    feed = FeedCreateRequest(title="t", feed_url="http://test.com/rss", site_url="http://test.com", owner_uid=2, cat_id=1)
    await ttrss_postgre_db.insert_feed_to_db(conn, feed)
    assert conn.execute.called

@pytest.mark.asyncio
async def test_insert_feed_to_db_raises_on_error():
    conn = AsyncMock()
    conn.fetchrow.side_effect = Exception("fail")
    feed = FeedCreateRequest(title="t", feed_url="http://test.com/rss", site_url="http://test.com", owner_uid=2, cat_id=1)
    with pytest.raises(Exception):
        await ttrss_postgre_db.insert_feed_to_db(conn, feed)

@pytest.mark.asyncio
async def test_get_entry_links_returns_links():
    conn = AsyncMock()
    conn.fetchrow.return_value = {"id": 1}
    conn.fetch.return_value = [{"link": "a"}, {"link": "b"}]
    links = await ttrss_postgre_db.get_entry_links(conn)
    assert links == ["a", "b"]

@pytest.mark.asyncio
async def test_mark_entry_as_viewed_executes():
    conn = AsyncMock()
    conn.fetchrow.return_value = {"id": 1}
    await ttrss_postgre_db.mark_entry_as_viewed(conn, "url")
    assert conn.execute.called

"""
@file test_ttrss_postgre_db.py
@author naflashDev
@brief Unit tests for ttrss_postgre_db.py
@details Tests for feed retrieval, insertion, and entry marking (mocks, no real DB).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.app.models import ttrss_postgre_db
from app.models.pydantic import FeedCreateRequest, FeedResponse

@pytest.mark.asyncio
async def test_get_feeds_from_db_returns_list():
    '''
    @brief Should return list of FeedResponse.
    '''
    conn = AsyncMock()
    conn.fetch.return_value = [
        {"id": 1, "title": "t", "feed_url": "f", "site_url": "s", "owner_uid": 2, "cat_id": 3}
    ]
    feeds = await ttrss_postgre_db.get_feeds_from_db(conn, 1)
    assert isinstance(feeds, list)
    assert isinstance(feeds[0], FeedResponse)

@pytest.mark.asyncio
async def test_insert_feed_to_db_inserts_and_creates_category():
    '''
    @brief Should insert feed and create category if needed.
    '''
    conn = AsyncMock()
    conn.fetchrow.side_effect = [None, {"id": 1}]
    conn.fetchval.return_value = 1
    # FeedCreateRequest requiere todos los campos obligatorios
    feed = FeedCreateRequest(title="t", feed_url="http://test.com/rss", site_url="http://test.com", owner_uid=2, cat_id=1)
    await ttrss_postgre_db.insert_feed_to_db(conn, feed)
    assert conn.execute.called

@pytest.mark.asyncio
async def test_insert_feed_to_db_raises_on_error():
    '''
    @brief Should raise HTTPException on error.
    '''
    conn = AsyncMock()
    conn.fetchrow.side_effect = Exception("fail")
    # FeedCreateRequest requiere todos los campos obligatorios
    feed = FeedCreateRequest(title="t", feed_url="http://test.com/rss", site_url="http://test.com", owner_uid=2, cat_id=1)
    with pytest.raises(Exception):
        await ttrss_postgre_db.insert_feed_to_db(conn, feed)

@pytest.mark.asyncio
async def test_get_entry_links_returns_links():
    '''
    @brief Should return list of links for admin.
    '''
    conn = AsyncMock()
    conn.fetchrow.return_value = {"id": 1}
    conn.fetch.return_value = [{"link": "a"}, {"link": "b"}]
    links = await ttrss_postgre_db.get_entry_links(conn)
    assert links == ["a", "b"]

@pytest.mark.asyncio
async def test_mark_entry_as_viewed_executes():
    '''
    @brief Should execute update for admin.
    '''
    conn = AsyncMock()
    conn.fetchrow.return_value = {"id": 1}
    await ttrss_postgre_db.mark_entry_as_viewed(conn, "url")
    assert conn.execute.called

"""
@file ttrss_postgre_db.py
@author naflashDev
@brief Operations for RSS feed entries in Tiny Tiny RSS using PostgreSQL.
@details Provides data models and database functions to retrieve and insert RSS feeds, ensuring data integrity and supporting API endpoints.
"""

from typing import List
from asyncpg import Connection
from fastapi import HTTPException

from app.models.pydantic import FeedCreateRequest, FeedResponse


async def get_feeds_from_db(
    conn: Connection,
    limit: int
) -> List[FeedResponse]:
    '''
    @brief Retrieve a limited number of feed records from the ttrss_feeds table.

    Fetches up to the specified limit of feed records from the database and returns them as FeedResponse objects.

    @param conn Active database connection (asyncpg.Connection).
    @param limit Maximum number of feeds to retrieve (int).
    @return List of feeds as FeedResponse objects (List[FeedResponse]).
    '''
    rows = await conn.fetch("SELECT * FROM ttrss_feeds LIMIT $1", limit)
    feeds = []
    for row in rows:
        cat_id = row['cat_id'] if isinstance(row['cat_id'], int) else 0
        feed = FeedResponse(
            id=row['id'],
            title=row['title'],
            feed_url=row['feed_url'],
            site_url=row['site_url'],
            owner_uid=row['owner_uid'],
            cat_id=cat_id
        )
        feeds.append(feed)
    return feeds


async def insert_feed_to_db(
    conn: Connection,
    feed: FeedCreateRequest
) -> None:
    '''
    @brief Insert a new feed into the ttrss_feeds table. Ensures the feed category 'Sin clasificar' exists before insertion.

    Inserts a new feed record into the database, creating the default category if needed.

    @param conn Active database connection (asyncpg.Connection).
    @param feed Data of the feed to insert (FeedCreateRequest).
    @return None. Raises HTTPException if insertion fails or constraints are violated.
    '''
    try:
        category = await conn.fetchrow("""
            SELECT id FROM ttrss_feed_categories
            WHERE title = 'Sin clasificar'
        """)

        if category:
            cat_id = category['id']
        else:
            await conn.execute("""
                INSERT INTO ttrss_feed_categories (title, owner_uid)
                VALUES ('Sin clasificar', $1)
            """, feed.owner_uid)

            cat_id = await conn.fetchval("""
                SELECT id FROM ttrss_feed_categories
                WHERE title = 'Sin clasificar'
            """)

        await conn.execute("""
            INSERT INTO ttrss_feeds (
                title, feed_url, site_url, owner_uid, cat_id
            ) VALUES ($1, $2, $3, $4, $5)
        """, feed.title, str(feed.feed_url),
             feed.site_url, feed.owner_uid, cat_id)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al insertar el feed en la base de datos: {str(e)}"
        )


async def get_entry_links(conn: Connection) -> List[str]:
    '''
    @brief Retrieve entry links that are unread (unread = true) for a specific user.

    Fetches all entry URLs that have not yet been viewed by the user 'admin'.

    @param conn Active database connection (asyncpg.Connection).
    @return List of URLs not yet viewed by the user (List[str]).
    '''
    login = "admin"

    row = await conn.fetchrow(
        "SELECT id FROM ttrss_users WHERE login = $1",
        login
    )
    if not row:
        raise ValueError("User not found")
    owner_uid = row["id"]
    rows = await conn.fetch(
        """
        SELECT e.link
        FROM ttrss_entries e
        JOIN ttrss_user_entries u ON u.ref_id = e.id
        WHERE e.link IS NOT NULL
          AND u.owner_uid = $1
          AND u.unread = TRUE
        """,
        owner_uid
    )
    return [row["link"] for row in rows]


async def mark_entry_as_viewed(conn: Connection, url: str) -> None:
    '''
    @brief Mark an entry as viewed (unread = false) for the user with login "admin".

    Updates the database to mark the entry with the given URL as viewed for the user 'admin'.

    @param conn Active database connection (asyncpg.Connection).
    @param url URL to mark as viewed (str).
    @return None.
    '''
    login = "admin"

    row = await conn.fetchrow(
        "SELECT id FROM ttrss_users WHERE login = $1",
        login
    )
    if not row:
        raise ValueError("User not found")
    owner_uid = row["id"]

    await conn.execute(
        """
        UPDATE ttrss_user_entries u
        SET unread = FALSE
        FROM ttrss_entries e
        WHERE u.ref_id = e.id
          AND u.owner_uid = $1
          AND e.link = $2
        """,
        owner_uid,
        url
    )



# @ Author: RootAnto
# @ Project: Cebolla
# @ Create Time: 2025-05-05 10:30:50
# @ Description:
# This module defines Pydantic data models used throughout the application
# for validating, processing, and representing RSS feed data.
# It includes models for creating and retrieving feed metadata from the database,
# handling lists of feed URLs, and processing Google Alert RSS feed entries and feeds.
# These models ensure data integrity and provide clear structure for API requests and responses.


from typing import List, Optional
from pydantic import BaseModel, HttpUrl

class FeedCreateRequest(BaseModel):
    """
    Pydantic model for validating input data when creating a new RSS feed entry.

    Attributes:
        feed_url (HttpUrl): The URL of the RSS feed.
        title (str): The title of the feed.
        site_url (str): The URL of the website hosting the feed.
        owner_uid (int): The user ID of the feed owner.
        cat_id (int): The category ID associated with the feed.
    """
    feed_url: HttpUrl
    title: str
    site_url: str
    owner_uid: int
    cat_id: int


class FeedResponse(BaseModel):
    """
    Pydantic model representing RSS feed data retrieved from the database.

    Attributes:
        id (int): Unique identifier of the feed in the database.
        title (str): Title of the feed.
        feed_url (str): URL of the RSS feed.
        site_url (str): URL of the website hosting the feed.
        owner_uid (int): User ID of the feed owner.
        cat_id (int): Category ID of the feed.
    """
    id: int
    title: str
    feed_url: str
    site_url: str
    owner_uid: int
    cat_id: int

class FeedUrlList(BaseModel):
    """
    Pydantic model for validating a list of feed URLs.

    Attributes:
        urls (List[HttpUrl]): A list of RSS feed URLs.
    """
    urls: List[HttpUrl]


class GoogleAlertEntry(BaseModel):
    """
    Pydantic model representing a single entry/item in a Google Alert RSS feed.

    Attributes:
        id (str): Unique identifier of the entry.
        title (str): Title of the entry.
        link (HttpUrl): URL link associated with the entry.
        published (Optional[str]): Publication date/time of the entry
        (optional).
        updated (Optional[str]): Last updated date/time of the
        entry (optional).
        content (Optional[str]): Content snippet or summary of the
        entry (optional).
    """
    id: str
    title: str
    link: HttpUrl
    published: Optional[str]
    updated: Optional[str]
    content: Optional[str]


class GoogleAlertFeed(BaseModel):
    """
    Pydantic model representing a Google Alert RSS feed.

    Attributes:
        id (str): Unique identifier of the feed.
        title (str): Title of the feed.
        link (HttpUrl): URL link of the feed.
        updated (Optional[str]): Last updated date/time of the feed (optional).
        entries (List[GoogleAlertEntry]): List of entries/items in the feed.
    """
    id: str
    title: str
    link: HttpUrl
    updated: Optional[str]
    entries: List[GoogleAlertEntry]

class FeedUrlRequest(BaseModel):
    """
    Pydantic model for a single feed URL request.

    Attributes:
        feed_url (HttpUrl): The RSS feed URL being requested or submitted.
    """
    feed_url: HttpUrl


class FeedUrlRequest(BaseModel):
    """
    Pydantic model representing a request containing a single RSS feed URL.

    Attributes:
        feed_url (HttpUrl): The RSS feed URL to be processed or saved.
    """
    feed_url: HttpUrl


class SaveLinkResponse(BaseModel):
    """
    Pydantic model representing the response after saving a feed link.

    Attributes:
        message (str): A confirmation message indicating the result.
        link (HttpUrl): The RSS feed URL that was saved.
        title (str): The title of the feed corresponding to the URL.
    """
    message: str
    link: HttpUrl
    title: str

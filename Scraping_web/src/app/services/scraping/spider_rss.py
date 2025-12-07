# @ Author: naflashDev
# @ Create Time: 2025-05-05 12:17:59
# @ Project: Cebolla
# @ Description:
# This module implements a dynamic Scrapy spider designed to extract RSS and
# Atom feed
# URLs from a given list of websites. It leverages the feedparser library to
# parse feed metadata such as titles and site URLs, and stores valid feeds
# asynchronously into a PostgreSQL database using asyncpg.
#
# Key functionalities include:
# - Reading URLs from a local file to scan for RSS feeds.
# - Dynamically creating and running a Scrapy spider that detects RSS/Atom/XML
# feeds via <link> tags.
# - Running the spider asynchronously with multiprocessing to handle multiple
# URLs concurrently.
# - Parsing each discovered feed to extract essential metadata.
# - Inserting extracted feed data into the PostgreSQL database with proper
# error handling.
# - Configurable crawling settings with retry mechanisms and polite crawling
# delays.
#
# This module supports scalable and efficient feed discovery and ingestion for
# the Cebolla project.


import feedparser
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import Spider
from app.models.ttrss_postgre_db import insert_feed_to_db, FeedCreateRequest
from multiprocessing import Process, Queue
from scrapy.utils.log import configure_logging
from typing import List, Type
from loguru import logger

def read_urls_from_file(file_path) -> List[str] | List:
    """
    Reads a list of URLs from a text file.

    This function attempts to open the specified file and read each line,
    stripping whitespace and ignoring empty lines. It returns a list of
    cleaned URL strings.

    Args:
        file_path (str): The path to the text file containing URLs, one per
        line.

    Returns:
        List[str]: A list of non-empty, stripped URL strings. If an error
        occurs, an empty list is returned and the error is printed.
    """
    try:
        with open(file_path, "r") as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return []

def create_rss_spider(urls, results)-> Type[Spider]:
    """
    Dynamically creates a Scrapy spider class to extract RSS/Atom/XML feed
    links from a list of URLs.

    This function defines and returns a custom Scrapy Spider class that will:
    - Visit each URL in the provided `urls` list.
    - Inspect <link> tags in the HTML response.
    - Identify links with RSS, Atom, or XML MIME types.
    - Normalize and collect unique feed URLs into the shared `results` list.

    Args:
        urls (List[str]): A list of web page URLs to scan for RSS feeds.
        results (List[str]): A mutable list to which discovered feed URLs will
        be appended.

    Returns:
        Type[Spider]: A Scrapy spider class configured to extract feed URLs.
    """
    class RSSSpider(Spider):
        name = "rss_spider"
        start_urls = urls

        def parse(self, response):
            for link in response.css("link"):
                href = link.attrib.get("href", "")
                type_ = link.attrib.get("type", "")
                if "rss" in type_ or "atom" in type_ or "application/xml" in type_:
                    full_url = response.urljoin(href)
                    if full_url not in results:
                        results.append(full_url)
                        logger.info(f"RSS found: {full_url}")
    return RSSSpider

def run_rss_spider(urls, queue) -> None:
    """
    Runs a Scrapy spider to discover RSS or Atom feed URLs from a list of
    websites.

    This function configures logging, creates a spider using
    `create_rss_spider`, and runs it in a Scrapy `CrawlerProces`.
    Once crawling is complete, the discovered RSS feed URLs are pushed into a
    multiprocessing queue for further use.

    Args:
        urls (List[str]): A list of web page URLs to scan for RSS/Atom feed
        links. queue (Queue): A multiprocessing queue where the discovered
        feed URLs will be stored.
    """

    configure_logging({'LOG_LEVEL': 'ERROR'})
    results = []
    spider = create_rss_spider(urls, results)

    process = CrawlerProcess(settings={
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "DOWNLOAD_DELAY": 2.0,
        "AUTOTHROTTLE_ENABLED": True,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 5,
        "RETRY_HTTP_CODES": [429, 500, 502, 503, 504],
        "LOG_ENABLED": False
    })

    process.crawl(spider)
    process.start()
    queue.put(results)

async def extract_rss_and_save(pool, file_path) -> None:
    """
    Extracts RSS/Atom feed URLs from a list of websites and stores valid feeds
    in a PostgreSQL database.

    This function:
    - Reads website URLs from a local file.
    - Uses a multiprocessing Scrapy spider to discover RSS/Atom feeds from
      those websites.
    - Parses each discovered feed using `feedparser`.
    - Extracts metadata such as the title and site URL.
    - Constructs a `FeedCreateRequest` and inserts the feed into the database
    via `insert_feed_to_db`.

    Args:
        pool: An `asyncpg.pool.Pool` object used to acquire database connections.
        file_path (str): The file path containing a list of website URLs to process.

    Returns:
        Coroutine[Any, Any, None]: An asynchronous coroutine that performs the
        feed extraction and saving process.
    """
    urls = read_urls_from_file(file_path)
    if not urls:
        print("No URLs found to process.")
        return

    queue = Queue()
    p = Process(target=run_rss_spider, args=(urls, queue))
    p.start()
    p.join()

    results = queue.get()

    async with pool.acquire() as conn:
        for feed_url in results:
            try:
                feed = feedparser.parse(feed_url)
                if not feed.entries:
                    logger.warning(f"⚠️  No entries found in {feed_url}")
                    continue

                title = feed.feed.get("title", "Untitled")
                site_url = feed.feed.get("link", "No site")

                feed_data = FeedCreateRequest(
                    title=title,
                    feed_url=feed_url,
                    site_url=site_url,
                    owner_uid=1,
                    cat_id=0
                )

                await insert_feed_to_db(conn, feed_data)
                logger.info(f"✅ Feed inserted: {feed_url}")

            except Exception as e:
                logger.error(f"❌ Error processing {feed_url}: {e}")

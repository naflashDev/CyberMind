"""
@file spider_rss.py
@author naflashDev
@brief Dynamic Scrapy spider for extracting RSS/Atom feeds.
@details Implements a dynamic Scrapy spider to extract RSS and Atom feed URLs from websites, parse metadata, and store results asynchronously in PostgreSQL. Supports concurrent crawling and error handling.
"""



import feedparser
import asyncio
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import Spider
from app.models.ttrss_postgre_db import insert_feed_to_db, FeedCreateRequest
from multiprocessing import Process, Queue
from scrapy.utils.log import configure_logging
from typing import List, Type
from loguru import logger

def read_urls_from_file(file_path) -> List[str] | List:
    '''
    @brief Reads a list of URLs from a text file.

    Attempts to open the specified file and read each line, stripping whitespace and ignoring empty lines. Returns a list of cleaned URL strings.

    @param file_path The path to the text file containing URLs, one per line (str).
    @return A list of non-empty, stripped URL strings. If an error occurs, an empty list is returned and the error is logged (List[str] | List).
    '''
    try:
        with open(file_path, "r") as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return []

def create_rss_spider(urls, results)-> Type[Spider]:
    '''
    @brief Dynamically creates a Scrapy spider class to extract RSS/Atom/XML feed links from a list of URLs.

    Defines and returns a custom Scrapy Spider class that will visit each URL in the provided `urls` list, inspect <link> tags in the HTML response, identify links with RSS, Atom, or XML MIME types, and collect unique feed URLs into the shared `results` list.

    @param urls List of web page URLs to scan for RSS feeds (List[str]).
    @param results Mutable list to which discovered feed URLs will be appended (List[str]).
    @return A Scrapy spider class configured to extract feed URLs (Type[Spider]).
    '''
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
    '''
    @brief Runs a Scrapy spider to discover RSS or Atom feed URLs from a list of websites.

    Configures logging, creates a spider using `create_rss_spider`, and runs it in a Scrapy `CrawlerProcess`. Once crawling is complete, the discovered RSS feed URLs are pushed into a multiprocessing queue for further use.

    @param urls List of web page URLs to scan for RSS/Atom feed links (List[str]).
    @param queue Multiprocessing queue where the discovered feed URLs will be stored (Queue).
    @return None.
    '''

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
    '''
    @brief Extracts RSS/Atom feed URLs from a list of websites and stores valid feeds in a PostgreSQL database.

    Reads website URLs from a local file, uses a multiprocessing Scrapy spider to discover RSS/Atom feeds, parses each discovered feed using `feedparser`, extracts metadata, constructs a `FeedCreateRequest` and inserts the feed into the database via `insert_feed_to_db`.

    @param pool asyncpg.pool.Pool object used to acquire database connections.
    @param file_path File path containing a list of website URLs to process (str).
    @return None. Performs the feed extraction and saving process asynchronously.
    '''
    urls = read_urls_from_file(file_path)
    if not urls:
        logger.info("No URLs found to process.")
        return

    # Run the blocking multiprocessing spider in a thread to avoid
    # blocking the asyncio event loop. The helper runs the Process,
    # waits for it to finish and returns the results from the queue.
    def _run_process_and_get_results(urls_list):
        q = Queue()
        proc = Process(target=run_rss_spider, args=(urls_list, q))
        proc.start()
        proc.join()
        try:
            return q.get()
        except Exception:
            return []

    results = await asyncio.to_thread(_run_process_and_get_results, urls)

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

# @ Author: naflashDev
# @ Create Time: 2025-05-5 12:17:59
# @ Project: Cebolla
# @ Description: This module defines the logic for dynamically scraping web
# pages using Scrapy.
# It includes a factory function that builds a custom Spider class on the fly,
# based on a list of input URLs. The spider extracts key structural content
# such as titles, headers (h1-h6), and paragraph text.
#
# The module also manages the execution of the spider:
# - Once via `run_dynamic_spider()` with a static list of URLs
# - Continuously via `run_dynamic_spider_from_db()`, which pulls fresh URLs
#   from a PostgreSQL database using an asyncpg connection pool.
#
# Extracted data is saved locally in JSON format for further processing or a
# nalysis.

from scrapy.spiders import Spider
from scrapy.crawler import CrawlerProcess
from app.models.ttrss_postgre_db import get_entry_links,mark_entry_as_viewed
from app.utils.utils import get_connection_parameters,create_config_file
from app.models.opensearh_db import store_in_opensearch
from multiprocessing import Process
import asyncio
import logging
from scrapy.utils.log import configure_logging
from typing import Type, Coroutine, Any
from loguru import logger

# Lock file name to manage concurrent write access to JSON output
LOCKFILE = "result.json.lock"
# Output JSON file name
OUTPUT_FILE = "./outputs/result.json"

CYBERSECURITY_KEYWORDS = [
    "ciberseguridad", "cybersecurity", "malware", "ransomware", "phishing",
    "hacking", "vulnerabilidad", "vulnerability", "ataque", "ataques", "exploit",
    "seguridad informática", "seguridad digital", "threat", "threats", "spyware",
    "breach", "data leak", "cyber attack", "ddos","firewall", "intrusion",
    "encryption", "cyber defense", "cyber threat", "zero-day", "botnet",
    "cyber espionage", "social engineering", "cyber resilience", "incident response",
    "penetration testing", "red team", "blue team", "cyber hygiene", "cyber risk",
    "cyber war", "advanced persistent threat", "apt", "cyber intelligence", "siem","sql injection", "xss"
    , "cross-site scripting"
]

def write_json_array_with_lock(data, filename=OUTPUT_FILE, lockfile=LOCKFILE):
    """
    Writes data into a single JSON array file with each JSON object on one line.
    Uses file-based locking to prevent concurrent writes.

    If file doesn't exist, creates it with an array containing the first data object.
    If file exists, inserts the new data before the closing ] with a comma separator.

    Args:
        data (dict): The scraped data to write.
        filename (str): Path to the JSON file.
        lockfile (str): Path to the lock file.
    """
    import os
    import time
    import json

    while os.path.exists(lockfile):
        time.sleep(0.1)

    with open(lockfile, "w") as f_lock:
        f_lock.write("locked")

    try:
        if not os.path.exists(filename):
            with open(filename, "w", encoding="utf8") as f:
                f.write("[\n")
                json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
                f.write("\n]")
        else:
            with open(filename, "r+", encoding="utf8") as f:
                f.seek(0, os.SEEK_END)
                pos = f.tell() - 1

                while pos > 0:
                    f.seek(pos)
                    char = f.read(1)
                    if char == ']':
                        break
                    pos -= 1

                if pos <= 0:
                    # Malformed file fallback
                    f.seek(0, os.SEEK_END)
                    f.write(",\n")
                    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
                    f.write("\n]")
                else:
                    f.seek(pos)
                    f.truncate()
                    f.write(",\n")
                    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
                    f.write("\n]")
    finally:
        os.remove(lockfile)


def create_dynamic_spider(urls,parameters) -> Type[Spider]:
    """
    Creates a dynamic Scrapy spider class for extracting content from a list
    of URLs.

    This function defines and returns a custom Scrapy Spider class that
    processes each URL by extracting:
      - The page title
      - All text content inside header tags (h1–h6) and paragraph tags (p)
      - Writes scraped data into a JSON file with manual file locking
      - Marks the URL as scraped in the database opening and closing
        a connection for each URL.

    Args:
        urls (list[str]): A list of URLs to crawl.
        db_config (dict): Configuration dict for asyncpg connection parameters.

    Returns:
        Type[Spider]: A dynamically created Scrapy Spider class.
    """

    class DynamicSpider(Spider):
        name = "dynamic_spider"
        start_urls = urls

        def parse(self, response):
            data = {
                "url": response.url,
                "title": response.css("title::text").get(default="Untitled")
            }
            full_text = data["title"].lower()
            for tag in ["h1", "h2", "h3", "h4", "h5", "h6", "p"]:
                elements = response.css(f"{tag}::text").getall()
                clean_elements = [e.strip() for e in elements if e.strip()]
                data[tag] = clean_elements
                full_text += " " + " ".join(clean_elements).lower()

            # Check if any cybersecurity keyword is in the text
            if any(keyword in full_text for keyword in CYBERSECURITY_KEYWORDS):
                write_json_array_with_lock(data)
                store_in_opensearch(data,parameters[0],parameters[1],"scrapy_documents")
                logger.info(f"URL relacionada con ciberseguridad: {response.url}")
                yield data
            else:
                logger.info(f"Descartada (no relevante): {response.url}")
            logger.info(f"URL: {response.url} scrapeada")


            yield data


    return DynamicSpider


def run_dynamic_spider(urls,parameters) -> None:
    """
    Runs a dynamically generated Scrapy spider to scrape content from a list
    of URLs.

    This function sets up logging and Scrapy settings, creates a dynamic
    spider using the provided URLs, and launches a Scrapy crawler process with
    that spider.

    Features configured:
        - Disables default Scrapy logging to avoid console clutter.
        - Sets a realistic user-agent string for better scraping reliability.
        - Enables a download delay and auto-throttling to reduce server load.
        - Configures retries for transient HTTP errors (e.g., 429, 503).
        - Writes scraped data into a local JSON file ("result.json") using
          manual file locking to avoid concurrency problems.

    Args:
        urls (list[str]): A list of web URLs to be scraped.
        parameters (tuple): A tuple of parameters to connect to the OpenSearch database.
    """
    configure_logging(install_root_handler=False)
    logging.getLogger('scrapy').propagate = False
    logging.getLogger().setLevel(logging.CRITICAL)

    DynamicSpider = create_dynamic_spider(urls,parameters)

    process = CrawlerProcess(settings={
        "LOG_ENABLED": False,
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        ),
        "DOWNLOAD_DELAY": 2.0,  # 2 seconds between requests
        "AUTOTHROTTLE_ENABLED": True,  # Adjusts delay based on load
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 5,  # Retry failed requests up to 5 times
        "RETRY_HTTP_CODES": [429, 500, 502, 503, 504],
        # No FEEDS or ITEM_PIPELINES used here because writing is manual
    })

    process.crawl(DynamicSpider)
    process.start()
    logger.info("Urls scrapeadas")


async def run_dynamic_spider_from_db(pool) -> Coroutine[Any, Any, None]:
    """
    Creates and returns an asynchronous function that continuously runs the
    dynamic Scrapy spider.

    This function:
    - Periodically acquires URLs from a PostgreSQL connection pool.
    - Spawns a separate process to run a Scrapy spider using those URLs.
    - Waits 60 seconds before repeating the process.

    Args:
        pool (asyncpg.pool.Pool): The asyncpg connection pool for database
        access.

    Returns:
        None.
    """
    number=0
    while True:
        logger.info(f"Scraped lap {number}")
        async with pool.acquire() as conn:
            urls = await get_entry_links(conn)
            if not urls:
                logger.info("No URLs found to process.")
            else:
                logger.info(f"{len(urls)} found to scraped")
                # Obtain the parameters for the OpenSearch database
                parameters: tuple = (
                    'localhost',
                    9200
                )
                file_name: str = 'cfg.ini'
                file_content: list[str] = [
                    '# Configuration file.\n',
                    '# This file contains the parameters for connecting to the opensearch database server.\n',
                    '# ONLY one uncommented line is allowed.\n',
                    '# The valid line format is: server_ip,server_port\n',
                    f'{parameters[0]};{parameters[1]}\n'
                ]

                # Get the connection parameters or assign default ones
                retorno_otros = get_connection_parameters(file_name)
                logger.info(retorno_otros[1])

                if retorno_otros[0] != 0:
                    logger.info('Recreating configuration file...')
                    retorno_otros = create_config_file(file_name, file_content)
                    logger.info(retorno_otros[1])
                    # If the file had to be recreated, default values will be used

                    if retorno_otros[0] != 0:
                        logger.error('Configuration file missing. Execution cannot continue without a configuration file.')
                        return
                else:
                    parameters = retorno_otros[2]  # Get parameters read from the config file

                for url in urls:
                    await mark_entry_as_viewed(conn, url)
                urls_def=[]
                urls_def = urls_def + [url for url in urls if url not in urls_def]
                # Run the spider in a separate process (avoids signal issues)
                p = Process(target=run_dynamic_spider, args=(urls,parameters))
                p.start()

        logger.info("Waiting for next run...")
        await asyncio.sleep(93600)
        number+=1
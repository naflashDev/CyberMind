import os
from dotenv import load_dotenv
load_dotenv()
"""
@file spider_factory.py
@brief Dynamic Scrapy spider factory and runner.
@details Creates a dynamic Scrapy `Spider` class from a list of URLs and
provides helpers to run the spider either once (`run_dynamic_spider`) or
continuously by polling a PostgreSQL database (`run_dynamic_spider_from_db`).
The module writes results to a local JSON file and registers spawned
processes so the application UI can terminate them via a stop event.
@author naflashDev
"""
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
    '''
    @brief Writes data into a single JSON array file with each JSON object on one line, using file-based locking.

    If the file does not exist, creates it with an array containing the first data object. If the file exists, inserts the new data before the closing bracket with a comma separator.

    @param data The scraped data to write (dict).
    @param filename Path to the JSON file (str).
    @param lockfile Path to the lock file (str).
    @return None.
    '''
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
    '''
    @brief Creates a dynamic Scrapy spider class for extracting content from a list of URLs.

    Defines and returns a custom Scrapy Spider class that processes each URL, extracts content, writes data to a JSON file, and marks the URL as scraped in the database.

    @param urls List of URLs to crawl (list[str]).
    @param parameters Tuple of parameters for OpenSearch connection (tuple).
    @return A dynamically created Scrapy Spider class (Type[Spider]).
    '''

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
    '''
    @brief Runs a dynamically generated Scrapy spider to scrape content from a list of URLs.

    Sets up logging and Scrapy settings, creates a dynamic spider using the provided URLs, and launches a Scrapy crawler process with that spider.

    @param urls List of web URLs to be scraped (list[str]).
    @param parameters Tuple of parameters to connect to the OpenSearch database (tuple).
    @return None.
    '''
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


async def run_dynamic_spider_from_db(pool, stop_event=None, register_process=None) -> Coroutine[Any, Any, None]:
    '''
    @brief Continuously runs the dynamic Scrapy spider, polling URLs from the database and launching scraping processes.

    Periodically acquires URLs from a PostgreSQL connection pool, spawns a separate process to run a Scrapy spider, and waits before repeating the process. Responds to stop events for graceful shutdown.

    @param pool The asyncpg connection pool for database access.
    @param stop_event Optional event to signal stopping the loop.
    @param register_process Optional callback to register the spawned process.
    @return None (asynchronous coroutine).
    '''
    number = 0
    while True:
        # Respect immediate stop requests
        if stop_event is not None and getattr(stop_event, 'is_set', lambda: False)():
            logger.info("Dynamic spider stop_event detected; exiting run loop.")
            break

        # Ensure we have a valid asyncpg pool; try to create one on-demand
        if pool is None:
            try:
                import asyncpg
                pool = await asyncpg.create_pool(
                    user=os.getenv("POSTGRES_USER"),
                    password=os.getenv("POSTGRES_PASSWORD"),
                    database=os.getenv("POSTGRES_DB"),
                    host=os.getenv("POSTGRES_HOST"),
                    port=int(os.getenv("POSTGRES_PORT", 5432)),
                    min_size=1,
                    max_size=5,
                )
                logger.info("Created PostgreSQL pool on-demand in spider_factory.")
            except Exception as e:
                logger.warning(f"DB pool not available; will retry later: {e}")
                # back off briefly but remain responsive to stop_event
                await asyncio.sleep(5)
                continue

        try:
            async with pool.acquire() as conn:
                urls = await get_entry_links(conn)

                # Process retrieved URLs (if any) while connection still held
                if not urls:
                    # No work — use debug level to avoid console spam
                    logger.debug("No URLs found to process.")
                else:
                    # Only increment and log when there is actual work
                    number += 1
                    logger.info(f"Scraped lap {number}: {len(urls)} URLs to process")
                    # Obtain the parameters for the OpenSearch database
                    # Default parameters for OpenSearch connection
                    parameters: tuple = (
                        'localhost',
                        9200
                    )
                    file_name: str = 'cfg.ini'
                    file_content: list[str] = [
                        '# Configuration file.\n',
                        '# This file contains the parameters for connecting to the opensearch database server.\n',
                        '# ONLY one uncommented line is allowed.\n',
                        '# The valid line format is: server_ip=valor;server_port=valor\n',
                        'server_ip=localhost;server_port=9200\n'
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
                            # Intentar leer de nuevo tras crear el archivo
                            retorno_otros = get_connection_parameters(file_name)
                            logger.info(retorno_otros[1])
                            if retorno_otros[0] == 0:
                                parameters = retorno_otros[2]
                    else:
                        parameters = retorno_otros[2]  # Get parameters read from the config file

                    for url in urls:
                        await mark_entry_as_viewed(conn, url)
                    urls_def = []
                    urls_def = urls_def + [url for url in urls if url not in urls_def]
                    # Before launching, check stop_event
                    if stop_event is not None and getattr(stop_event, 'is_set', lambda: False)():
                        logger.info("Dynamic spider stop_event set; aborting launch.")
                        break
                    # Run the spider in a separate process (avoids signal issues)
                    p = Process(target=run_dynamic_spider, args=(urls, parameters))
                    p.start()
                    # allow caller to keep reference to process so UI can terminate it
                    if callable(register_process):
                        try:
                            register_process(p)
                        except Exception:
                            pass

                    # If stop_event set while process running, try to terminate process
                    if stop_event is not None and getattr(stop_event, 'is_set', lambda: False)():
                        try:
                            p.terminate()
                            logger.info("Dynamic spider process terminated due to stop_event.")
                        except Exception:
                            logger.exception("Error terminating dynamic spider process")
        except Exception as e:
            logger.exception(f"Error acquiring DB connection from pool or processing URLs: {e}")
            # drop the pool reference so we attempt to recreate it next loop
            try:
                pool = None
            except Exception:
                pass
            await asyncio.sleep(5)
            continue

        logger.debug("Waiting for next run...")
        # sleep in small increments so we can respond to stop_event quickly
        total_sleep = 93600
        check_interval = 5  # seconds
        slept = 0
        while slept < total_sleep:
            if stop_event is not None and getattr(stop_event, 'is_set', lambda: False)():
                logger.info("Dynamic spider stop_event detected during sleep; exiting loop.")
                break
            to_sleep = min(check_interval, total_sleep - slept)
            await asyncio.sleep(to_sleep)
            slept += to_sleep
        
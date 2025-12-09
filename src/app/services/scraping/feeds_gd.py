import asyncio
import random
from pathlib import Path
from googlesearch import search
from loguru import logger
from concurrent.futures import ThreadPoolExecutor

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 '
    '(KHTML, like Gecko) Version/16.5 Safari/605.1.15',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0',
]

DORKS = [
    '"cybersecurity" "RSS feed"',
    '"cybersecurity" "Atom feed"',
    '"OT security" "RSS feed"',
    '"OT security" "Atom feed"',
    '"IT security" "RSS feed"',
    '"IT security" "Atom feed"',
    '"information security" "RSS feed"',
    '"information security" "Atom feed"',
]

MAX_SEARCHES_PER_MINUTE = 6
MIN_SECONDS_BETWEEN_SEARCHES = 60 / MAX_SEARCHES_PER_MINUTE

executor = ThreadPoolExecutor()

OUTPUT_FILE = Path("./data/urls_cybersecurity_ot_it.txt")


async def search_async(query: str, num_results: int = 15) -> list[str]:
    '''
    @brief Perform a Google search asynchronously.

    Executes a search query using Google's search engine via the `googlesearch` module.
    The function runs within a thread executor to remain non-blocking in async context.

    @param query Search query to be executed.
    @param num_results Number of results to retrieve.
    @return List of result URLs.
    '''
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        executor, lambda: list(search(query, num_results=num_results))
    )


async def run_dork_search_feed():
    '''
    @brief Perform Google Dork queries and write results incrementally to a file.

    Executes a list of predefined search queries related to cybersecurity topics.
    Each valid, non-duplicate result is written immediately to a local file.
    Includes randomized delays to reduce risk of throttling by Google.

    @note Helps in continuously collecting potentially relevant URLs.
    '''
    logger.info("Starting search for cybersecurity-related URLs...")

    existing_urls = set()
    if OUTPUT_FILE.exists():
        with OUTPUT_FILE.open("r", encoding="utf-8") as f:
            existing_urls = {line.strip() for line in f if line.strip()}

    for dork in DORKS:
        logger.info(f"🔎 Searching with dork: {dork}")
        try:
            results = await search_async(dork, num_results=15)
            for url in results:
                if not url.startswith("http"):
                    continue
                if url in existing_urls:
                    continue

                logger.success(f"Found URL: {url}")
                with OUTPUT_FILE.open("a", encoding="utf-8") as f:
                    f.write(url + "\n")

                existing_urls.add(url)

                await asyncio.sleep(random.uniform(1, 2))

        except Exception as e:
            logger.error(f"Error while searching with dork '{dork}': {e}")

        sleep_time = random.uniform(
            MIN_SECONDS_BETWEEN_SEARCHES * 0.8, MIN_SECONDS_BETWEEN_SEARCHES * 1.5
        )
        logger.info(f"Waiting {sleep_time:.2f} seconds before next search...")
        await asyncio.sleep(sleep_time)

    logger.info("Finished all dork searches.")

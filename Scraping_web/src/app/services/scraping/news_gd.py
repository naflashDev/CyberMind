import asyncio
import json
import random
from pathlib import Path
from typing import List, Dict, Optional
import httpx
from bs4 import BeautifulSoup
from googlesearch import search
from loguru import logger

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/123.0.0.0 Safari/537.36'
    )
}

DORKS = [
    '"SCADA vulnerability"',
    '"ICS vulnerability"',
    '"OT security" AND "vulnerability"',
    '"cybersecurity vulnerability" after:2024-05-01',
    '"vulnerabilidad SCADA"',
    '"ciberseguridad industrial vulnerabilidad"',
    '"seguridad OT" AND "vulnerabilidad"',
    '"vulnerabilidad ciberseguridad"',
]

KEYWORDS = [
    'vulnerability', 'exploit', 'SCADA', 'ICS', 'OT security',
    'IT security', 'malware', 'vulnerabilidad', 'ciberseguridad'
]

OUTPUT_FILE = Path("./outputs/result.json")


def is_relevant(text: str, keywords: List[str] = KEYWORDS) -> bool:
    '''
    @brief Check if the article contains any relevant keyword.

    Evaluates whether the given text includes at least one of the defined
    keywords (case-insensitive).

    @param text: Full text content of the article.
    @param keywords: List of keywords to check against.
    @return: True if any keyword is found, False otherwise.
    '''
    return any(k.lower() in text.lower() for k in keywords)


async def extract_news_structure(url: str) -> Optional[Dict]:
    '''
    @brief Extract structured content from a news article URL.

    Fetches and parses the HTML of the given URL to extract article content
    and metadata. Only returns the result if it's considered relevant.

    @param url: URL of the article.
    @return: Dictionary containing article metadata or None if irrelevant or
    error occurs.
    '''
    try:
        async with httpx.AsyncClient(
            headers=HEADERS, timeout=10, follow_redirects=True
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            def extract_all(tag: str) -> List[str]:
                return [e.get_text(strip=True) for e in soup.find_all(tag)]

            news = {
                "url": url,
                "title": soup.title.string.strip() if soup.title else "",
                "h1": extract_all("h1"),
                "h2": extract_all("h2"),
                "h3": extract_all("h3"),
                "h4": extract_all("h4"),
                "h5": extract_all("h5"),
                "h6": extract_all("h6"),
                "p": extract_all("p"),
            }

            full_text = " ".join(news["p"])
            return news if is_relevant(full_text) else None

    except Exception as e:
        logger.warning(f"Error processing {url}: {e}")
        return None


async def async_search(query: str, num_results: int = 5) -> List[str]:
    '''
    @brief Perform Google search asynchronously.

    Executes a Google search for the given query in a non-blocking way.

    @param query: Search string.
    @param num_results: Number of URLs to retrieve.
    @return: List of result URLs.
    '''
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, lambda: list(search(query, num_results=num_results))
    )


def load_existing_urls() -> set:
    '''
    @brief Load existing URLs from the result file.

    Reads existing URLs from the JSON file to avoid duplication.

    @return: Set of existing URLs.
    '''
    if OUTPUT_FILE.exists():
        try:
            with OUTPUT_FILE.open("r", encoding="utf-8") as f:
                existing_news = json.load(f)
                return {item["url"] for item in existing_news}
        except json.JSONDecodeError:
            logger.warning("JSON file is corrupted. Starting with an empty set.")
            return set()
    return set()


def append_news_item(news_item: Dict):
    '''
    @brief Append a single news item to the result file.

    Loads existing items, appends a new one, and writes back to disk.

    @param news_item: Dictionary with structured news content.
    '''
    try:
        if OUTPUT_FILE.exists():
            with OUTPUT_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []

        data.append(news_item)

        with OUTPUT_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Failed to append news item: {e}")


async def run_news_search():
    '''
    @brief Main routine to search and collect cybersecurity news articles.

    - Iterates over predefined dorks.
    - Searches via Google.
    - Extracts and filters relevant articles.
    - Writes each relevant article to JSON immediately.
    '''
    logger.info("Starting news search...")

    seen_urls = load_existing_urls()

    for dork in DORKS:
        logger.info(f"Searching with dork: {dork}")
        try:
            results = await async_search(dork, num_results=5)
            for url in results:
                if not url.startswith("http") or url in seen_urls:
                    continue

                news_item = await extract_news_structure(url)
                if news_item:
                    append_news_item(news_item)
                    seen_urls.add(url)
                    logger.success(f"Added news from {url}")

                await asyncio.sleep(random.uniform(2, 5))

        except Exception as e:
            logger.error(f"rror during search with dork '{dork}': {e}")

        sleep_time = random.randint(20, 35)
        logger.info(f"Waiting {sleep_time} seconds before next dork...")
        await asyncio.sleep(sleep_time)

    logger.info("Finished news collection.")


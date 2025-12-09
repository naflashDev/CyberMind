# @ Author: RootAnto
# @ Project: Cebolla
# @ Create Time: 2025-05-20 10:30:50
# @ Description: Automates extracting real URLs from Google Alerts RSS feeds.
# It reads feed URLs from a file, parses each feed to retrieve entries, cleans
# redirected links to get the actual URLs, and saves them to an output file.
# Logging with loguru is included for monitoring the process.

import feedparser
import urllib.parse
from loguru import logger
import os

# Path to the file containing Google Alerts RSS feed URLs
FEEDS_FILE_PATH = "./data/google_alert_rss.txt"

# Path to the file where the extracted real URLs will be saved
URLS_FILE_PATH = "./data/urls_cybersecurity_ot_it.txt"


def clean_google_redirect_url(url: str) -> str:
    '''
    @brief Extracts the real URL from a Google Alerts redirect link.

    Google Alerts often provides links that redirect through Google's own
    tracking system. This function parses the URL and extracts the actual
    destination URL from the query string.

    @param url: The full Google redirect URL
    (typically containing a ?url= parameter).
    @return: The real target URL extracted from the redirect,
    or the original URL if not found.
    '''
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    real_url = query_params.get("url", [url])[0]
    return real_url


def fetch_and_save_alert_urls():
    '''
    @brief Parses Google Alerts RSS feeds and extracts the real destination
    URLs.

    This function reads RSS feed URLs from a file, parses each feed using
    `feedparser`, and extracts the actual destination URLs from redirect links
    (typical in Google Alerts). It removes any redirect/tracking wrappers,
    cleans the URLs, and writes the final list to a specified output file.

    The input file (defined by FEEDS_FILE_PATH) should contain one feed URL
    per line. Lines may optionally contain additional info after
    a '|' character, which will be ignored.

    @note Uses the `clean_google_redirect_url()` helper to extract real URLs
    from redirect links.
    @note Logs progress and warnings using the `loguru` logger.

    @return None. The function writes output to a file and logs progress.
    '''
    if not os.path.exists(FEEDS_FILE_PATH):
        logger.error(f"Feeds file not found: {FEEDS_FILE_PATH}")
        return

    os.makedirs(os.path.dirname(URLS_FILE_PATH), exist_ok=True)

    total_urls = []

    # Read only the clean URL before a possible '|' separator
    with open(FEEDS_FILE_PATH, "r", encoding="utf-8") as feeds_file:
        feed_urls = []
        for line in feeds_file:
            line = line.strip()
            if not line:
                continue
            url_only = line.split('|')[0].strip()
            feed_urls.append(url_only)

    for feed_url in feed_urls:
        logger.info(f"Reading feed: {feed_url}")
        feed = feedparser.parse(feed_url)

        if not feed.entries:
            logger.warning(f"No entries found in: {feed_url}")
            continue

        for entry in feed.entries:
            link = entry.get("link")
            if link:
                clean_url = clean_google_redirect_url(link)
                total_urls.append(clean_url)

    if not total_urls:
        logger.warning("No valid URLs were extracted from any feed.")
        return

    with open(URLS_FILE_PATH, "w", encoding="utf-8") as f:
        for url in total_urls:
            f.write(url + "\n")

    logger.info(f"{len(total_urls)} URLs saved to {URLS_FILE_PATH}")

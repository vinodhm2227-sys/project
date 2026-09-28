"""
scraper.py
----------
This file is responsible for one job: given a URL, download the page
and turn it into clean, readable plain text.

HOW `requests` WORKS (quick explanation):
`requests.get(url)` sends an HTTP GET request to a server, exactly like
a browser does when you type a URL and hit Enter. It waits for the
server to respond and gives us back a `Response` object containing the
status code (200 = OK, 404 = Not Found, etc.) and the raw HTML text.

HOW BeautifulSoup EXTRACTS TEXT (quick explanation):
BeautifulSoup takes raw HTML (a big string full of tags like <div>,
<p>, <script>) and turns it into a tree of Python objects we can
search and manipulate. We use it to:
  1. Find and remove tags we don't care about (scripts, styles, nav).
  2. Pull out just the human-readable text with `.get_text()`.
"""

import re
from urllib.parse import urlparse
import ipaddress
import socket

import requests
from bs4 import BeautifulSoup
import urllib.robotparser as robotparser

# How long we'll wait for a website to respond before giving up.
REQUEST_TIMEOUT_SECONDS = 10

# A normal-looking User-Agent so we behave like a regular browser
# instead of an anonymous bot (some sites block requests with no
# User-Agent header at all).
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; SimpleScrapingChatbot/1.0; "
        "+https://example.com/bot-info)"
    )
}

# Tags whose content is never useful "readable text" for our chatbot.
TAGS_TO_REMOVE = [
    "script", "style", "nav", "footer", "header", "noscript",
    "form", "svg", "iframe", "aside",
]


class ScraperError(Exception):
    """
    Custom exception used to signal a "known" scraping problem
    (bad URL, timeout, blocked by robots.txt, etc.) with a message
    that's safe and clear to show directly to the end user.
    """
    pass


def _validate_url(url: str) -> str:
    """
    Basic URL validation and security checks.

    - Ensures the URL has a scheme (http/https) and a domain.
    - Blocks obviously "internal network" targets (localhost, private
      IP ranges) so the app can't be used to probe internal services.
      This is a best-effort check, not a bulletproof security barrier.
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ScraperError("Please enter a valid URL starting with http:// or https://")

    if not parsed.netloc:
        raise ScraperError("That doesn't look like a valid website URL.")

    hostname = parsed.hostname or ""

    # Block localhost / loopback / private network addresses.
    blocked_hostnames = {"localhost", "127.0.0.1", "0.0.0.0"}
    if hostname.lower() in blocked_hostnames:
        raise ScraperError("Scraping local or internal addresses is not allowed.")

    try:
        # Resolve the hostname to an IP and check if it's private.
        resolved_ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(resolved_ip)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
            raise ScraperError("Scraping internal/private network addresses is not allowed.")
    except socket.gaierror:
        # If we can't resolve it, requests will fail later anyway with
        # a clear error, so we let it continue rather than blocking.
        pass

    return url


def _check_robots_txt(url: str) -> bool:
    """
    Checks the site's robots.txt file to see if our bot is allowed to
    fetch this specific page. Returns True if allowed (or if we can't
    determine it, in which case we default to allowing but still keep
    the request lightweight and polite).
    """
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    parser = robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
        return parser.can_fetch(HEADERS["User-Agent"], url)
    except Exception:
        # If robots.txt can't be fetched/parsed, we don't block the
        # user -- most sites without a robots.txt allow crawling.
        return True


def _clean_text(raw_text: str) -> str:
    """
    Collapses excessive whitespace/newlines so the text we send to the
    LLM is compact and readable instead of full of blank lines and
    stray spaces left over from the page's HTML layout.
    """
    # Replace any run of whitespace (spaces, tabs, newlines) with a
    # single space, then trim the ends.
    cleaned = re.sub(r"\s+", " ", raw_text)
    return cleaned.strip()


def scrape_website(url: str, max_length: int = 15000) -> str:
    """
    Main entry point for this module.

    1. Validate the URL and block unsafe/internal targets.
    2. Respect robots.txt.
    3. Download the page with `requests`.
    4. Parse it with BeautifulSoup and strip out non-content tags.
    5. Extract and clean the readable text.
    6. Truncate to `max_length` characters to keep things fast and
       within LLM context limits.

    Raises ScraperError with a friendly message on any failure.
    """
    url = _validate_url(url)

    if not _check_robots_txt(url):
        raise ScraperError(
            "This website's robots.txt does not allow automated scraping of this page."
        )

    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.Timeout:
        raise ScraperError("The website took too long to respond. Please try again.")
    except requests.exceptions.ConnectionError:
        raise ScraperError("Could not connect to that website. Please check the URL.")
    except requests.exceptions.RequestException as e:
        raise ScraperError(f"Failed to fetch the website: {e}")

    if response.status_code != 200:
        raise ScraperError(
            f"The website returned an error (HTTP {response.status_code}). "
            "It may be unavailable or blocking automated requests."
        )

    content_type = response.headers.get("Content-Type", "")
    if "text/html" not in content_type:
        raise ScraperError("That URL does not appear to point to an HTML web page.")

    # Parse the HTML using BeautifulSoup's built-in parser.
    soup = BeautifulSoup(response.text, "html.parser")

    # Remove tags that never contain useful "readable content" --
    # scripts, styles, navigation bars, footers, etc.
    for tag_name in TAGS_TO_REMOVE:
        for tag in soup.find_all(tag_name):
            tag.decompose()  # removes the tag and everything inside it

    # get_text() walks the remaining tree and joins all the leftover
    # text nodes together. separator=" " keeps words from neighboring
    # tags from accidentally being glued together.
    raw_text = soup.get_text(separator=" ")
    cleaned_text = _clean_text(raw_text)

    if not cleaned_text:
        raise ScraperError("No readable text could be found on that page.")

    # Limit how much text we keep, so the LLM prompt doesn't get huge.
    if len(cleaned_text) > max_length:
        cleaned_text = cleaned_text[:max_length]

    return cleaned_text

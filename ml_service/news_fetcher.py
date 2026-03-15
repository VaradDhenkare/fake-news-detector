"""
news_fetcher.py
---------------
Fetches live news from free RSS feeds and scrapes article text from URLs.

RSS Sources (no API key required):
  - BBC News
  - Reuters
  - The Guardian
  - NPR News

Web scraping uses requests + BeautifulSoup for article text extraction.
"""

import re
import logging
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

# ── RSS Feed Sources ──────────────────────────────────────────────────────────
RSS_SOURCES = [
    {
        "name": "BBC News",
        "url": "https://feeds.bbci.co.uk/news/rss.xml",
        "icon": "🇬🇧",
    },
    {
        "name": "Reuters",
        "url": "https://feeds.reuters.com/reuters/topNews",
        "icon": "📰",
    },
    {
        "name": "The Guardian",
        "url": "https://www.theguardian.com/world/rss",
        "icon": "🌍",
    },
    {
        "name": "NPR News",
        "url": "https://feeds.npr.org/1001/rss.xml",
        "icon": "🎙️",
    },
    {
        "name": "Al Jazeera",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "icon": "🗺️",
    },
]

REQUEST_TIMEOUT = 8  # seconds
MAX_ARTICLES_PER_SOURCE = 6


# ── RSS Fetcher ───────────────────────────────────────────────────────────────

def fetch_rss_articles(max_per_source: int = MAX_ARTICLES_PER_SOURCE) -> list[dict]:
    """
    Fetch headlines + summaries from all RSS_SOURCES.

    Returns list of article dicts:
    {
        "title":       str,
        "summary":     str,
        "url":         str,
        "source":      str,
        "source_icon": str,
        "published":   str,
        "text":        str   # title + summary combined for ML prediction
    }
    """
    articles = []

    for source in RSS_SOURCES:
        try:
            logger.info(f"Fetching RSS from {source['name']}...")
            feed = feedparser.parse(source["url"])

            entries = feed.entries[:max_per_source]
            for entry in entries:
                title   = _clean(getattr(entry, "title",   ""))
                summary = _clean(getattr(entry, "summary", ""))
                link    = getattr(entry, "link", "")
                pub     = getattr(entry, "published", "")

                # Skip entries with no meaningful content
                if not title or len(title) < 10:
                    continue

                # Combine title + summary for richer ML input
                combined = f"{title}. {summary}" if summary else title

                articles.append({
                    "title":       title,
                    "summary":     summary,
                    "url":         link,
                    "source":      source["name"],
                    "source_icon": source["icon"],
                    "published":   pub,
                    "text":        combined,
                })

        except Exception as e:
            logger.warning(f"Failed to fetch RSS from {source['name']}: {e}")
            continue

    # Sort articles by published date, newest first
    articles.sort(key=lambda x: datetime.strptime(x["published"], "%a, %d %b %Y %H:%M:%S %z") if x["published"] else datetime.min, reverse=True)
    logger.info(f"Fetched {len(articles)} articles from RSS feeds.")
    return articles


# ── URL Article Scraper ────────────────────────────────────────────────────────

def extract_article_text(url: str) -> dict:
    """
    Scrape the main text content from a news article URL.
    Falls back to OG tags / JSON-LD for JS-rendered sites (Reuters, CNN, etc.).
    """
    if not url or not url.startswith(("http://", "https://")):
        raise ValueError("Invalid URL. Must start with http:// or https://")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise ValueError(f"Request timed out after {REQUEST_TIMEOUT}s: {url}")
    except requests.exceptions.HTTPError as e:
        raise ValueError(f"HTTP error {e.response.status_code} fetching URL: {url}")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Could not reach URL: {e}")

    soup = BeautifulSoup(response.content, "lxml")

    # ── Title: OG tag > h1 > <title> ─────────────────────────────────────────
    title = ""
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = _clean(og_title["content"])
    elif soup.find("h1"):
        title = _clean(soup.find("h1").get_text())
    elif soup.find("title"):
        title = _clean(soup.find("title").get_text())

    # ── Meta description fallback ─────────────────────────────────────────────
    meta_desc = ""
    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        meta_desc = _clean(og_desc["content"])
    else:
        std_desc = soup.find("meta", attrs={"name": "description"})
        if std_desc and std_desc.get("content"):
            meta_desc = _clean(std_desc["content"])

    # ── JSON-LD structured data (articleBody on news sites) ──────────────────
    import json as _json
    ld_text = ""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = _json.loads(script.string or "")
            if isinstance(data, list):
                data = data[0]
            if isinstance(data, dict):
                for key in ("articleBody", "description", "abstract"):
                    val = data.get(key, "")
                    if val and len(val) > 50:
                        ld_text = _clean(str(val))[:3000]
                        break
        except Exception:
            pass
        if ld_text:
            break

    # ── Remove noise ──────────────────────────────────────────────────────────
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "form", "button", "iframe", "noscript"]):
        tag.decompose()

    # ── Article body ──────────────────────────────────────────────────────────
    article_tag = soup.find("article") or soup.find("main")
    paragraphs  = article_tag.find_all("p") if article_tag else soup.find_all("p")
    body_text   = " ".join(
        _clean(p.get_text()) for p in paragraphs if len(p.get_text().strip()) > 40
    )

    # ── Priority: JSON-LD > scraped body > meta description ──────────────────
    if ld_text:
        content = ld_text
    elif len(body_text) > 100:
        content = body_text
    else:
        content = meta_desc or body_text   # JS-rendered site fallback

    full_text = f"{title}. {content}".strip() if title else content

    if len(full_text) < 30:
        raise ValueError(
            "Not enough article text could be extracted. This site may use "
            "JavaScript rendering. Try copying the article text and using "
            "the 'Analyze Text' option instead."
        )

    domain = re.sub(r"https?://(www\.)?", "", url).split("/")[0]
    return {
        "title":  title,
        "text":   full_text[:8000],
        "url":    url,
        "source": domain,
    }



# ── Internal helper ───────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

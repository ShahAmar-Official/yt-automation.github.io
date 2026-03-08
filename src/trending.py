"""
trending.py — Fetch trending topics from Google Trends, Hacker News, and NewsAPI.

Returns a deduplicated list of trending topic strings and picks the
best topic using a simple cross-source scoring heuristic.
"""

import logging
import time
from typing import Any

import requests

import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_MIN_TOPICS = 10  # Minimum number of topics to maintain in the combined list

# ---------------------------------------------------------------------------
# Fallback topics used when all external sources fail
# ---------------------------------------------------------------------------
FALLBACK_TOPICS: list[str] = [
    "Artificial Intelligence breakthroughs",
    "Space exploration news",
    "Viral life hacks",
    "Tech gadgets you need",
    "Hidden travel destinations",
    "Money-saving tips",
    "Fitness motivation",
    "Surprising science facts",
    "DIY home improvement",
    "Healthy eating trends",
]


def _fetch_google_trends(retries: int = 3, backoff: float = 2.0) -> list[str]:
    """Fetch daily trending searches for the US from Google Trends.

    Uses pytrends if available, otherwise falls back to an empty list so the
    rest of the pipeline can continue with Hacker News results.
    """
    try:
        from pytrends.request import TrendReq  # type: ignore[import]
    except ImportError:
        logger.warning("pytrends not installed — skipping Google Trends")
        return []

    for attempt in range(1, retries + 1):
        try:
            pt = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
            trending_df = pt.trending_searches(pn="united_states")
            topics: list[str] = trending_df[0].tolist()
            logger.info("Google Trends returned %d topics", len(topics))
            return topics[:20]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Google Trends attempt %d/%d failed: %s", attempt, retries, exc)
            if attempt < retries:
                time.sleep(backoff * attempt)
    return []


def _fetch_hackernews_trending(retries: int = 3, backoff: float = 2.0) -> list[str]:
    """Fetch top story titles from Hacker News via the Algolia API.

    Completely free — no API key or authentication required.  The Algolia
    search API for Hacker News returns current front-page stories in a
    single request.
    """
    url = "https://hn.algolia.com/api/v1/search"
    params = {"tags": "front_page", "hitsPerPage": 25}

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            hits = data.get("hits", [])
            topics = [hit["title"] for hit in hits if hit.get("title")]
            logger.info("Hacker News returned %d topics", len(topics))
            return topics[:20]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Hacker News attempt %d/%d failed: %s", attempt, retries, exc)
            if attempt < retries:
                time.sleep(backoff * attempt)
    return []


def _fetch_newsapi_trending(retries: int = 3, backoff: float = 2.0) -> list[str]:
    """Fetch top headline titles from NewsAPI.org.

    Requires ``NEWSAPI_KEY`` to be set; returns an empty list gracefully
    if the key is absent or the request fails.
    """
    if not config.NEWSAPI_KEY:
        return []

    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "country": "us",
        "pageSize": 20,
        "apiKey": config.NEWSAPI_KEY,
    }

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
            topics = [
                # NewsAPI titles often include a source suffix like "Title - Source Name";
                # strip the suffix to keep only the meaningful headline text.
                a["title"].split(" - ")[0].strip()
                for a in articles
                if a.get("title") and a["title"] != "[Removed]"
            ]
            logger.info("NewsAPI returned %d topics", len(topics))
            return topics[:20]
        except Exception as exc:  # noqa: BLE001
            logger.warning("NewsAPI attempt %d/%d failed: %s", attempt, retries, exc)
            if attempt < retries:
                time.sleep(backoff * attempt)
    return []


def get_trending_topics() -> list[str]:
    """Combine Google Trends, Hacker News, and NewsAPI results into a deduplicated list.

    Returns at least 10 topic strings, falling back to :data:`FALLBACK_TOPICS`
    if the external sources cannot provide enough results.
    """
    google_topics = _fetch_google_trends()
    hn_topics = _fetch_hackernews_trending()
    newsapi_topics = _fetch_newsapi_trending()

    seen: set[str] = set()
    combined: list[str] = []
    for topic in google_topics + hn_topics + newsapi_topics:
        normalised = topic.strip()
        if normalised and normalised.lower() not in seen:
            seen.add(normalised.lower())
            combined.append(normalised)

    if len(combined) < _MIN_TOPICS:
        logger.info("Fewer than %d topics found (%d); padding with fallbacks", _MIN_TOPICS, len(combined))
        for fallback in FALLBACK_TOPICS:
            if fallback.lower() not in seen:
                seen.add(fallback.lower())
                combined.append(fallback)
            if len(combined) >= _MIN_TOPICS:
                break

    logger.info("Total unique topics available: %d", len(combined))
    return combined


def get_best_topic() -> str:
    """Pick the most viral/interesting topic using a cross-source scoring heuristic.

    Fetches from each source once, then scores topics so that those appearing
    in multiple sources rank higher.  Within each source, earlier results
    (higher rank) get more points.
    """
    google_topics = _fetch_google_trends()
    hn_topics = _fetch_hackernews_trending()
    newsapi_topics = _fetch_newsapi_trending()

    scores: dict[str, float] = {}

    for rank, topic in enumerate(google_topics):
        key = topic.strip().lower()
        scores[key] = scores.get(key, 0) + (len(google_topics) - rank)

    for rank, topic in enumerate(hn_topics):
        key = topic.strip().lower()
        # Double the score if it already appeared in Google Trends (cross-source bonus)
        bonus = 2.0 if key in scores else 1.0
        scores[key] = scores.get(key, 0) + bonus * (len(hn_topics) - rank)

    for rank, topic in enumerate(newsapi_topics):
        key = topic.strip().lower()
        # Double the score if it already appeared in another source (cross-source bonus)
        bonus = 2.0 if key in scores else 1.0
        scores[key] = scores.get(key, 0) + bonus * (len(newsapi_topics) - rank)

    # Rebuild mapping from lower-case key → original casing
    original: dict[str, str] = {}
    for topic in google_topics + hn_topics + newsapi_topics:
        key = topic.strip().lower()
        if key not in original:
            original[key] = topic.strip()

    if not scores:
        logger.warning("No trending topics found; using first fallback topic")
        return FALLBACK_TOPICS[0]

    best_key = max(scores, key=lambda k: scores[k])
    best_topic = original.get(best_key, FALLBACK_TOPICS[0])
    logger.info("Best topic selected: '%s' (score=%.1f)", best_topic, scores[best_key])

    # Pad the combined topic list with fallbacks so get_trending_topics() stays
    # consistent without making a second round of network calls.
    seen: set[str] = {t.strip().lower() for t in google_topics + hn_topics + newsapi_topics}
    combined = list(original.values())
    for fallback in FALLBACK_TOPICS:
        if fallback.lower() not in seen:
            seen.add(fallback.lower())
            combined.append(fallback)
        if len(combined) >= _MIN_TOPICS:
            break
    logger.info("Total unique topics available: %d", len(combined))

    return best_topic

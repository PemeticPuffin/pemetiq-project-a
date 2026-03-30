"""Fetch recent company news from Finnhub."""

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import requests
from dotenv import load_dotenv

from config import NEWS_LOOKBACK_DAYS, REQUEST_TIMEOUT, MAX_RETRIES

load_dotenv()
logger = logging.getLogger(__name__)

_FINNHUB_NEWS_URL = "https://finnhub.io/api/v1/company-news"


@dataclass
class NewsArticle:
    """A single news article."""

    title: str
    description: Optional[str]
    source: str
    published_at: str
    url: str


@dataclass
class NewsData:
    """Collection of news articles for a company."""

    company_name: str
    ticker: str
    articles: list[NewsArticle] = field(default_factory=list)
    fetch_error: Optional[str] = None

    @property
    def article_count(self) -> int:
        return len(self.articles)


def fetch_news(company_name: str, ticker: str, max_articles: int = 30) -> NewsData:
    """Fetch recent news for a company from Finnhub.

    Args:
        company_name: Legal company name (used for logging only).
        ticker: Stock ticker symbol used as the Finnhub query key.
        max_articles: Maximum number of articles to return.

    Returns:
        NewsData with articles, or fetch_error set if failed.
    """
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        return NewsData(
            company_name=company_name,
            ticker=ticker,
            fetch_error="FINNHUB_API_KEY not set in environment",
        )

    to_date = datetime.utcnow().strftime("%Y-%m-%d")
    from_date = (datetime.utcnow() - timedelta(days=NEWS_LOOKBACK_DAYS)).strftime("%Y-%m-%d")

    params = {
        "symbol": ticker,
        "from": from_date,
        "to": to_date,
        "token": api_key,
    }

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(
                _FINNHUB_NEWS_URL,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()

            if not isinstance(data, list):
                error_msg = data.get("error", "Unexpected Finnhub response format")
                logger.warning("Finnhub error: %s", error_msg)
                return NewsData(company_name=company_name, ticker=ticker, fetch_error=error_msg)

            articles = []
            for item in data[:max_articles]:
                title = item.get("headline", "").strip()
                if not title:
                    continue
                # Convert Unix timestamp to ISO date string
                ts = item.get("datetime", 0)
                published_at = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d") if ts else ""
                articles.append(
                    NewsArticle(
                        title=title,
                        description=item.get("summary") or None,
                        source=item.get("source", "Unknown"),
                        published_at=published_at,
                        url=item.get("url", ""),
                    )
                )

            logger.info("Fetched %d articles for %s from Finnhub", len(articles), company_name)
            return NewsData(company_name=company_name, ticker=ticker, articles=articles)

        except requests.RequestException as exc:
            if attempt < MAX_RETRIES:
                logger.warning("Retry %d/%d for Finnhub: %s", attempt + 1, MAX_RETRIES, exc)
                time.sleep(1)
            else:
                logger.warning("Finnhub fetch failed: %s", exc)
                return NewsData(
                    company_name=company_name,
                    ticker=ticker,
                    fetch_error=str(exc),
                )


def format_articles_for_prompt(news_data: NewsData) -> str:
    """Format NewsData into a compact string suitable for an LLM prompt.

    Args:
        news_data: Populated NewsData instance.

    Returns:
        Multi-line string with numbered headlines and descriptions.
    """
    if news_data.fetch_error:
        return f"[News data unavailable: {news_data.fetch_error}]"

    if not news_data.articles:
        return "[No news articles found for this company in the last 30 days.]"

    lines = [
        f"Recent news for {news_data.company_name} ({news_data.ticker}) "
        f"— {news_data.article_count} articles:\n"
    ]
    for i, article in enumerate(news_data.articles, 1):
        date = article.published_at[:10] if article.published_at else "unknown date"
        lines.append(f"{i}. [{date}] {article.title} ({article.source})")
        if article.description:
            lines.append(f"   {article.description}")
    return "\n".join(lines)

"""
news.py - Asset de récupération des news via Google News RSS
============================================================

RÔLE : Récupère les news financières pour chaque ticker via RSS feeds
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dagster import asset, AssetExecutionContext, MetadataValue
import time

from market_etl_pipeline.config import TICKERS


def fetch_ticker_news_rss(ticker: str) -> list:
    """Récupère les news pour un ticker via Google News RSS"""
    try:
        # URL du flux RSS Google News
        query = f"{ticker} stock" if not ticker.endswith("-USD") else ticker.replace("-USD", " crypto")
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')
        
        records = []
        for item in items[:3]:  # Top 3 news par ticker
            records.append({
                'ticker': ticker,
                'title': item.title.text if item.title else 'N/A',
                'publisher': item.source.text if item.source else 'N/A',
                'published_date': item.pubDate.text if item.pubDate else 'N/A',
                'link': item.link.text if item.link else ''
            })
        
        return records
        
    except Exception:
        return []


@asset(group_name="market_data")
def asset_news(context: AssetExecutionContext) -> pd.DataFrame:
    """
    Asset 3/5 : Récupère les news financières via Google News RSS
    """
    
    context.log.info(f"Fetching news for {len(TICKERS)} tickers via RSS")
    
    all_news = []
    
    for i, ticker in enumerate(TICKERS, 1):
        context.log.info(f"[{i}/{len(TICKERS)}] Fetching news for {ticker}...")
        
        records = fetch_ticker_news_rss(ticker)
        
        if records:
            all_news.extend(records)
            context.log.info(f"✓ {ticker}: {len(records)} news")
        
        if i < len(TICKERS):
            time.sleep(0.3)
    
    if not all_news:
        context.log.warning("No news retrieved, using empty DataFrame")
        df = pd.DataFrame(columns=['ticker', 'title', 'publisher', 'published_date', 'link'])
    else:
        df = pd.DataFrame(all_news)
        context.log.info(f"Retrieved {len(df)} news items")
    
    context.add_output_metadata({
        "num_news": len(df),
        "num_tickers_with_news": df['ticker'].nunique() if len(df) > 0 else 0,
        "preview": MetadataValue.text(df.head(5).to_csv(index=False) if len(df) > 0 else "No news")
    })
    
    return df

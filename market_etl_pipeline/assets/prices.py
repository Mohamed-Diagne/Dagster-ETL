"""
prices.py - Asset de récupération des prix via API Yahoo Finance directe
==========================================================================

RÔLE : Premier asset du pipeline - récupère les prix de marché via API REST
"""

import pandas as pd
import requests
from dagster import asset, AssetExecutionContext, MetadataValue
import time
from datetime import datetime, timedelta

from market_etl_pipeline.config import TICKERS


def fetch_ticker_data(ticker: str) -> list:
    """Récupère les données pour un ticker via API Yahoo Finance directe"""
    try:
        # API Yahoo Finance directe
        period1 = int((datetime.now() - timedelta(days=7)).timestamp())
        period2 = int(datetime.now().timestamp())
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {
            'period1': period1,
            'period2': period2,
            'interval': '1d'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        
        if 'chart' not in data or 'result' not in data['chart']:
            return []
        
        result = data['chart']['result'][0]
        
        if 'timestamp' not in result or 'indicators' not in result:
            return []
        
        timestamps = result['timestamp']
        quotes = result['indicators']['quote'][0]
        
        records = []
        for i in range(len(timestamps)):
            close = quotes['close'][i]
            if close is not None:
                records.append({
                    'ticker': ticker,
                    'date': pd.Timestamp(timestamps[i], unit='s').normalize(),
                    'open': float(quotes['open'][i] or 0),
                    'high': float(quotes['high'][i] or 0),
                    'low': float(quotes['low'][i] or 0),
                    'close': float(close),
                    'volume': int(quotes['volume'][i] or 0)
                })
        
        # Retourne les 2 derniers jours
        return records[-2:] if len(records) >= 2 else records
        
    except Exception:
        return []


@asset(group_name="market_data")
def asset_prices(context: AssetExecutionContext) -> pd.DataFrame:
    """
    Asset 1/5 : Récupère les prix quotidiens via API Yahoo Finance REST
    """
    
    context.log.info(f"Fetching prices for {len(TICKERS)} tickers via API")
    
    all_data = []
    failed_tickers = []
    
    for i, ticker in enumerate(TICKERS, 1):
        context.log.info(f"[{i}/{len(TICKERS)}] Fetching {ticker}...")
        
        records = fetch_ticker_data(ticker)
        
        if records:
            all_data.extend(records)
            context.log.info(f"✓ {ticker}: {len(records)} records")
        else:
            failed_tickers.append(ticker)
            context.log.warning(f"✗ {ticker}: no data")
        
        if i < len(TICKERS):
            time.sleep(1.0)
    
    if not all_data:
        raise RuntimeError("No price data retrieved")
    
    df = pd.DataFrame(all_data).sort_values(['ticker', 'date'])
    df['date'] = pd.to_datetime(df['date'])
    
    context.log.info(f"Retrieved {len(df)} records for {df['ticker'].nunique()} tickers")
    context.log.info(f"Failed: {len(failed_tickers)} tickers")
    
    context.add_output_metadata({
        "num_records": len(df),
        "num_tickers": df['ticker'].nunique(),
        "failed_tickers": MetadataValue.text(", ".join(failed_tickers) if failed_tickers else "None"),
        "date_range": MetadataValue.text(f"{df['date'].min()} to {df['date'].max()}"),
        "preview": MetadataValue.text(df.head(10).to_csv(index=False)),
    })
    
    return df

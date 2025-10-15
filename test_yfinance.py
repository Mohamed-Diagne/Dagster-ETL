#!/usr/bin/env python3
"""Test script pour diagnostiquer yfinance"""

import yfinance as yf
import pandas as pd

print("=== Test 1: Ticker.history() AAPL ===")
try:
    ticker = yf.Ticker('AAPL')
    data = ticker.history(period='2d')
    print(f'Shape: {data.shape}')
    print(data)
    print()
except Exception as e:
    print(f'ERROR: {e}\n')

print("=== Test 2: download AAPL ===")
try:
    data2 = yf.download('AAPL', period='2d', progress=False)
    print(f'Shape: {data2.shape}')
    print(data2)
    print()
except Exception as e:
    print(f'ERROR: {e}\n')

print("=== Test 3: download multiple tickers ===")
try:
    data3 = yf.download(['AAPL', 'MSFT', 'GOOGL'], period='2d', group_by='column', progress=False)
    print(f'Shape: {data3.shape}')
    print(f'Columns: {data3.columns}')
    print(data3)
except Exception as e:
    print(f'ERROR: {e}\n')

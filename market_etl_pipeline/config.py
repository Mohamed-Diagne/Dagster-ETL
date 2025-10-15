"""
config.py - Configuration centrale du pipeline
==============================================

Ce fichier contient toutes les configurations du projet :
- Liste des tickers à tracker (52 instruments)
- Paramètres de qualité (seuils de validation)
- Settings API (retry, timeout)

Pourquoi ce fichier ?
- Centralise toute la config en un seul endroit
- Facile à modifier sans toucher au code
- Permet de changer les tickers ou seuils rapidement
"""

from datetime import datetime
from pathlib import Path

# Liste des 52 tickers à tracker (requirement: 50+ instruments)
# Diversifié : stocks, indices, ETFs, crypto
TICKERS = [
    # Tech stocks (10)
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX", "AMD", "INTC",
    # Finance (10)
    "JPM", "BAC", "GS", "MS", "WFC", "C", "BLK", "V", "MA", "AXP",
    # Healthcare (10)
    "JNJ", "UNH", "PFE", "ABBV", "TMO", "MRK", "LLY", "ABT", "DHR", "BMY",
    # Consumer (10)
    "WMT", "PG", "KO", "PEP", "NKE", "COST", "HD", "MCD", "SBUX", "DIS",
    # Energy (5)
    "XOM", "CVX", "COP", "SLB", "EOG",
    # Indices & ETFs (5)
    "SPY", "QQQ", "DIA", "IWM", "VTI",
    # Crypto (2)
    "BTC-USD", "ETH-USD",
]

# Dossier où sauver les PDFs générés
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)  # Créé automatiquement si n'existe pas

# Seuils de validation qualité (BONUS requirement)
# Utilisés par data_quality_report pour détecter problèmes
QUALITY_CHECKS = {
    "min_price": 0.01,              # Prix minimum valide (1 cent)
    "max_price": 1_000_000,         # Prix maximum valide (1M$)
    "max_return_pct": 50.0,         # Return > 50% = outlier suspect
    "min_data_completeness": 0.8,   # Minimum 80% des tickers doivent avoir des données
}

# Paramètres API yfinance (gestion des échecs)
REQUEST_TIMEOUT = 30    # Timeout requête (secondes)
MAX_RETRIES = 3         # Nombre de tentatives si échec
RETRY_DELAY = 2         # Délai entre tentatives (secondes)

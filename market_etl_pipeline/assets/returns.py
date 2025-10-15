"""
returns.py - Asset de calcul des returns
=========================================

RÔLE : Calcule les returns quotidiens à partir des prix

Ce que fait cet asset :
1. Reçoit le DataFrame de asset_prices (Dagster le passe automatiquement)
2. Utilise pandas groupby + shift pour calculer returns
3. Formule : (prix_aujourd'hui - prix_hier) / prix_hier * 100
4. Retourne DataFrame avec les returns calculés

Technique pandas clé :
- groupby('ticker') : groupe par ticker
- shift(1) : décale d'une ligne (prix précédent)
- Évite de refaire un appel API yfinance !

Dagster capabilities démontrées :
- Asset dependency (deps=["asset_prices"])
- Dagster passe automatiquement les données
- Pas besoin de gérer input/output manuellement
- Le lineage est automatique dans l'UI

Colonnes du DataFrame retourné :
- ticker, date, close, prev_close
- daily_return : différence en $
- return_pct : différence en %
"""

import pandas as pd
from dagster import asset, AssetExecutionContext, MetadataValue


@asset(group_name="analytics")
def asset_returns(context: AssetExecutionContext, asset_prices: pd.DataFrame) -> pd.DataFrame:
    """
    Asset 2/5 : Calcule les returns quotidiens
    
    Input : asset_prices DataFrame (passé automatiquement par Dagster)
    Output : DataFrame avec returns calculés
    
    Dagster capabilities démontrées :
    - Dependency injection : Dagster passe asset_prices automatiquement
    - Lineage tracking : le lien prices → returns est visible dans l'UI
    - Data transformation pipeline
    """
    
    context.log.info("Calculating returns")
    
    # Étape 1 : Trier par ticker et date (important pour shift)
    df = asset_prices.sort_values(['ticker', 'date']).copy()
    
    # Étape 2 : Calculer prix précédent pour chaque ticker
    # groupby('ticker') : traite chaque ticker séparément
    # shift(1) : décale d'une ligne = prix du jour précédent
    df['prev_close'] = df.groupby('ticker')['close'].shift(1)
    
    # Étape 3 : Enlever les premières lignes (pas de prev_close)
    # Chaque ticker perd sa première ligne (pas de prix précédent)
    df = df.dropna(subset=['prev_close'])
    
    # Étape 4 : Calculer returns
    df['daily_return'] = df['close'] - df['prev_close']  # En dollars
    df['return_pct'] = (df['daily_return'] / df['prev_close']) * 100  # En %
    
    # Colonnes finales
    result = df[['ticker', 'date', 'close', 'prev_close', 'daily_return', 'return_pct']].copy()
    
    # Stats pour metadata
    avg_return = result['return_pct'].mean()
    top_gainers = result.nlargest(5, 'return_pct')[['ticker', 'return_pct']]
    
    context.log.info(f"Calculated {len(result)} returns. Avg: {avg_return:.2f}%")
    
    # Metadata Dagster : stats visibles dans UI
    context.add_output_metadata({
        "num_records": len(result),
        "avg_return_pct": float(round(avg_return, 2)),
        "top_gainers": MetadataValue.text(top_gainers.to_csv(index=False)),
        "preview": MetadataValue.text(result.head(5).to_csv(index=False)),
    })
    
    # Retourne le DataFrame - utilisé par data_quality_report et market_recap_pdf
    return result

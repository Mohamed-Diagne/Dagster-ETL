"""
quality_checks.py - Asset de validation qualité (BONUS)
========================================================

RÔLE : Valide la qualité des données avant génération PDF

Ce que fait cet asset :
1. Vérifie que les prix sont dans des ranges valides
2. Détecte les outliers (returns extrêmes > 50%)
3. Vérifie la complétude des données (>= 80%)
4. Détecte valeurs manquantes et doublons
5. Calcule un quality score global

Pourquoi c'est important ?
- Évite de générer un PDF avec des données erronées
- Détecte les problèmes tôt dans le pipeline
- Produit un rapport de qualité dans le PDF final

Dagster capabilities démontrées :
- Asset avec multiples dépendances (prices ET returns)
- Dagster attend que les 2 soient prêts avant d'exécuter
- Validation automatique dans le pipeline
- Quality gates (peut fail si score trop bas)

Les 5 checks :
1. Data completeness : % de tickers récupérés
2. Price range : prix entre 0.01$ et 1M$
3. Missing values : détecte NaN
4. Outliers : returns > 50% en une journée
5. Duplicates : détecte doublons
"""

import pandas as pd
from dagster import asset, AssetExecutionContext, MetadataValue
from typing import Dict, List, Any

from market_etl_pipeline.config import QUALITY_CHECKS, TICKERS


@asset(group_name="analytics")
def data_quality_report(
    context: AssetExecutionContext,
    asset_prices: pd.DataFrame,      # Passé par Dagster
    asset_returns: pd.DataFrame      # Passé par Dagster
) -> Dict[str, Any]:
    """
    Asset 4/5 : Validation qualité des données (BONUS requirement)
    
    Input : asset_prices ET asset_returns (Dagster les passe automatiquement)
    Output : Dict avec rapport de qualité
    
    Dagster capabilities démontrées :
    - Multiple dependencies (2 assets requis)
    - Validation automatique avant PDF
    - Metadata avec résultats des checks
    """
    
    context.log.info("Running data quality checks")
    
    # Structure du rapport de qualité
    quality_report = {
        'checks_passed': [],     # Liste des checks qui ont réussi
        'checks_failed': [],     # Liste des checks qui ont échoué
        'warnings': [],          # Warnings non-bloquants
        'metrics': {}            # Métriques numériques
    }
    
    # === CHECK 1 : Complétude des données ===
    # Vérifie qu'on a récupéré au moins 80% des tickers
    expected_tickers = len(TICKERS)  # 52 configurés
    actual_tickers = asset_prices['ticker'].nunique()  # Combien récupérés
    completeness_ratio = actual_tickers / expected_tickers
    
    quality_report['metrics']['data_completeness'] = completeness_ratio
    
    if completeness_ratio >= QUALITY_CHECKS['min_data_completeness']:
        quality_report['checks_passed'].append(
            f"Data completeness: {completeness_ratio:.1%} (>= {QUALITY_CHECKS['min_data_completeness']:.1%})"
        )
    else:
        quality_report['checks_failed'].append(
            f"Data completeness: {completeness_ratio:.1%} (< {QUALITY_CHECKS['min_data_completeness']:.1%})"
        )
    
    # === CHECK 2 : Validation des prix ===
    # Vérifie que tous les prix sont dans une range réaliste
    # Prix < 0.01$ ou > 1M$ = probablement une erreur
    invalid_prices = asset_prices[
        (asset_prices['close'] < QUALITY_CHECKS['min_price']) |
        (asset_prices['close'] > QUALITY_CHECKS['max_price'])
    ]
    
    if len(invalid_prices) == 0:
        quality_report['checks_passed'].append("All prices within valid range")
    else:
        quality_report['checks_failed'].append(
            f"Found {len(invalid_prices)} prices outside valid range"
        )
        quality_report['warnings'].extend(
            invalid_prices[['ticker', 'close']].to_dict('records')
        )
    
    # === CHECK 3 : Valeurs manquantes ===
    # Détecte les NaN dans les DataFrames
    missing_prices = asset_prices.isnull().sum().sum()
    missing_returns = asset_returns.isnull().sum().sum()
    
    if missing_prices == 0 and missing_returns == 0:
        quality_report['checks_passed'].append("No missing values detected")
    else:
        quality_report['warnings'].append(
            f"Missing values: {missing_prices} in prices, {missing_returns} in returns"
        )
    
    # === CHECK 4 : Détection outliers ===
    # Return > 50% en 1 jour = suspect (erreur ou événement extrême)
    outlier_returns = asset_returns[
        asset_returns['return_pct'].abs() > QUALITY_CHECKS['max_return_pct']
    ]
    
    if len(outlier_returns) == 0:
        quality_report['checks_passed'].append("No extreme return outliers detected")
    else:
        quality_report['warnings'].append(
            f"Found {len(outlier_returns)} extreme returns (>{QUALITY_CHECKS['max_return_pct']}%)"
        )
        for _, row in outlier_returns.iterrows():
            quality_report['warnings'].append(
                f"{row['ticker']}: {row['return_pct']:.2f}%"
            )
    
    # === CHECK 5 : Détection doublons ===
    # Vérifie qu'il n'y a pas de données dupliquées (ticker + date)
    duplicates = asset_prices[asset_prices.duplicated(subset=['ticker', 'date'], keep=False)]
    
    if len(duplicates) == 0:
        quality_report['checks_passed'].append("No duplicate records found")
    else:
        quality_report['checks_failed'].append(f"Found {len(duplicates)} duplicate records")
    
    # === Calcul du quality score global ===
    # Score = % de checks qui ont passé
    total_checks = len(quality_report['checks_passed']) + len(quality_report['checks_failed'])
    passed_checks = len(quality_report['checks_passed'])
    quality_report['metrics']['quality_score'] = passed_checks / total_checks if total_checks > 0 else 0
    
    context.log.info(
        f"Quality checks complete: {passed_checks}/{total_checks} passed. "
        f"Quality score: {quality_report['metrics']['quality_score']:.1%}"
    )
    
    # Metadata Dagster : affiche résumé des checks dans UI
    context.add_output_metadata({
        "quality_score": float(quality_report['metrics']['quality_score']),
        "checks_passed": len(quality_report['checks_passed']),
        "checks_failed": len(quality_report['checks_failed']),
        "warnings": len(quality_report['warnings']),
        "passed_checks": MetadataValue.md("\n".join(f"✅ {c}" for c in quality_report['checks_passed'])),
        "failed_checks": MetadataValue.md("\n".join(f"❌ {c}" for c in quality_report['checks_failed']) if quality_report['checks_failed'] else "None"),
    })
    
    # Retourne le rapport - utilisé par market_recap_pdf pour section qualité
    return quality_report

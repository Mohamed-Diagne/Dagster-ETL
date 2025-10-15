"""
definitions.py - Point d'entrée Dagster
========================================

Ce fichier est le CŒUR de l'orchestration Dagster.
Il charge tous les assets et les déclare à Dagster.

Comment Dagster l'utilise :
1. Dagster lit ce fichier au démarrage (via pyproject.toml)
2. Il trouve l'objet 'defs' (Definitions)
3. Il charge tous les assets et comprend leurs dépendances
4. Il crée automatiquement le lineage graph.

Workflow :
- `load_assets_from_modules` : Charge tous les @asset des fichiers Python
- `Definitions` : Déclare à Dagster quels assets existent
- Dagster détecte les dépendances automatiquement (via deps=[...] ou les arguments de fonction)
"""

from dagster import Definitions, load_assets_from_modules

# Import des modules contenant les assets
from market_etl_pipeline.assets import news, prices, returns, quality_checks, pdf_report

# Liste des modules à charger (ordre logique du pipeline)
modules_to_load = [
    news,            # asset_news : collecte d'actualités
    prices,          # asset_prices : récupération des prix
    returns,         # asset_returns : calcul des rendements
    quality_checks,  # asset_quality_checks : vérifications de qualité
    pdf_report       # asset_pdf_report : génération du rapport final
]

# Chargement automatique des assets
all_assets = load_assets_from_modules(modules_to_load)

# Définition principale du pipeline Dagster
defs = Definitions(
    assets=all_assets
)

# Dagster va automatiquement :
# 1. Créer le graphe : news → prices → returns → quality_checks → pdf_report
# 2. Déterminer l'ordre d'exécution optimal
# 3. Gérer le passage des données entre les assets
# 4. Afficher tout le pipeline dans l'interface (http://localhost:3000)

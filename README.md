# Market ETL Pipeline - Dagster Demo

Pipeline ETL qui démontre les **capacités de Dagster** : asset management, lineage tracking, et orchestration de données financières.

## 🎯 Objectif

Démontrer la maîtrise de **Dagster** pour :
- Gérer des **assets** avec dépendances automatiques
- Tracker le **lineage** (traçabilité des données)
- Orchestrer un pipeline ETL réel
- Intégrer des APIs externes (Yahoo Finance, Google News RSS)

## 🚀 Installation & Lancement

```bash
# Cloner le repo
git clone https://github.com/Mohamed-Diagne/Dagster-ETL.git
cd Dagster-ETL

# Créer environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Installer dépendances
pip install -r requirements.txt

# Lancer Dagster
./run.sh
```

Ouvrir **http://localhost:3000** → Cliquer **"Materialize all"**

Le PDF sera généré dans `outputs/market_recap_YYYYMMDD.pdf`

## 📊 Les 5 Assets Dagster

Dagster gère automatiquement les dépendances entre assets :

```
┌─────────────┐     ┌──────────────┐
│asset_prices │     │ asset_news   │
│(Yahoo API)  │     │(Google RSS)  │
└──────┬──────┘     └──────┬───────┘
       │                   │
       ├───────────────────┘
       │
       ▼
┌──────────────┐
│asset_returns │
│(calcul %)    │
└──────┬───────┘
       │
       ▼
┌───────────────────┐
│data_quality_report│
│(validations)      │
└──────┬────────────┘
       │
       ▼
┌──────────────────┐
│market_recap_pdf  │
└─────────┬────────┘
          │
          ▼
    outputs/*.pdf
```

### 1. asset_prices
- **Source** : Yahoo Finance API REST (directe)
- **Action** : Récupère 2 jours de prix OHLCV pour 52 tickers
- **Output** : DataFrame(ticker, date, open, high, low, close, volume)
- **Technique** : Appels séquentiels avec délai 1s pour éviter rate limiting

### 2. asset_news
- **Source** : Google News RSS feeds
- **Action** : Récupère 3 news par ticker via RSS
- **Output** : DataFrame(ticker, title, publisher, link, published_date)
- **Technique** : Parsing XML avec BeautifulSoup

### 3. asset_returns
- **Dépend de** : asset_prices
- **Action** : Calcule returns quotidiens avec `groupby` + `shift`
- **Formule** : `(close - prev_close) / prev_close * 100`
- **Output** : DataFrame(ticker, date, close, prev_close, daily_return, return_pct)

### 4. data_quality_report
- **Dépend de** : asset_prices, asset_returns
- **Action** : 5 validations automatiques
  1. Complétude (>= 80%)
  2. Prix valides ($0.01 - $1M)
  3. Outliers (returns > 50%)
  4. Valeurs manquantes
  5. Doublons
- **Output** : Dict avec quality_score et checks

### 5. market_recap_pdf
- **Dépend de** : TOUS les assets
- **Action** : Génère PDF professionnel avec ReportLab
- **Output** : PDF dans `outputs/market_recap_YYYYMMDD.pdf`

## 📄 Contenu du PDF

Le PDF généré contient :

1. ✅ **Executive Summary** - Statistiques du jour (nb assets, avg return, gainers/losers)
2. ✅ **Chart Top 5 Performers** - Graphique bar chart (matplotlib)
3. ✅ **Table TOUS les assets** - Prix et returns pour les 52 tickers
4. ✅ **News du jour** - 1 article par ticker avec liens cliquables
5. ✅ **Quality Report** - Score de qualité + checks passés/échoués

## 🎨 Architecture Dagster

### Comment ça fonctionne

```
./run.sh
   ↓
lance dagster dev
   ↓
lit workspace.yaml → pointe vers definitions.py
   ↓
definitions.py charge tous les @asset
   ↓
Dagster construit le graph de dépendances
   ↓
UI disponible sur localhost:3000
```

### Fichiers clés

```
market_etl_pipeline/
├── __init__.py            # Rend le package importable
├── config.py              # Configuration (52 tickers, seuils)
├── definitions.py         # Point d'entrée Dagster
└── assets/
    ├── __init__.py        # Rend assets/ importable
    ├── prices.py          # Fetch prix via Yahoo API
    ├── news.py            # Fetch news via Google RSS
    ├── returns.py         # Calcul returns
    ├── quality_checks.py  # Validations qualité
    └── pdf_report.py      # Génération PDF

outputs/                   # PDFs générés
.venv/                     # Environnement Python
workspace.yaml             # Config Dagster
pyproject.toml             # Metadata projet
requirements.txt           # Dépendances
run.sh                     # Script de lancement
```

### Passage de données entre assets

Dagster passe automatiquement les données :

```python
# prices.py
@asset
def asset_prices(context) -> pd.DataFrame:
    return DataFrame  # Dagster stocke ça

# returns.py
@asset
def asset_returns(asset_prices: pd.DataFrame) -> pd.DataFrame:
    # asset_prices est automatiquement passé par Dagster!
    return calculate_returns(asset_prices)
```

## 🎨 Ce que Dagster apporte

### 1. Asset Management
Chaque asset est une fonction Python qui produit des données réutilisables.

### 2. Lineage Tracking
Dagster trace automatiquement les dépendances et affiche le graph dans l'UI.

### 3. Metadata & Observability
Chaque asset expose des métadonnées visibles dans l'UI :
```python
context.add_output_metadata({
    "num_records": len(df),
    "preview": MetadataValue.text(df.head().to_csv())
})
```

### 4. UI Visualization
L'interface Dagster montre :
- **Lineage graph** : dépendances visuelles entre assets
- **Metadata** : preview des données de chaque asset
- **Logs** : exécution en temps réel
- **Run history** : historique des exécutions

## ⚙️ Configuration

Modifier `market_etl_pipeline/config.py` :
- `TICKERS` : Liste des 52 tickers trackés
- `QUALITY_CHECKS` : Seuils de validation
- `MAX_RETRIES` / `RETRY_DELAY` : Paramètres de resilience

## 🔧 Gestion des erreurs

- **API rate limiting** : Délais séquentiels (1s entre requêtes)
- **Tickers échoués** : Pipeline continue avec les données disponibles
- **News manquantes** : DataFrame vide accepté
- **Quality gates** : Validation avant génération PDF

## 📦 Dépendances principales

- `dagster` - Orchestration
- `pandas` - Manipulation données
- `requests` - API calls
- `beautifulsoup4` - Parsing RSS
- `matplotlib` - Génération charts
- `reportlab` - Génération PDF



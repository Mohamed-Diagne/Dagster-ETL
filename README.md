# Market ETL Pipeline - Dagster Demo

Pipeline ETL qui démontre les **capacités de Dagster** : asset management, lineage tracking, et orchestration de données financières.

## 🎯 Objectif

Démontrer la maîtrise de **Dagster** pour :
- Gérer des **assets** avec dépendances automatiques
- Tracker le **lineage** (traçabilité des données)
- Orchestrer un pipeline ETL réel
- Intégrer des librairies externes (yfinance)

## 🚀 Installation & Lancement

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
dagster dev
```

Ouvrir **http://localhost:3000** → Cliquer **"Materialize all"**

## 📊 Les 5 Assets Dagster

Dagster gère automatiquement les dépendances entre assets :

```
┌─────────────┐     ┌──────────────┐
│asset_prices │     │ asset_news   │
│(52 tickers) │     │(via yfinance)│
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
│data_quality_report│ (BONUS)
│(5 validations)    │
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
- **Source** : yfinance API
- **Action** : Récupère 2 jours de prix OHLCV pour 52 tickers
- **Output** : DataFrame(ticker, date, open, high, low, close, volume)
- **Error handling** : Retry 3x avec délai 2s

### 2. asset_news
- **Source** : yfinance API
- **Action** : Récupère news pour 15 tickers
- **Output** : DataFrame(ticker, title, publisher, link, published_date)

### 3. asset_returns
- **Dépend de** : asset_prices
- **Action** : Calcule returns quotidiens avec `groupby` + `shift`
- **Formule** : `(close - prev_close) / prev_close * 100`
- **Output** : DataFrame(ticker, date, close, prev_close, daily_return, return_pct)

### 4. data_quality_report (BONUS)
- **Dépend de** : asset_prices, asset_returns
- **Action** : 5 validations automatiques
  1. Complétude (>= 80%)
  2. Prix valides ($0.01 - $1M)
  3. Outliers (returns > 50%)
  4. Valeurs manquantes
  5. Doublons
- **Output** : Dict avec quality_score

### 5. market_recap_pdf
- **Dépend de** : TOUS les assets
- **Action** : Génère PDF professionnel
- **Output** : PDF dans `outputs/market_recap_YYYYMMDD.pdf`

## 📄 Contenu du PDF

Le PDF généré contient (requirements satisfaits) :

1. ✅ **Executive Summary** - Résumé du jour
2. ✅ **Chart Top 5 Performers** - Graphique bar chart
3. ✅ **Table TOUS les assets** - Prix et returns pour les 52 tickers
4. ✅ **News du jour** - Articles avec liens cliquables
5. ✅ **Quality Report** - Score de qualité (BONUS)

## 🎨 Ce que Dagster apporte

### 1. Asset Management
Chaque asset est une fonction Python qui produit des données :
```python
@asset
def asset_prices(context):
    # Récupère les prix
    return dataframe
```

### 2. Lineage Tracking
Dagster trace automatiquement les dépendances :
```python
@asset(deps=["asset_prices"])
def asset_returns(asset_prices: pd.DataFrame):
    # Dagster passe automatiquement les données
    return calculate_returns(asset_prices)
```

### 3. Metadata & Observability
Chaque asset peut exposer des métadonnées :
```python
context.add_output_metadata({
    "num_records": len(df),
    "preview": MetadataValue.md(df.head().to_markdown())
})
```

### 4. UI Visualization
L'interface Dagster montre :
- **Lineage graph** : dépendances visuelles
- **Metadata** : preview des données
- **Logs** : exécution en temps réel
- **Run history** : historique

## 🧪 Tests

```bash
pytest tests/ -v
```

Valide :
- Calculs des returns (positifs, négatifs, zéro)
- Seuils quality checks
- Edge cases

## 📁 Structure

```
market_etl_pipeline/
├── config.py              # 52 tickers + paramètres
├── definitions.py         # Définitions Dagster
└── assets/
    ├── prices.py          # Fetch prix (retry logic)
    ├── news.py            # Fetch news (yfinance)
    ├── returns.py         # Calcul returns (groupby+shift)
    ├── quality_checks.py  # 5 validations (BONUS)
    └── pdf_report.py      # Génération PDF

tests/
├── test_returns.py        # Tests calculs
└── test_quality_checks.py # Tests validations
```

## ⚙️ Configuration

Modifier `market_etl_pipeline/config.py` :
- `TICKERS` : ajouter/retirer des tickers
- `QUALITY_CHECKS` : ajuster les seuils
- `MAX_RETRIES` / `RETRY_DELAY` : tuner resilience

## 🎤 Pour l'Interview

### Points clés Dagster à expliquer :

**1. Asset-based paradigm**
> "Dagster utilise des assets au lieu de tasks. Chaque asset produit des données réutilisables. C'est plus intuitif que les DAGs traditionnels."

**2. Automatic dependency resolution**
> "Je définis juste `deps=['asset_prices']` et Dagster passe automatiquement les données. Pas besoin de gérer manuellement les inputs/outputs."

**3. Lineage tracking**
> "Dans l'UI, on voit clairement que returns dépend de prices, le PDF dépend de tout. C'est automatique, pas de code supplémentaire."

**4. Metadata & observability**
> "Chaque asset expose des métriques : nombre de lignes, preview, quality score. On voit tout dans l'UI sans logger manuellement."

**5. Error resilience**
> "J'ai ajouté retry logic (3 tentatives) et graceful degradation. Si un ticker échoue, le pipeline continue avec les autres."

**6. Data quality (BONUS)**
> "Le `data_quality_report` asset valide automatiquement la qualité avant génération PDF. Score de 100% aujourd'hui."

### Flow à expliquer :

> "Le pipeline récupère les prix de 52 instruments via yfinance, calcule les returns avec un shift pandas, valide la qualité, récupère les news, puis génère un PDF avec charts et tables. Dagster orchestre tout et trace les dépendances automatiquement."

## 🔧 Error Handling

- **API failures** : Retry 3x avec 2s de délai
- **Missing data** : Continue avec données disponibles
- **Quality gates** : Valide avant PDF

## ✅ Requirements Coverage

| Requirement | Status |
|------------|--------|
| 50+ instruments | ✅ 52 tickers |
| Daily prices (yfinance) | ✅ asset_prices |
| News collection | ✅ asset_news |
| Returns calculation | ✅ asset_returns |
| PDF with table | ✅ TOUS les assets |
| PDF with chart | ✅ Top 5 performers |
| PDF with news | ✅ Avec liens cliquables |
| Dagster orchestration | ✅ 5 assets |
| Lineage tracking | ✅ Dependencies graph |
| Error handling | ✅ Retry + logs |
| Tests | ✅ pytest tests/ |
| Dagster UI | ✅ Visualization |
| **BONUS: Quality checks** | ✅ data_quality_report |
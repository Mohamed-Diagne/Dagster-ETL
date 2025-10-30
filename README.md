# Market ETL Pipeline - Dagster Demo

ETL pipeline showcasing **Dagster’s capabilities**: asset management, lineage tracking, and orchestration of financial data.

## 🎯 Objective

Demonstrate proficiency with **Dagster** to:

* Manage **assets** with automatic dependencies
* Track **data lineage** and traceability
* Orchestrate a real-world ETL pipeline
* Integrate external APIs (Yahoo Finance, Google News RSS)

## 🚀 Installation & Launch

```bash
# Clone the repository
git clone https://github.com/Mohamed-Diagne/Dagster-ETL.git
cd Dagster-ETL

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch Dagster
./run.sh
```

Open **[http://localhost:3000](http://localhost:3000)** → Click **"Materialize all"**

A PDF report will be generated in `outputs/market_recap_YYYYMMDD.pdf`

## 📊 The 5 Dagster Assets

Dagster automatically manages dependencies between assets:

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
│(returns %)   │
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

* **Source**: Yahoo Finance REST API
* **Action**: Fetches 2 days of OHLCV prices for 52 tickers
* **Output**: DataFrame(ticker, date, open, high, low, close, volume)
* **Technique**: Sequential API calls with 1s delay to avoid rate limiting

### 2. asset_news

* **Source**: Google News RSS feeds
* **Action**: Retrieves 3 news articles per ticker via RSS
* **Output**: DataFrame(ticker, title, publisher, link, published_date)
* **Technique**: XML parsing using BeautifulSoup

### 3. asset_returns

* **Depends on**: asset_prices
* **Action**: Computes daily returns using `groupby` + `shift`
* **Formula**: `(close - prev_close) / prev_close * 100`
* **Output**: DataFrame(ticker, date, close, prev_close, daily_return, return_pct)

### 4. data_quality_report

* **Depends on**: asset_prices, asset_returns
* **Action**: Performs 5 automatic data validations

  1. Completeness (≥ 80%)
  2. Valid price range ($0.01 – $1M)
  3. Outliers (returns > 50%)
  4. Missing values
  5. Duplicates
* **Output**: Dict with quality_score and check results

### 5. market_recap_pdf

* **Depends on**: All previous assets
* **Action**: Generates a professional PDF report using ReportLab
* **Output**: PDF saved as `outputs/market_recap_YYYYMMDD.pdf`

## 📄 PDF Contents

The generated PDF includes:

1. ✅ **Executive Summary** – Daily statistics (asset count, avg return, gainers/losers)
2. ✅ **Top 5 Performers Chart** – Bar chart (matplotlib)
3. ✅ **All Assets Table** – Prices and returns for 52 tickers
4. ✅ **Daily News** – 1 clickable article per ticker
5. ✅ **Quality Report** – Overall score + passed/failed checks

## 🎨 Dagster Architecture

### How It Works

```
./run.sh
   ↓
launches dagster dev
   ↓
reads workspace.yaml → points to definitions.py
   ↓
definitions.py loads all @asset functions
   ↓
Dagster builds the dependency graph
   ↓
UI available at localhost:3000
```

### Key Files

```
market_etl_pipeline/
├── __init__.py            # Makes the package importable
├── config.py              # Configuration (52 tickers, thresholds)
├── definitions.py         # Dagster entry point
└── assets/
    ├── __init__.py        # Makes assets/ importable
    ├── prices.py          # Fetch prices via Yahoo API
    ├── news.py            # Fetch news via Google RSS
    ├── returns.py         # Compute returns
    ├── quality_checks.py  # Perform data validations
    └── pdf_report.py      # Generate PDF report

outputs/                   # Generated PDFs  
.venv/                     # Python virtual environment  
workspace.yaml             # Dagster config  
pyproject.toml             # Project metadata  
requirements.txt           # Dependencies  
run.sh                     # Launch script  
```

### Data Passing Between Assets

Dagster automatically handles data transfer between assets:

```python
# prices.py
@asset
def asset_prices(context) -> pd.DataFrame:
    return df  # Dagster stores this output

# returns.py
@asset
def asset_returns(asset_prices: pd.DataFrame) -> pd.DataFrame:
    # asset_prices is automatically passed by Dagster!
    return calculate_returns(asset_prices)
```

## 🎨 What Dagster Brings

### 1. Asset Management

Each asset is a Python function producing reusable, trackable data.

### 2. Lineage Tracking

Dagster automatically visualizes dependencies between assets in its UI.

### 3. Metadata & Observability

Each asset can log custom metadata for UI inspection:

```python
context.add_output_metadata({
    "num_records": len(df),
    "preview": MetadataValue.text(df.head().to_csv())
})
```

### 4. UI Visualization

Dagster’s interface displays:

* **Lineage graph** – visual dependencies
* **Metadata** – preview of each asset’s data
* **Logs** – real-time execution details
* **Run history** – record of all pipeline runs

## ⚙️ Configuration

Edit `market_etl_pipeline/config.py`:

* `TICKERS`: list of 52 tracked tickers
* `QUALITY_CHECKS`: validation thresholds
* `MAX_RETRIES` / `RETRY_DELAY`: resilience parameters

## 🔧 Error Handling

* **API rate limiting**: sequential requests with 1s delay
* **Failed tickers**: pipeline continues with available data
* **Missing news**: empty DataFrame accepted
* **Quality gates**: validation performed before PDF generation

## 📦 Main Dependencies

* `dagster` – Orchestration
* `pandas` – Data manipulation
* `requests` – API calls
* `beautifulsoup4` – RSS parsing
* `matplotlib` – Chart generation
* `reportlab` – PDF report generation

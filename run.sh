#!/bin/bash
# Script de lancement simple du pipeline Dagster

cd "/Users/mohameddiagne/Desktop/ETL Challenge"
source .venv/bin/activate
export MPLBACKEND=Agg

echo "🚀 Lancement de Dagster..."
echo "📊 Interface: http://localhost:3000"
dagster dev

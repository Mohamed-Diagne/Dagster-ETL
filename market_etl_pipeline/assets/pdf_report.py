"""
pdf_report.py - Asset de génération PDF
========================================

RÔLE : Asset final - génère le rapport PDF quotidien

Ce que fait cet asset :
1. Reçoit TOUS les autres assets (prices, returns, news, quality)
2. Crée un chart matplotlib des top 5 performers
3. Génère un PDF professionnel avec ReportLab
4. Sauvegarde dans outputs/market_recap_YYYYMMDD.pdf

Contenu du PDF (requirements) :
- Page 1 : Executive summary + chart top 5
- Pages suivantes : Table complète prix/returns pour TOUS les assets
- Dernières pages : News du jour + quality report

Dagster capabilities démontrées :
- Asset avec 4 dépendances (attend tous les autres)
- Dagster passe automatiquement les 4 DataFrames/Dicts
- Lineage complet visible dans UI
- Metadata avec chemin du PDF généré

Libraries utilisées :
- matplotlib : génération du chart
- reportlab : génération PDF (tables, paragraphes, images)
"""

import pandas as pd
import numpy as np
from dagster import asset, AssetExecutionContext, MetadataValue
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Mode non-interactif (pas de fenêtre)
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

from market_etl_pipeline.config import OUTPUT_DIR


@asset(group_name="reporting")
def market_recap_pdf(
    context: AssetExecutionContext,
    asset_prices: pd.DataFrame,       # Passé par Dagster
    asset_returns: pd.DataFrame,      # Passé par Dagster
    asset_news: pd.DataFrame,         # Passé par Dagster
    data_quality_report: dict         # Passé par Dagster
) -> str:
    """
    Asset 5/5 : Génère le PDF final du market recap
    
    Input : Les 4 autres assets (Dagster les passe automatiquement)
    Output : Chemin du PDF généré
    
    Dagster capabilities démontrées :
    - Asset final avec toutes les dépendances
    - Dagster attend que TOUT soit prêt avant d'exécuter
    - Aggregation de multiples sources de données
    - Génération d'artifact final (PDF)
    """
    
    context.log.info("Generating market recap PDF")
    
    # Create filename with timestamp
    date_str = datetime.now().strftime("%Y%m%d")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_filename = OUTPUT_DIR / f"market_recap_{date_str}.pdf"
    
    # Create PDF document
    doc = SimpleDocTemplate(
        str(pdf_filename),
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )
    
    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    title = Paragraph(f"Daily Market Recap - {datetime.now().strftime('%B %d, %Y')}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Executive Summary
    elements.append(Paragraph("Executive Summary", heading_style))
    
    num_assets = asset_returns['ticker'].nunique()
    avg_return = asset_returns['return_pct'].dropna().mean()
    num_gainers = (asset_returns['return_pct'] > 0).sum()
    num_losers = (asset_returns['return_pct'] < 0).sum()
    
    summary_text = f"""
    <b>Market Overview:</b><br/>
    • Total Assets Tracked: {len(asset_returns)}<br/>
    • Average Return: {avg_return:.2f}%<br/>
    • Gainers: {num_gainers} | Losers: {num_losers}<br/>
    • Data Quality Score: {data_quality_report['metrics']['quality_score']:.1%}<br/>
    """
    
    elements.append(Paragraph(summary_text, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Top 5 Performers Chart
    context.log.info("Creating top performers chart")
    top_5 = asset_returns.nlargest(5, 'return_pct')[['ticker', 'return_pct']]
    
    fig, ax = plt.subplots(figsize=(8, 4))
    colors_bar = ['green' if x > 0 else 'red' for x in top_5['return_pct']]
    ax.barh(top_5['ticker'], top_5['return_pct'], color=colors_bar)
    ax.set_xlabel('Return (%)')
    ax.set_title('Top 5 Performers of the Day')
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    plt.tight_layout()
    
    # Save chart to buffer
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()
    
    # Add chart to PDF
    elements.append(Paragraph("Top 5 Performers", heading_style))
    img = Image(img_buffer, width=6*inch, height=3*inch)
    elements.append(img)
    elements.append(Spacer(1, 0.3*inch))
    
    # Price & Returns Table (ALL assets as required)
    elements.append(Paragraph("Daily Prices & Returns (All Assets)", heading_style))
    
    table_data = [['Ticker', 'Close Price', 'Daily Return', 'Return %']]
    
    for _, row in asset_returns.sort_values('return_pct', ascending=False).iterrows():
        table_data.append([
            row['ticker'],
            f"${row['close']:.2f}",
            f"${row['daily_return']:.2f}",
            f"{row['return_pct']:.2f}%"
        ])
    
    table = Table(table_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    elements.append(table)
    elements.append(PageBreak())
    
    # Market News Section
    elements.append(Paragraph("Key News of the Day", heading_style))
    
    # 1 news par ticker
    news_per_ticker = asset_news.groupby('ticker').first().reset_index()
    
    for idx, (_, news) in enumerate(news_per_ticker.iterrows(), 1):
        has_link = pd.notna(news.get('link')) and news.get('link')
        link_html = f' <link href="{news["link"]}">Read more</link>' if has_link else ""
        
        news_text = f"""
        <b>{idx}. [{news['ticker']}] {news['title']}</b><br/>
        <i>{news['publisher']} - {news['published_date']}</i>{link_html}<br/>
        """
        elements.append(Paragraph(news_text, styles['Normal']))
        elements.append(Spacer(1, 0.15*inch))
    
    # Data Quality Section
    elements.append(PageBreak())
    elements.append(Paragraph("Data Quality Report", heading_style))
    
    quality_text = f"""
    <b>Quality Score: {data_quality_report['metrics']['quality_score']:.1%}</b><br/><br/>
    <b>Checks Passed ({len(data_quality_report['checks_passed'])}):</b><br/>
    """
    
    for check in data_quality_report['checks_passed']:
        quality_text += f"✓ {check}<br/>"
    
    if data_quality_report['checks_failed']:
        quality_text += f"<br/><b>Checks Failed ({len(data_quality_report['checks_failed'])}):</b><br/>"
        for check in data_quality_report['checks_failed']:
            quality_text += f"✗ {check}<br/>"
    
    elements.append(Paragraph(quality_text, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    
    context.log.info(f"PDF generated successfully: {pdf_filename}")
    
    context.add_output_metadata({
        "pdf_path": str(pdf_filename),
        "file_size_kb": round(pdf_filename.stat().st_size / 1024, 2),
        "num_pages": "~3-4",
        "preview": MetadataValue.md(f"PDF saved to: `{pdf_filename}`"),
    })
    
    return str(pdf_filename)

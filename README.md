# Equity Market Surveillance & Regulatory Compliance Analytics

Python · SQL · Dashboard (Streamlit) · Power BI-ready exports

Monitors NSE/BSE equities for abnormal price-volume behaviour, liquidity stress and volatility
regimes, using market data from **yfinance**. Surveillance indicators and alert rules are written in
**SQL** (window functions on SQLite); a web dashboard sits on top, and CSV exports feed a Power BI report.

> Alerts are statistical screens for analyst review. They are not findings of manipulation or non-compliance.

## What it does
| Layer | File | Purpose |
|---|---|---|
| Ingest | `surveillance/ingest.py` | yfinance OHLCV for ~24 NSE large/mid caps, 5 BSE dual listings, Nifty 50 benchmark |
| SQL indicators | `surveillance/sql/02_indicators.sql` | returns, gaps, 20-day volume ratio, price/volume z-scores, rolling volatility, Amihud illiquidity, excess return vs Nifty |
| SQL alerts | `surveillance/sql/03_alerts.sql` | `PRICE_SPIKE`, `VOLUME_SPIKE`, `PRICE_VOLUME`, `GAP`, `LIQUIDITY_DRY` + severity score (thresholds are parameters) |
| SQL cross-venue | `surveillance/sql/04_exchange_spread.sql` | NSE-vs-BSE close spread (bps) and volume share |
| Dashboard | `app/dashboard.py` | Overview, Price & Volume, Volatility & Liquidity, Alerts, NSE vs BSE, Method |
| Power BI | `surveillance/export.py` | `indicators.csv`, `alerts.csv`, `exchange_spread.csv`, `securities.csv` |

## Quick start
```bash
git clone https://github.com/<your-username>/equity-market-surveillance.git
cd equity-market-surveillance
pip install -r requirements.txt
python -m surveillance.cli --period 1y --export   # downloads from yfinance, builds SQL tables, writes exports/
streamlit run app/dashboard.py                    # opens http://localhost:8501
```
No internet? `python -m surveillance.cli --demo` loads clearly-labelled **synthetic** data so you can try the UI.
You can also click **Fetch live** / **Demo data** inside the dashboard sidebar.

## Power BI
Open Power BI Desktop → Get Data → Text/CSV → load the four files in `exports/` → relate
`indicators.symbol`/`alerts.symbol` to `securities.symbol`. Suggested visuals: alerts by day, volatility heatmap, price/volume per symbol.

## Method (short)
- Baselines use the **prior 20 sessions**, so an anomaly never contaminates its own baseline.
- `volatility_20` = stdev of daily returns × √252. `illiquidity_20` = mean(|ret| / turnover).
- HIGH severity = price and volume breach together, or a large move on ≥2× volume.
- Customise the universe in `surveillance/config.py`; tune thresholds in the dashboard sidebar or `DEFAULT_THRESHOLDS`.

## Tests
`python -m pytest` — checks SQL indicators against pandas, alert logic, threshold monotonicity, and that the dashboard runs.

## Data & limits
yfinance is an unofficial Yahoo Finance wrapper: data may be delayed, adjusted or occasionally missing; it is not an exchange-grade feed.

## License
MIT

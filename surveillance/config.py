"""Universe and defaults. Edit UNIVERSE to monitor different securities."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "surveillance.db"
SQL_DIR = Path(__file__).resolve().parent / "sql"
BENCHMARK = "^NSEI"  # Nifty 50

# symbol: (name, sector)
UNIVERSE = {
    "RELIANCE.NS": ("Reliance Industries", "Energy"),
    "TCS.NS": ("Tata Consultancy Services", "IT"),
    "HDFCBANK.NS": ("HDFC Bank", "Financials"),
    "INFY.NS": ("Infosys", "IT"),
    "ICICIBANK.NS": ("ICICI Bank", "Financials"),
    "SBIN.NS": ("State Bank of India", "Financials"),
    "BHARTIARTL.NS": ("Bharti Airtel", "Telecom"),
    "ITC.NS": ("ITC", "FMCG"),
    "LT.NS": ("Larsen & Toubro", "Industrials"),
    "HINDUNILVR.NS": ("Hindustan Unilever", "FMCG"),
    "AXISBANK.NS": ("Axis Bank", "Financials"),
    "KOTAKBANK.NS": ("Kotak Mahindra Bank", "Financials"),
    "MARUTI.NS": ("Maruti Suzuki", "Auto"),
    "SUNPHARMA.NS": ("Sun Pharma", "Pharma"),
    "TATAMOTORS.NS": ("Tata Motors", "Auto"),
    "TATASTEEL.NS": ("Tata Steel", "Metals"),
    "ADANIENT.NS": ("Adani Enterprises", "Conglomerate"),
    "ADANIPORTS.NS": ("Adani Ports", "Industrials"),
    "WIPRO.NS": ("Wipro", "IT"),
    "ONGC.NS": ("ONGC", "Energy"),
    "ZOMATO.NS": ("Zomato", "Consumer Tech"),
    "YESBANK.NS": ("Yes Bank", "Financials"),
    "IDEA.NS": ("Vodafone Idea", "Telecom"),
    "SUZLON.NS": ("Suzlon Energy", "Industrials"),
    # BSE listings of dual-listed names, for NSE-vs-BSE comparison
    "RELIANCE.BO": ("Reliance Industries", "Energy"),
    "TCS.BO": ("Tata Consultancy Services", "IT"),
    "HDFCBANK.BO": ("HDFC Bank", "Financials"),
    "INFY.BO": ("Infosys", "IT"),
    "SBIN.BO": ("State Bank of India", "Financials"),
}

DEFAULT_THRESHOLDS = dict(price_z=3.0, vol_ratio=3.0, move_pct=0.03, gap_pct=0.03, dry_ratio=0.3)

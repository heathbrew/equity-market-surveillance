"""CSV exports so the same data can feed a Power BI report (Get Data -> Text/CSV)."""
from pathlib import Path
import pandas as pd
from .config import ROOT, DEFAULT_THRESHOLDS
from . import db


def export_csv(con, out_dir=ROOT / "exports"):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    ind = pd.read_sql_query("SELECT * FROM indicators", con)
    ind.to_csv(out / "indicators.csv", index=False)
    lo, hi = ind["date"].min(), ind["date"].max()
    db.alerts(con, lo, hi, **DEFAULT_THRESHOLDS).to_csv(out / "alerts.csv", index=False)
    db.exchange_spread(con).to_csv(out / "exchange_spread.csv", index=False)
    pd.read_sql_query("SELECT * FROM securities", con).to_csv(out / "securities.csv", index=False)
    return ["indicators.csv", "alerts.csv", "exchange_spread.csv", "securities.csv"]

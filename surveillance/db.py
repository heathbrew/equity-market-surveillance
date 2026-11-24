import sqlite3
from pathlib import Path
import pandas as pd
from .config import DB_PATH, SQL_DIR


def connect(path=DB_PATH) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(path))


def run_script(con, name: str):
    con.executescript((SQL_DIR / name).read_text())


def build_indicators(con):
    run_script(con, "01_schema.sql")
    run_script(con, "02_indicators.sql")
    con.commit()


def alerts(con, start, end, price_z=3.0, vol_ratio=3.0, move_pct=0.03, gap_pct=0.03, dry_ratio=0.3) -> pd.DataFrame:
    q = (SQL_DIR / "03_alerts.sql").read_text()
    return pd.read_sql_query(q, con, params=dict(start=str(start), end=str(end), price_z=price_z,
                             vol_ratio=vol_ratio, move_pct=move_pct, gap_pct=gap_pct, dry_ratio=dry_ratio))


def exchange_spread(con) -> pd.DataFrame:
    return pd.read_sql_query((SQL_DIR / "04_exchange_spread.sql").read_text(), con)

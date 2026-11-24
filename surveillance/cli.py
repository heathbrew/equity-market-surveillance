import argparse
from .config import UNIVERSE, BENCHMARK, DB_PATH
from . import db, ingest


def main(argv=None):
    ap = argparse.ArgumentParser(prog="surveillance", description="Equity market surveillance pipeline")
    ap.add_argument("--period", default="1y", help="yfinance period (e.g. 6mo, 1y, 2y)")
    ap.add_argument("--demo", action="store_true", help="use SYNTHETIC data (offline demo only)")
    ap.add_argument("--db", default=str(DB_PATH))
    ap.add_argument("--export", action="store_true", help="also export CSVs for Power BI -> exports/")
    a = ap.parse_args(argv)
    syms = list(UNIVERSE) + [BENCHMARK]
    prices = ingest.synthetic(syms) if a.demo else ingest.fetch_yfinance(syms, period=a.period)
    con = db.connect(a.db)
    ingest.load(con, prices, "SYNTHETIC DEMO DATA" if a.demo else "yfinance")
    db.build_indicators(con)
    n = con.execute("SELECT COUNT(*) FROM indicators").fetchone()[0]
    print(f"Loaded {len(prices):,} price rows; built {n:,} indicator rows -> {a.db}")
    if a.export:
        from .export import export_csv
        print("Exported:", ", ".join(export_csv(con)))


if __name__ == "__main__":
    main()

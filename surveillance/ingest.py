"""Load OHLCV data into SQLite from yfinance (live) or a synthetic generator (offline demo/tests)."""
import numpy as np
import pandas as pd
from .config import UNIVERSE, BENCHMARK
from .db import run_script


def _exchange(sym):
    return "INDEX" if sym.startswith("^") else ("NSE" if sym.endswith(".NS") else "BSE")


def fetch_yfinance(symbols, period="1y", start=None, end=None) -> pd.DataFrame:
    import yfinance as yf
    kw = dict(start=start, end=end) if start else dict(period=period)
    raw = yf.download(list(symbols), group_by="ticker", auto_adjust=False,
                      progress=False, threads=True, **kw)
    frames = []
    for s in symbols:
        try:
            d = raw[s].dropna(how="all").reset_index()
        except KeyError:
            continue
        if d.empty:
            continue
        d.columns = [str(c).lower().replace(" ", "_") for c in d.columns]
        d["symbol"] = s
        frames.append(d[["symbol", "date", "open", "high", "low", "close", "adj_close", "volume"]])
    if not frames:
        raise RuntimeError("yfinance returned no data (check network / tickers).")
    out = pd.concat(frames)
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    return out


def synthetic(symbols, days=260, seed=7) -> pd.DataFrame:
    """Synthetic random-walk data with injected anomalies. FOR DEMO/TESTS ONLY - not market data."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    mkt = rng.normal(0.0003, 0.008, days)
    frames, base_prices = [], {}
    for s in symbols:
        base = s.split(".")[0]
        if s.endswith(".BO") and f"{base}.NS" in base_prices:   # BSE tracks NSE closely
            c = base_prices[f"{base}.NS"] * (1 + rng.normal(0, 0.0004, days))
            vol = rng.lognormal(12, 0.3, days)
        else:
            r = 0.9 * mkt + rng.normal(0, rng.uniform(0.007, 0.016), days)
            vol = rng.lognormal(rng.uniform(13, 15), 0.35, days)
            for k in rng.choice(np.arange(30, days), 4, replace=False):   # injected events
                r[k] += rng.choice([-1, 1]) * rng.uniform(0.045, 0.09)
                vol[k] *= rng.uniform(3.5, 7)
            c = rng.uniform(100, 4000) * np.exp(np.cumsum(r))
        base_prices[s] = c
        o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, 0.003, days))
        h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.004, days)))
        l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.004, days)))
        frames.append(pd.DataFrame(dict(symbol=s, date=dates.strftime("%Y-%m-%d"), open=o, high=h,
                                        low=l, close=c, adj_close=c, volume=vol.round())))
    c = 22000 * np.exp(np.cumsum(mkt))
    frames.append(pd.DataFrame(dict(symbol=BENCHMARK, date=dates.strftime("%Y-%m-%d"), open=c, high=c,
                                    low=c, close=c, adj_close=c, volume=0)))
    return pd.concat(frames)


def load(con, prices: pd.DataFrame, source: str):
    run_script(con, "01_schema.sql")
    con.execute("DELETE FROM prices"); con.execute("DELETE FROM securities")
    secs = [(s, *UNIVERSE.get(s, (s, "Index")), _exchange(s)) for s in prices["symbol"].unique()]
    con.executemany("INSERT INTO securities VALUES (?,?,?,?)", secs)
    cols = ["symbol", "date", "open", "high", "low", "close", "adj_close", "volume"]
    con.executemany("INSERT OR REPLACE INTO prices VALUES (?,?,?,?,?,?,?,?)",
                    prices[cols].astype(object).where(prices[cols].notna(), None).values.tolist())
    for k, v in [("source", source), ("benchmark", BENCHMARK),
                 ("loaded_at", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))]:
        con.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (k, v))
    con.commit()

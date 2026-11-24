import sqlite3
import numpy as np
import pandas as pd
from surveillance import ingest, db
from surveillance.config import UNIVERSE, BENCHMARK, DEFAULT_THRESHOLDS


def _con(tmp_path):
    con = sqlite3.connect(tmp_path / "t.db")
    ingest.load(con, ingest.synthetic(list(UNIVERSE) + [BENCHMARK], days=120), "test")
    db.build_indicators(con)
    return con


def test_indicators_match_pandas(tmp_path):
    con = _con(tmp_path)
    df = pd.read_sql_query("SELECT * FROM prices WHERE symbol='TCS.NS' ORDER BY date", con)
    df["ret"] = df.close.pct_change()
    df["vr"] = df.volume / df.volume.shift(1).rolling(20).mean()
    ind = pd.read_sql_query("SELECT * FROM indicators WHERE symbol='TCS.NS' ORDER BY date", con)
    m = ind.merge(df[["date", "ret", "vr"]], on="date", suffixes=("", "_pd")).dropna(subset=["vr"])
    full = m[m.index >= 20]  # rows with a full 20-day baseline
    assert np.allclose(full.ret, full.ret_pd)
    assert np.allclose(full.vol_ratio, full.vr)


def test_injected_anomalies_are_flagged(tmp_path):
    con = _con(tmp_path)
    a = db.alerts(con, "2000-01-01", "2100-01-01", **DEFAULT_THRESHOLDS)
    assert len(a) > 0
    assert (a.severity == "HIGH").sum() > 0


def test_stricter_thresholds_give_fewer_alerts(tmp_path):
    con = _con(tmp_path)
    loose = db.alerts(con, "2000-01-01", "2100-01-01", price_z=2, vol_ratio=2)
    strict = db.alerts(con, "2000-01-01", "2100-01-01", price_z=4, vol_ratio=5)
    assert len(strict) < len(loose)


def test_exchange_spread_has_dual_listed(tmp_path):
    con = _con(tmp_path)
    sp = db.exchange_spread(con)
    assert set(sp.base_symbol) >= {"RELIANCE", "TCS"}

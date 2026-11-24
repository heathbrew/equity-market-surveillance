"""Streamlit surveillance dashboard.  Run:  streamlit run app/dashboard.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from surveillance import db, ingest
from surveillance.config import DB_PATH, UNIVERSE, BENCHMARK, DEFAULT_THRESHOLDS

BLUE, ORANGE, AQUA, YELLOW, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#0b0b0b", "#52514e", "#e6e5e1"
SEV_COLOR = {"HIGH": ORANGE, "MEDIUM": YELLOW, "LOW": BLUE}

st.set_page_config(page_title="Equity Market Surveillance", page_icon="📈", layout="wide")
st.markdown("""<style>
.block-container{padding-top:1.4rem}
[data-testid="stMetricValue"]{font-size:1.9rem}
.banner{background:#fff4e5;border:1px solid #eda100;padding:.5rem .8rem;border-radius:6px;font-size:.9rem}
</style>""", unsafe_allow_html=True)


def style(fig, h=380):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(color=MUTED), legend=dict(orientation="h", y=1.08, x=0), hovermode="x unified")
    fig.update_xaxes(gridcolor=GRID, linecolor=GRID); fig.update_yaxes(gridcolor=GRID, linecolor=GRID)
    return fig


# ---------------- data loading ----------------
def get_con():
    return db.connect(DB_PATH)


def has_data():
    if not Path(DB_PATH).exists():
        return False
    try:
        return get_con().execute("SELECT COUNT(*) FROM indicators").fetchone()[0] > 0
    except Exception:
        return False


with st.sidebar:
    st.header("Data")
    period = st.selectbox("yfinance period", ["6mo", "1y", "2y", "5y"], index=1)
    c1, c2 = st.columns(2)
    if c1.button("Fetch live", use_container_width=True, help="Download NSE/BSE data via yfinance"):
        try:
            with st.spinner("Downloading from Yahoo Finance..."):
                con = get_con()
                ingest.load(con, ingest.fetch_yfinance(list(UNIVERSE) + [BENCHMARK], period=period), "yfinance")
                db.build_indicators(con)
            st.cache_data.clear(); st.rerun()
        except Exception as e:
            st.error(f"Fetch failed: {e}")
    if c2.button("Demo data", use_container_width=True, help="Synthetic data, offline demo only"):
        con = get_con()
        ingest.load(con, ingest.synthetic(list(UNIVERSE) + [BENCHMARK]), "SYNTHETIC DEMO DATA")
        db.build_indicators(con); st.cache_data.clear(); st.rerun()

if not has_data():
    st.title("Equity Market Surveillance")
    st.info("No data yet. Click **Fetch live** in the sidebar (or run `python -m surveillance.cli`).")
    st.stop()

con = get_con()
meta = dict(con.execute("SELECT key, value FROM meta").fetchall())
ind = pd.read_sql_query("SELECT i.*, s.name, s.sector, s.exchange FROM indicators i JOIN securities s USING(symbol)", con)
ind["date"] = pd.to_datetime(ind["date"])

# ---------------- sidebar filters ----------------
with st.sidebar:
    st.caption(f"Source: **{meta.get('source')}** · loaded {meta.get('loaded_at')}")
    st.header("Filters")
    lo, hi = ind["date"].min().date(), ind["date"].max().date()
    dr = st.date_input("Date range", (max(lo, (ind["date"].max() - pd.Timedelta(days=180)).date()), hi), min_value=lo, max_value=hi)
    start, end = (dr[0], dr[1]) if len(dr) == 2 else (lo, hi)
    exch = st.multiselect("Exchange", ["NSE", "BSE"], default=["NSE"])
    pool = sorted(ind[ind.exchange.isin(exch)].symbol.unique())
    syms = st.multiselect("Securities", pool, default=pool)
    st.header("Alert thresholds")
    th = dict(
        price_z=st.slider("Price move z-score ≥", 1.5, 6.0, DEFAULT_THRESHOLDS["price_z"], 0.1),
        vol_ratio=st.slider("Volume / 20d avg ≥", 1.5, 10.0, DEFAULT_THRESHOLDS["vol_ratio"], 0.5),
        move_pct=st.slider("Price-volume: |return| ≥", 0.01, 0.10, DEFAULT_THRESHOLDS["move_pct"], 0.005, format="%.3f"),
        gap_pct=st.slider("Opening gap ≥", 0.01, 0.10, DEFAULT_THRESHOLDS["gap_pct"], 0.005, format="%.3f"),
        dry_ratio=st.slider("Liquidity dry-up: volume ≤", 0.05, 0.6, DEFAULT_THRESHOLDS["dry_ratio"], 0.05),
    )

if "SYNTHETIC" in str(meta.get("source")):
    st.markdown('<div class="banner">⚠️ Showing <b>synthetic demo data</b>, not real market data. '
                'Click <b>Fetch live</b> to load NSE/BSE data from Yahoo Finance.</div>', unsafe_allow_html=True)

st.title("Equity Market Surveillance")
st.caption("NSE/BSE price, volume, liquidity and volatility monitoring · SQL-driven alert rules")

view = ind[(ind.date.dt.date >= start) & (ind.date.dt.date <= end) & ind.symbol.isin(syms)]
al = db.alerts(con, start, end, **th)
al = al[al.symbol.isin(syms)]
al["date"] = pd.to_datetime(al["date"])

t_over, t_pv, t_vl, t_al, t_ex, t_m = st.tabs(["Overview", "Price & Volume", "Volatility & Liquidity", "Alerts", "NSE vs BSE", "Method"])

# ---------------- Overview ----------------
with t_over:
    k = st.columns(5)
    k[0].metric("Securities monitored", len(syms))
    k[1].metric("Alerts", f"{len(al):,}")
    k[2].metric("High severity", int((al.severity == "HIGH").sum()))
    k[3].metric("Avg 20d volatility (ann.)", f"{view.volatility_20.mean() * 100:.1f}%" if len(view) else "–")
    k[4].metric("Most-flagged", al.symbol.value_counts().index[0] if len(al) else "–")
    a, b = st.columns(2)
    with a:
        st.subheader("Alerts per day by severity")
        d = al.groupby([al.date.dt.date, "severity"]).size().unstack(fill_value=0)
        fig = go.Figure()
        for sev in ["HIGH", "MEDIUM", "LOW"]:
            if sev in d:
                fig.add_bar(x=d.index, y=d[sev], name=sev, marker_color=SEV_COLOR[sev], marker_line=dict(color="white", width=1))
        st.plotly_chart(style(fig.update_layout(barmode="stack"), 340), use_container_width=True)
    with b:
        st.subheader("Most-flagged securities")
        c = al.groupby("symbol").agg(n=("score", "size"), s=("score", "sum")).sort_values("s").tail(10)
        fig = go.Figure(go.Bar(x=c.s, y=c.index, orientation="h", marker_color=BLUE, hovertemplate="%{y}: score %{x}<extra></extra>"))
        st.plotly_chart(style(fig.update_layout(hovermode="closest", xaxis_title="cumulative alert score"), 340), use_container_width=True)

# ---------------- Price & Volume ----------------
with t_pv:
    sym = st.selectbox("Security", syms or pool, key="pv_sym")
    d = view[view.symbol == sym].sort_values("date")
    f = al[al.symbol == sym]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35], vertical_spacing=0.04)
    fig.add_scatter(x=d.date, y=d.close, name="Close", line=dict(color=BLUE, width=2), row=1, col=1)
    fm = d.merge(f[["date", "severity", "flags"]], on="date")
    for sev in ["HIGH", "MEDIUM"]:
        m = fm[fm.severity == sev]
        fig.add_scatter(x=m.date, y=m.close, mode="markers", name=f"{sev} alert", text=m["flags"],
                        marker=dict(color=SEV_COLOR[sev], size=10, line=dict(color="white", width=2)), row=1, col=1)
    fig.add_bar(x=d.date, y=d.volume, name="Volume", marker_color="#9ec1ee", row=2, col=1)
    fig.add_scatter(x=d.date, y=d.avg_vol_20, name="20d avg volume", line=dict(color=ORANGE, width=2), row=2, col=1)
    st.plotly_chart(style(fig, 560), use_container_width=True)
    st.caption("Price and volume are on separate panels (no dual axis). Markers show flagged sessions.")

# ---------------- Volatility & liquidity ----------------
with t_vl:
    a, b = st.columns([3, 2])
    with a:
        st.subheader("Rolling 20-day annualised volatility")
        piv = view.pivot_table(index="symbol", columns="date", values="volatility_20")
        if len(piv):
            fig = go.Figure(go.Heatmap(z=piv.values, x=piv.columns, y=piv.index, colorscale=[[0, "#e8f1fc"], [1, "#0b3a75"]],
                                       colorbar=dict(title="σ ann."), hovertemplate="%{y} %{x|%d %b}: %{z:.1%}<extra></extra>"))
            st.plotly_chart(style(fig.update_layout(hovermode="closest"), 460), use_container_width=True)
    with b:
        st.subheader("Illiquidity (Amihud, latest)")
        last = view.sort_values("date").groupby("symbol").tail(1).set_index("symbol")
        r = (last.illiquidity_20 * 1e9).sort_values().tail(12)
        fig = go.Figure(go.Bar(x=r.values, y=r.index, orientation="h", marker_color=BLUE, hovertemplate="%{y}: %{x:.3f}<extra></extra>"))
        st.plotly_chart(style(fig.update_layout(hovermode="closest", xaxis_title="|return| per ₹1bn traded"), 460), use_container_width=True)
    st.caption("Higher Amihud ratio = a given turnover moves the price more = thinner liquidity.")

# ---------------- Alerts ----------------
with t_al:
    sev = st.multiselect("Severity", ["HIGH", "MEDIUM", "LOW"], default=["HIGH", "MEDIUM"])
    t = al[al.severity.isin(sev)].copy()
    t["date"] = t.date.dt.date
    st.dataframe(t.assign(ret=t.ret * 100, gap=t.gap * 100, volatility_20=t.volatility_20 * 100,
                          excess_ret=t.excess_ret * 100)
                 .rename(columns={"ret": "ret %", "gap": "gap %", "volatility_20": "vol20 %", "excess_ret": "excess ret %"}),
                 use_container_width=True, hide_index=True, height=520,
                 column_config={c: st.column_config.NumberColumn(format="%.2f") for c in
                                ["close", "ret %", "gap %", "vol_ratio", "price_z", "vol_z", "vol20 %", "excess ret %"]})
    st.download_button("Download alerts CSV", t.to_csv(index=False), "alerts.csv", "text/csv")

# ---------------- NSE vs BSE ----------------
with t_ex:
    sp = db.exchange_spread(con)
    if sp.empty:
        st.info("No dual-listed NSE/BSE pairs in the loaded data.")
    else:
        sp["date"] = pd.to_datetime(sp["date"]); sp = sp[(sp.date.dt.date >= start) & (sp.date.dt.date <= end)]
        base = st.selectbox("Dual-listed security", sorted(sp.base_symbol.unique()))
        d = sp[sp.base_symbol == base].sort_values("date")
        a, b = st.columns(2)
        with a:
            st.subheader("NSE − BSE close spread (bps)")
            fig = go.Figure(go.Scatter(x=d.date, y=d.spread_bps, line=dict(color=BLUE, width=2)))
            st.plotly_chart(style(fig.update_layout(yaxis_title="bps"), 340), use_container_width=True)
        with b:
            st.subheader("NSE share of combined volume")
            fig = go.Figure(go.Scatter(x=d.date, y=d.nse_volume_share, line=dict(color=ORANGE, width=2)))
            st.plotly_chart(style(fig.update_layout(yaxis_tickformat=".0%"), 340), use_container_width=True)

# ---------------- Method ----------------
with t_m:
    st.markdown("""
**Pipeline:** yfinance OHLCV → SQLite (`prices`) → SQL window functions (`indicators`) → rule-based alerts (`03_alerts.sql`).

| Indicator | Definition |
|---|---|
| `ret`, `gap` | close/prev close − 1; open/prev close − 1 |
| `vol_ratio` | volume ÷ mean volume of the prior 20 sessions |
| `price_z` / `vol_z` | z-score vs the prior 20 sessions (today excluded from its own baseline) |
| `volatility_20` | std-dev of daily returns over 20 sessions × √252 |
| `illiquidity_20` | Amihud: mean(\\|ret\\| ÷ turnover) over 20 sessions |
| `excess_ret` | stock return − Nifty 50 return (idiosyncratic move) |

**Flags:** `PRICE_SPIKE`, `VOLUME_SPIKE`, `PRICE_VOLUME` (large move *with* ≥2× volume), `GAP`, `LIQUIDITY_DRY`.
Severity is HIGH when price and volume breach together. Thresholds are the sidebar sliders.

*Alerts are statistical screens for review, not findings of manipulation or non-compliance.*
""")

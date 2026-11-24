-- Surveillance indicators. Rolling windows use the 20 PRIOR sessions so that
-- today's anomaly does not contaminate its own baseline.
DROP TABLE IF EXISTS indicators;
CREATE TABLE indicators AS
WITH base AS (
    SELECT p.symbol, p.date, p.open, p.high, p.low, p.close, p.volume,
           LAG(p.close) OVER w AS prev_close
    FROM prices p
    JOIN securities s ON s.symbol = p.symbol AND s.exchange <> 'INDEX'
    WHERE p.close IS NOT NULL AND p.volume IS NOT NULL
    WINDOW w AS (PARTITION BY p.symbol ORDER BY p.date)
),
rets AS (
    SELECT *,
           close / prev_close - 1                      AS ret,
           open  / prev_close - 1                      AS gap,
           (high - low) / prev_close                   AS range_pct,
           close * volume                              AS turnover
    FROM base WHERE prev_close IS NOT NULL AND prev_close > 0
),
win AS (
    SELECT *,
        AVG(ret)      OVER pw                      AS ret_mean,
        AVG(ret*ret)  OVER pw                      AS ret_sq_mean,
        AVG(volume)   OVER pw                      AS vol_mean,
        AVG(volume*volume) OVER pw                 AS vol_sq_mean,
        AVG(turnover) OVER pw                      AS turnover_mean,
        COUNT(*)      OVER pw                      AS n_prior,
        AVG(ret*ret)  OVER cw                      AS ret_sq_mean_cur,
        AVG(ret)      OVER cw                      AS ret_mean_cur,
        COUNT(*)      OVER cw                      AS n_cur,
        AVG(CASE WHEN turnover > 0 THEN ABS(ret)/turnover END) OVER cw AS amihud_20
    FROM rets
    WINDOW pw AS (PARTITION BY symbol ORDER BY date ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING),
           cw AS (PARTITION BY symbol ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
),
mkt AS (   -- benchmark return for market-relative (idiosyncratic) moves
    SELECT date, close / LAG(close) OVER (ORDER BY date) - 1 AS mkt_ret
    FROM prices WHERE symbol = (SELECT value FROM meta WHERE key = 'benchmark')
)
SELECT w.symbol, w.date, w.open, w.high, w.low, w.close, w.volume,
       w.ret, w.gap, w.range_pct, w.turnover,
       m.mkt_ret,
       w.ret - COALESCE(m.mkt_ret, 0)                                   AS excess_ret,
       w.vol_mean                                                       AS avg_vol_20,
       CASE WHEN w.vol_mean > 0 THEN w.volume / w.vol_mean END          AS vol_ratio,
       CASE WHEN w.n_prior >= 10 AND (w.ret_sq_mean - w.ret_mean*w.ret_mean) > 0
            THEN (w.ret - w.ret_mean) / SQRT(w.ret_sq_mean - w.ret_mean*w.ret_mean) END AS price_z,
       CASE WHEN w.n_prior >= 10 AND (w.vol_sq_mean - w.vol_mean*w.vol_mean) > 0
            THEN (w.volume - w.vol_mean) / SQRT(w.vol_sq_mean - w.vol_mean*w.vol_mean) END AS vol_z,
       CASE WHEN w.n_cur >= 10 AND (w.ret_sq_mean_cur - w.ret_mean_cur*w.ret_mean_cur) > 0
            THEN SQRT(w.ret_sq_mean_cur - w.ret_mean_cur*w.ret_mean_cur) * SQRT(252.0) END AS volatility_20,
       w.amihud_20                                                      AS illiquidity_20,
       w.n_prior
FROM win w LEFT JOIN mkt m ON m.date = w.date
WHERE w.n_prior >= 10;
CREATE INDEX IF NOT EXISTS ix_ind ON indicators(symbol, date);

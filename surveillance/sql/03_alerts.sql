-- Rule-based alert flags. Named parameters let the dashboard re-tune thresholds live.
--   :price_z  :vol_ratio  :move_pct  :gap_pct  :dry_ratio
SELECT symbol, date, close, ret, gap, volume, vol_ratio, price_z, vol_z, volatility_20, excess_ret,
       (CASE WHEN ABS(price_z) >= :price_z                                   THEN 'PRICE_SPIKE ' ELSE '' END ||
        CASE WHEN vol_ratio >= :vol_ratio                                    THEN 'VOLUME_SPIKE ' ELSE '' END ||
        CASE WHEN ABS(ret) >= :move_pct AND vol_ratio >= 2                   THEN 'PRICE_VOLUME ' ELSE '' END ||
        CASE WHEN ABS(gap) >= :gap_pct                                       THEN 'GAP ' ELSE '' END ||
        CASE WHEN vol_ratio <= :dry_ratio                                    THEN 'LIQUIDITY_DRY ' ELSE '' END) AS flags,
       (CASE WHEN ABS(price_z) >= :price_z THEN 2 ELSE 0 END +
        CASE WHEN vol_ratio >= :vol_ratio THEN 2 ELSE 0 END +
        CASE WHEN ABS(ret) >= :move_pct AND vol_ratio >= 2 THEN 3 ELSE 0 END +
        CASE WHEN ABS(gap) >= :gap_pct THEN 1 ELSE 0 END +
        CASE WHEN vol_ratio <= :dry_ratio THEN 1 ELSE 0 END) AS score,
       CASE WHEN ABS(price_z) >= :price_z AND vol_ratio >= :vol_ratio THEN 'HIGH'
            WHEN ABS(ret) >= :move_pct AND vol_ratio >= 2 THEN 'HIGH'
            WHEN ABS(price_z) >= :price_z OR vol_ratio >= :vol_ratio THEN 'MEDIUM'
            ELSE 'LOW' END AS severity
FROM indicators
WHERE date BETWEEN :start AND :end
  AND (ABS(price_z) >= :price_z OR vol_ratio >= :vol_ratio
       OR (ABS(ret) >= :move_pct AND vol_ratio >= 2)
       OR ABS(gap) >= :gap_pct OR vol_ratio <= :dry_ratio)
ORDER BY score DESC, date DESC;

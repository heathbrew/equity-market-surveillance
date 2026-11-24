-- NSE vs BSE cross-venue comparison for dual-listed names (RELIANCE.NS vs RELIANCE.BO)
SELECT n.date, SUBSTR(n.symbol,1,LENGTH(n.symbol)-3) AS base_symbol,
       n.close AS nse_close, b.close AS bse_close,
       (n.close - b.close) / b.close * 10000.0 AS spread_bps,
       n.volume AS nse_volume, b.volume AS bse_volume,
       n.volume * 1.0 / NULLIF(n.volume + b.volume, 0) AS nse_volume_share
FROM prices n JOIN prices b
  ON b.date = n.date AND b.symbol = SUBSTR(n.symbol,1,LENGTH(n.symbol)-3) || '.BO'
WHERE n.symbol LIKE '%.NS' AND n.close IS NOT NULL AND b.close IS NOT NULL;

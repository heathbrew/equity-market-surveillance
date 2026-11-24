CREATE TABLE IF NOT EXISTS securities (
    symbol   TEXT PRIMARY KEY,
    name     TEXT,
    sector   TEXT,
    exchange TEXT            -- NSE / BSE / INDEX
);
CREATE TABLE IF NOT EXISTS prices (
    symbol    TEXT NOT NULL,
    date      TEXT NOT NULL,  -- ISO yyyy-mm-dd
    open      REAL, high REAL, low REAL, close REAL, adj_close REAL,
    volume    REAL,
    PRIMARY KEY (symbol, date)
);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);

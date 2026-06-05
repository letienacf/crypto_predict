BEGIN;

CREATE TABLE IF NOT EXISTS symbols (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    base_asset VARCHAR(10) NOT NULL,
    quote_asset VARCHAR(10) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS intervals (
    id SERIAL PRIMARY KEY,
    interval VARCHAR(5) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS indicators (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    params JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS klines (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol_id INT NOT NULL REFERENCES symbols(id),
    interval_id INT NOT NULL REFERENCES intervals(id),
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    source VARCHAR(16) NOT NULL DEFAULT 'live',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (timestamp, symbol_id, interval_id)
);

CREATE TABLE IF NOT EXISTS indicator_values (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol_id INT NOT NULL REFERENCES symbols(id),
    interval_id INT NOT NULL REFERENCES intervals(id),
    indicator_id INT NOT NULL REFERENCES indicators(id),
    values JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (timestamp, symbol_id, interval_id, indicator_id)
);

CREATE INDEX IF NOT EXISTS idx_klines_symbol_interval_ts_desc
    ON klines (symbol_id, interval_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_indicator_values_symbol_interval_indicator_ts_desc
    ON indicator_values (symbol_id, interval_id, indicator_id, timestamp DESC);

COMMIT;

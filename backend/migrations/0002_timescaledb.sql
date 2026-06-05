BEGIN;

CREATE EXTENSION IF NOT EXISTS timescaledb;

SELECT create_hypertable(
    relation => 'klines',
    time_column_name => 'timestamp',
    if_not_exists => TRUE,
    migrate_data => TRUE
);

SELECT create_hypertable(
    relation => 'indicator_values',
    time_column_name => 'timestamp',
    if_not_exists => TRUE,
    migrate_data => TRUE
);

COMMIT;

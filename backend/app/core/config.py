from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized runtime settings with validation and safe defaults."""

    app_name: str = "crypto_predict_gateway"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    postgres_dsn: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/binance_market"
    )
    redis_url: str = "redis://localhost:6379/0"
    binance_ws_base_url: str = "wss://stream.binance.com:9443"
    binance_symbols: str = "btcusdt,ethusdt,bnbusdt"
    binance_intervals: str = "1m,5m,15m,1h,4h,1d,1w"
    binance_rest_base_url: str = "https://api.binance.com"
    binance_connection_rotation_seconds: int = Field(default=86100, ge=60)
    reconnect_max_seconds: int = Field(default=30, ge=1, le=300)
    enable_gap_detection: bool = True
    gap_fill_max_klines_per_request: int = Field(default=1000, ge=1, le=1000)
    ws_max_symbols_per_session: int = Field(default=50, ge=1, le=500)
    ws_max_intervals_per_session: int = Field(default=7, ge=1, le=20)
    data_saver_batch_size: int = Field(default=100, ge=1, le=5000)
    data_saver_max_batch_size: int = Field(default=5000, ge=100, le=50000)
    data_saver_flush_seconds: int = Field(default=10, ge=1, le=60)
    max_kline_limit: int = Field(default=1000, ge=1, le=5000)
    historical_cache_enabled: bool = True
    historical_cache_limit: int = Field(default=1000, ge=1, le=5000)
    historical_cache_ttl_seconds: int = Field(default=86400, ge=0)

    model_config = SettingsConfigDict(env_prefix="CP_", extra="ignore")

    @property
    def stream_symbols(self) -> list[str]:
        return [value.strip().lower() for value in self.binance_symbols.split(",") if value.strip()]

    @property
    def stream_intervals(self) -> list[str]:
        return [
            value.strip().lower()
            for value in self.binance_intervals.split(",")
            if value.strip()
        ]


settings = Settings()

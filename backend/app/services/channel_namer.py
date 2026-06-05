class ChannelNamer:
    """Canonical Redis channel naming helper (B2)."""

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        return symbol.strip().lower()

    @staticmethod
    def normalize_interval(interval: str) -> str:
        return interval.strip().lower()

    @classmethod
    def trade_tick(cls, symbol: str) -> str:
        return f"market:trade.tick:{cls.normalize_symbol(symbol)}"

    @classmethod
    def kline_partial(cls, symbol: str, interval: str) -> str:
        return (
            f"market:kline.partial:{cls.normalize_symbol(symbol)}:{cls.normalize_interval(interval)}"
        )

    @classmethod
    def kline_closed(cls, symbol: str, interval: str) -> str:
        return (
            f"market:kline.closed:{cls.normalize_symbol(symbol)}:{cls.normalize_interval(interval)}"
        )

    @classmethod
    def gap_detected(cls, symbol: str, interval: str) -> str:
        return (
            f"system:gap_detected:{cls.normalize_symbol(symbol)}:{cls.normalize_interval(interval)}"
        )

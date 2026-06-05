from app.services.binance_stream_parser import BinanceStreamParser


def test_parse_trade_tick() -> None:
    parser = BinanceStreamParser()
    payload = {
        "e": "aggTrade",
        "s": "BTCUSDT",
        "p": "65000.10",
        "q": "0.25",
        "T": 1717502400000,
    }

    result = parser.parse_trade_tick(payload)

    assert result.event_type == "trade.tick"
    assert result.symbol == "btcusdt"
    assert result.price == 65000.10
    assert result.quantity == 0.25


def test_parse_kline_closed() -> None:
    parser = BinanceStreamParser()
    payload = {
        "e": "kline",
        "s": "BTCUSDT",
        "k": {
            "i": "1m",
            "t": 1717502400000,
            "T": 1717502459999,
            "o": "65000.0",
            "h": "65010.0",
            "l": "64990.0",
            "c": "65005.0",
            "v": "12.5",
            "x": True,
        },
    }

    result = parser.parse_kline(payload)

    assert result.event_type == "kline.closed"
    assert result.is_closed is True
    assert result.interval == "1m"

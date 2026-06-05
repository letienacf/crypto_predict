from app.services.channel_namer import ChannelNamer


def test_channel_namer_trade_tick() -> None:
    channel = ChannelNamer.trade_tick("BTCUSDT")
    assert channel == "market:trade.tick:btcusdt"


def test_channel_namer_kline_closed() -> None:
    channel = ChannelNamer.kline_closed("ETHUSDT", "1M")
    assert channel == "market:kline.closed:ethusdt:1m"

import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceWithdrawException
from binance.enums import *
import talib
import numpy
from datetime import datetime
from enum import Enum
import csv
import matplotlib.pyplot as plt
from ta import trend

from Connect import Connect
from Candles import Candles
from OnlineTrade import Trade
from BackTest import Algorithm_1
import Strategy


def main(client):
    """

    :type client: type of binance client
    """
    # candle = Candles(client)
    # klines = candle.getKlines("BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "1 hour ago UTC", "")
    # # c = candle.getCandle('BTCUSDT', Client.KLINE_INTERVAL_1HOUR)
    # candle.unpackCandle(klines)
    # high_series = pd.Series(candle.high)
    # low_series = pd.Series(candle.low)
    # alg = Algorithm_1(klines, high_series, low_series, candle.close)
    # alg.RunAlgorithm()

    trade = Trade(client, "BTC", "USDT")
    trade.RunTradeThread()

if __name__ == "__main__":
    connectToBinance = Connect()
    client = connectToBinance.ConnectTo
    main(client)

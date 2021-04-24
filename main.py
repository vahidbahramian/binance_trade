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
from binance.websockets import BinanceSocketManager
from ta import trend

from Connect import Connect
from Candles import Candles
from OnlineTrade import Algo_1
from BackTest import Algorithm_1
import Strategy
from IO import FileWorking
from threading import Lock

def main(client):
    """

    :type client: type of binance client
    """
    # mutex = Lock()
    # candle = Candles(client, mutex)
    # klines = candle.getKlines("BNBUSDT", Client.KLINE_INTERVAL_1HOUR, "1 Jan, 2018", "1 Jan, 2020")
    # with open("BNBBTC_1HOUR_1.1.2018_1.1.2020.txt", "w") as file:
    #     file.write(json.dumps(klines))
    # FileWorking.WriteKlines(klines, "Data\\BNBUSDT_1HOUR_1.1.2018_1.1.2020.txt")
    # # c = candle.getCandle('BTCUSDT', Client.KLINE_INTERVAL_1HOUR)
    # candle.unpackCandle(klines)
    # high_series = pd.Series(candle.high)
    # low_series = pd.Series(candle.low)
    # alg = Algorithm_1(klines, high_series, low_series, candle.close)
    # alg.RunAlgorithm()
    bsm = BinanceSocketManager(client)
    bsm.start()

    mutex = Lock()
    candle = Candles(client,mutex)
    btc_trade = Algo_1(client, bsm , candle, "BTC", "USDT", ignoreLastTrade=True)
    btc_trade.SetAlgorithmParam(window1=36, window2=48, window3=144, t=18, a=0, b=0.04)
    btc_trade.RunTradeThread()

    eth_trade = Algo_1(client, bsm ,candle, "ETH", "USDT", ignoreLastTrade=True)
    eth_trade.SetAlgorithmParam(window1=9, window2=24, window3=96, t=26, a=0, b=0.04)
    eth_trade.RunTradeThread()

if __name__ == "__main__":
    connectToBinance = Connect()
    client = connectToBinance.ConnectTo
    main(client)

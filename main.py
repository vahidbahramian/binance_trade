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
import configparser
import sys

from Connect import Connect
from Candles import Candles
from IO import FileWorking
from OnlineTrade import Algo_1, Algo_2
import BackTest
import Strategy
from threading import Lock
from binance.websockets import BinanceSocketManager
from twisted.internet import reactor

def main(client):
    """

    :type client: type of binance client
    """
    back_test = False

    mutex = Lock()
    candle = Candles(client, mutex)
    # start_time = "1.1.2020"
    # end_time = "1.1.2021"
    # klines = (candle.getKlines("BNBBTC", Client.KLINE_INTERVAL_1HOUR, "1 Jan, 2020", "1 Jan, 2021"))
    # FileWorking.WriteKlines(klines, "Data\\" + "BNBBTC" + "_1HOUR_" + start_time + "_" + end_time + ".txt")
    if back_test:
        # alg = BackTest.Algorithm_1(candle)
        # alg.RunAlgorithm()

        currency = ["BTCUSDT", "BNBUSDT", "BNBBTC"]
        alg = BackTest.Algorithm_2(candle, currency)
        alg.RunAlgorithm()

        # currency = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        # currency_pair = ["ETHBTC", "BNBBTC"]
        # correspond = {}
        # for i, item in enumerate(currency_pair):
        #     correspond[item] = currency[i+1]
        # alg = BackTest.Algorithm_3(candle, currency, currency_pair, correspond)
        # alg.RunAlgorithm()
    else:
        bsm = BinanceSocketManager(client)
        # bsm.start()
        # bsm.close()
        # reactor.stop()

        # btc_trade = Algo_1(client, bsm , candle, "BTC", "USDT", ignoreLastTrade=False)
        # btc_trade.SetAlgorithmParam(window1=36, window2=48, window3=144, t=18, a=0, b=0.04)
        # btc_trade.RunTradeThread()
        #
        # eth_trade = Algo_1(client, bsm ,candle, "ETH", "USDT", ignoreLastTrade=False)
        # eth_trade.SetAlgorithmParam(window1=9, window2=24, window3=96, t=26, a=0, b=0.04)
        # eth_trade.RunTradeThread()

        currency = ["BTC", "ETH", "BNB", "USDT"]
        trade = Algo_2(client, bsm, candle, currency)
        trade.SetAlgorithmParam(currency="BTCUSDT", window1=36, window2=72, window3=96, t=26, a=0.01, b=0.06)
        trade.SetAlgorithmParam(currency="ETHBTC", window1=9, window2=24, window3=144, t=26, a=0, b=0.05)
        trade.SetAlgorithmParam(currency="BNBBTC", window1=24, window2=72, window3=144, t=26, a=0, b=0.04)
        trade.RunTradeThread()

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('Config.ini')
    section = str(sys.argv[1])
    connectToBinance = Connect(config[section])
    client = connectToBinance.ConnectTo
    main(client)

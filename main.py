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
from OnlineTrade import Algo_1, Algo_2, Algo_3
import BackTest
import Strategy
from threading import Lock
from binance.websockets import BinanceSocketManager
from twisted.internet import reactor

def main(client):
    """

    :type client: type of binance client
    """
    back_test = True

    mutex = Lock()
    candle = Candles(client, mutex)
    # start_time = "1.1.2020"
    # end_time = "1.1.2021"
    # klines = (candle.getKlines("LTCUSDT", Client.KLINE_INTERVAL_1HOUR, "1 Jan, 2020", "1 Jan, 2021"))
    # FileWorking.WriteKlines(klines, "Data\\" + "LTCUSDT" + "_1HOUR_" + start_time + "_" + end_time + ".txt")
    if back_test:
        # alg = BackTest.Algorithm_1(candle)
        # alg.RunAlgorithm()

        # currency = ["BTCUSDT", "BNBUSDT", "BNBBTC"]
        # alg = BackTest.Algorithm_2(candle, currency)
        # alg.RunAlgorithm()

        # currency = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        # currency_pair = ["ETHBTC", "BNBBTC"]
        # correspond = {}
        # for i, item in enumerate(currency_pair):
        #     correspond[item] = currency[i+1]
        # alg = BackTest.Algorithm_3(candle, currency, currency_pair, correspond)
        # alg.RunAlgorithm()

        currency = ["BTC", "ETH", "USDT"]
        trade = BackTest.Algorithm_4(candle, currency)

        trade.SetAlgorithmParam(currency[0] + currency[2], window1=36, window2=72, window3=144, t=26, a=0.01, b=0.06)
        trade.SetAlgorithmParam(currency[1] + currency[2], window1=18, window2=24, window3=48, t=26, a=0, b=0.06)
        window1 = [9, 18, 24, 36]
        window2 = [24, 48, 72]
        window3 = [48, 96, 144]
        t_ = [18, 26, 48]
        a_ = [0, 0.01]
        b_ = [0.04, 0.05, 0.06]
        SL_arr = [0.025, 0.05]

        # self.window1 = [18]
        # self.window2 = [24]
        # self.window3 = [96]
        # self.t = [18]
        # self.a = [0]
        # self.b = [0.05]

        for win1 in window1:
            for win2 in window2:
                for win3 in window3:
                    for t in t_:
                        print(win1, " ", win2, " ", win3, " ", t, " ")
                        for a in a_:
                            for b in b_:
                                trade.SetAlgorithmParam(currency[1] + currency[0], window1=win1, window2=win2,
                                                        window3=win3, t=t, a=a, b=b)
                                trade.Run()

        # currency = ["BTC", "ETH", "BNB", "LTC", "XRP", "USDT"]
        # trade.SetAlgorithmParam("BTCUSDT", window1=36, window2=72, window3=96, t=26, a=0.01, b=0.06)
        # trade.SetAlgorithmParam("ETHUSDT", window1=9, window2=24, window3=144, t=26, a=0, b=0.05)
        # trade.SetAlgorithmParam("BNBUSDT", window1=18, window2=72, window3=96, t=26, a=0, b=0.04)
        # trade.SetAlgorithmParam("LTCUSDT", window1=18, window2=72, window3=96, t=26, a=0, b=0.04)
        # trade.SetAlgorithmParam("XRPUSDT", window1=18, window2=72, window3=96, t=26, a=0, b=0.04)
        # trade.SetAlgorithmParam("ETHBTC", window1=9, window2=24, window3=144, t=26, a=0, b=0.05)
        # trade.SetAlgorithmParam("BNBBTC", window1=18, window2=72, window3=96, t=26, a=0, b=0.04)
        # trade.SetAlgorithmParam("LTCBTC", window1=18, window2=72, window3=96, t=26, a=0, b=0.04)
        # trade.SetAlgorithmParam("XRPBTC", window1=18, window2=72, window3=96, t=26, a=0, b=0.04)
        # trade.Run()
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

        # currency = ["BTC", "ETH", "BNB", "USDT"]
        # trade = Algo_2(client, bsm, candle, currency)
        # trade.SetAlgorithmParam("BTCUSDT", window1=36, window2=72, window3=96, t=26, a=0.01, b=0.06)
        # trade.SetAlgorithmParam("ETHBTC", window1=9, window2=24, window3=144, t=26, a=0, b=0.05)
        # trade.SetAlgorithmParam("BNBBTC", window1=18, window2=72, window3=96, t=26, a=0, b=0.04)
        # trade.RunTradeThread()

        currency = ["BTC", "ETH", "BNB", "USDT"]
        trade = Algo_3(client, bsm, candle, currency)
        trade.SetAlgorithmParam("BTCUSDT", window1=36, window2=72, window3=96, t=26, a=0.01, b=0.06)
        trade.SetAlgorithmParam("ETHUSDT", window1=9, window2=24, window3=144, t=26, a=0, b=0.05)
        trade.SetAlgorithmParam("BNBUSDT", window1=18, window2=72, window3=96, t=26, a=0, b=0.04)
        trade.SetAlgorithmParam("ETHBTC", window1=9, window2=24, window3=144, t=26, a=0, b=0.05)
        trade.SetAlgorithmParam("BNBBTC", window1=18, window2=72, window3=96, t=26, a=0, b=0.04)
        trade.RunTradeThread()

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('Config.ini')
    section = str(sys.argv[1])
    connectToBinance = Connect(config[section])
    client = connectToBinance.ConnectTo
    main(client)

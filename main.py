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
from OnlineTrade import Algo_1
import BackTest
import Strategy
from threading import Lock
from binance.websockets import BinanceSocketManager

def main(client):
    """

    :type client: type of binance client
    """
    back_test = True

    mutex = Lock()
    candle = Candles(client, mutex)

    if back_test:
        # alg = BackTest.Algorithm_1(candle)
        # alg.RunAlgorithm()
        currency = ["BTCUSDT", "ETHUSDT"]
        currency_pair = ["ETHBTC"]
        correspond = {"ETHBTC": "ETHUSDT"}
        alg = BackTest.Algorithm_3(candle, currency, currency_pair, correspond)
        alg.RunAlgorithm()
    else:
        bsm = BinanceSocketManager(client)
        bsm.start()

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

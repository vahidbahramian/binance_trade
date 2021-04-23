import sys
import traceback
from datetime import datetime
import threading
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceWithdrawException, BinanceRequestException,\
    BinanceOrderException
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects, RequestException
from Strategy import ICHIMOKU_2_Strategy
from Candles import Candles
import pandas as pd
import numpy
import logging
import time
import datetime
from IO import WritePrintToFile
from Algorithm import OnlineAlgorithm

class Algo_1(OnlineAlgorithm):
    def __init__(self, client, candle, firstCurrency, secondCurrency, ignoreLastTrade):
        self.client = client
        self.candle = candle
        # self.SetLastSellBuyPrice('XRPBNB')
        self.first_currency = firstCurrency
        self.second_currency = secondCurrency
        self.currency_pair = firstCurrency + secondCurrency

        self.ignoreLastTrade = ignoreLastTrade
        # self.candle = Candles(client)
        # klines = self.candle.getKlines(self.currency_pair, Client.KLINE_INTERVAL_1HOUR, "10 days ago UTC", "")
        # # klines = candle.getKlines("BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "1 hour ago UTC", "")
        # self.candle.unpackCandle(klines)
        # high_series = pd.Series(self.candle.high)
        # low_series = pd.Series(self.candle.low)
        # self.close_data = self.candle.close
        # self.ichi_2_strategy = ICHIMOKU_2_Strategy(high_series, low_series, self.close_data)
        #
        # self.SetAlgorithmParam(36, 48, 144, 18, 0, 0.04)
        # self.ichi_2_strategy.ComputeIchimoku_A(self.win1, self.win2)
        # self.ichi_2_strategy.ComputeIchimoku_B(self.win2, self.win3)
        # self.ichi_2_strategy.ComputeIchimoku_Base_Line(self.win1, self.win2)
        # self.ichi_2_strategy.ComputeIchimoku_Conversion_Line(self.win1, self.win2)

        # self.LastTimeOfCandle = self.candle.timeUTC[-1]

        self.InitLogger()

    def SetAlgorithmParam(self, window1, window2, window3, t, a, b):
        self.win1 = window1
        self.win2 = window2
        self.win3 = window3
        self.t = t
        self.a = a
        self.b = b

    def InitCandle(self):
        klines = self.candle.getKlines(self.currency_pair, Client.KLINE_INTERVAL_1HOUR, "10 days ago UTC", "")
        # klines = candle.getKlines("BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "1 hour ago UTC", "")
        self.candle.unpackCandle(klines)
        high_series = pd.Series(self.candle.high)
        low_series = pd.Series(self.candle.low)
        self.close_data = self.candle.close
        self.ichi_2_strategy = ICHIMOKU_2_Strategy(high_series, low_series, self.close_data)

        self.ichi_2_strategy.ComputeIchimoku_A(self.win1, self.win2)
        self.ichi_2_strategy.ComputeIchimoku_B(self.win2, self.win3)
        self.ichi_2_strategy.ComputeIchimoku_Base_Line(self.win1, self.win2)
        self.ichi_2_strategy.ComputeIchimoku_Conversion_Line(self.win1, self.win2)

        self.LastTimeOfCandle = self.candle.timeUTC[-1]

    def InitLogger(self):
        # Create a logging instance
        self.logger = logging.getLogger('my_application')
        self.logger.setLevel(logging.INFO)  # you can set this to be DEBUG, INFO, ERROR

        # Assign a file-handler to that instance
        fh = logging.FileHandler("log.log")
        fh.setLevel(logging.INFO)  # again, you can set this differently

        # Format your logs (optional)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)  # This will set the format to the file handler

        # Add the handler to your logging instance
        self.logger.addHandler(fh)

    # def SetLastSellBuyPrice(self, currency_pair):
    #     my_trade = self.client.get_my_trades(symbol=currency_pair)
    #     setSell = False
    #     setBuy = False
    #     self.sell_price_xrp = 0
    #     self.buy_price_xrp = 0
    #     for i,item in enumerate(reversed(my_trade)):
    #         if item['isBuyer'] and not setBuy:
    #             self.buy_price_xrp = item['price']
    #             setBuy = True
    #         elif not item['isBuyer'] and not setSell:
    #             self.sell_price_xrp = item['price']
    #             setSell = True
    #         elif setBuy and setSell:
    #             break

    def RunTradeThread(self):
        self.InitCandle()
        try:
            th = threading.Thread(target=self.RunTrade, args=())
            th.start()
            # self.updateCandleTimer = threading.Timer(10, self.UpdateCandle, [self.currency_pair, "1 hour ago UTC"])
            # self.updateCandleTimer.start()
            # th1 = threading.Thread(target=self.RunTrade, args=())
            # th1.start()
        except:
            print("Error: unable to start thread")

    def BuyOrderCondition(self):
        return self.ichi_2_strategy.BuyStrategy(len(self.ichi_2_strategy.close_data) - 1, self.t, self.a, self.b)

    def SellOrderCondition(self):
        return self.ichi_2_strategy.SellStrategy(len(self.ichi_2_strategy.close_data) - 1, self.t)

    def UpdateCandle(self, currency_pair, time):
        c = self.candle.getKlines(currency_pair, Client.KLINE_INTERVAL_1HOUR, time, "")
        self.candle.unpackCandle(c)
        if len(self.candle.timeUTC) != 0:
            if self.candle.timeUTC[0] > self.LastTimeOfCandle:
                self.ichi_2_strategy.high_data.pop(0)
                self.ichi_2_strategy.high_data.reset_index(drop=True, inplace=True)
                self.ichi_2_strategy.low_data.pop(0)
                self.ichi_2_strategy.low_data.reset_index(drop=True, inplace=True)
                self.ichi_2_strategy.close_data = numpy.delete(self.ichi_2_strategy.close_data, 0)


                self.ichi_2_strategy.high_data = \
                    self.ichi_2_strategy.high_data.append(pd.Series(self.candle.high[0]), ignore_index=True)
                self.ichi_2_strategy.low_data = \
                    self.ichi_2_strategy.low_data.append(pd.Series(self.candle.low[0]), ignore_index=True)
                self.ichi_2_strategy.close_data = numpy.append(self.ichi_2_strategy.close_data, self.candle.close[0])

                self.ichi_2_strategy.ComputeIchimoku_A(self.win1, self.win2)
                self.ichi_2_strategy.ComputeIchimoku_B(self.win2, self.win3)
                self.ichi_2_strategy.ComputeIchimoku_Base_Line(self.win1, self.win2)
                self.ichi_2_strategy.ComputeIchimoku_Conversion_Line(self.win1, self.win2)

                self.LastTimeOfCandle = self.candle.timeUTC[0]

                print(datetime.datetime.now())
        # c = self.candle.getKlines(currency_pair, Client.KLINE_INTERVAL_1HOUR, time, "")
        # self.candle.unpackCandle(c)
        # if len(self.candle.timeUTC) != 0:
        #     if self.candle.timeUTC[0] > self.LastTimeOfCandle:
        #         self.ichi_2_strategy.high_data.pop(0)
        #         self.ichi_2_strategy.high_data.reset_index(drop=True, inplace=True)
        #         self.ichi_2_strategy.low_data.pop(0)
        #         self.ichi_2_strategy.low_data.reset_index(drop=True, inplace=True)
        #         self.ichi_2_strategy.close_data = numpy.delete(self.ichi_2_strategy.close_data, 0)
        #
        #
        #         self.ichi_2_strategy.high_data = \
        #             self.ichi_2_strategy.high_data.append(pd.Series(self.candle.high[0]), ignore_index=True)
        #         self.ichi_2_strategy.low_data = \
        #             self.ichi_2_strategy.low_data.append(pd.Series(self.candle.low[0]), ignore_index=True)
        #         self.ichi_2_strategy.close_data = numpy.append(self.ichi_2_strategy.close_data, self.candle.close[0])
        #
        #         self.ichi_2_strategy.ComputeIchimoku_A(self.win1, self.win2)
        #         self.ichi_2_strategy.ComputeIchimoku_B(self.win2, self.win3)
        #         self.ichi_2_strategy.ComputeIchimoku_Base_Line(self.win1, self.win2)
        #         self.ichi_2_strategy.ComputeIchimoku_Conversion_Line(self.win1, self.win2)
        #
        #         self.LastTimeOfCandle = self.candle.timeUTC[0]
        #
        #         print(datetime.datetime.now())

    def RunTrade(self):
        # try:
        last_trade = self.client.get_my_trades(symbol=self.currency_pair)
        if len(last_trade) > 0 and last_trade[-1]['isBuyer']:
            isPosition = True
        else:
            isPosition = False
        while True:
            self.UpdateCandle(self.currency_pair, "1 hour ago UTC")
            # time.sleep(0.5)
            try:
                open_order = self.client.get_open_orders(symbol=self.currency_pair)
                if len(open_order) == 0:
                    if not isPosition and self.BuyOrderCondition():
                        last_trade = self.client.get_my_trades(symbol=self.currency_pair)
                        if self.ignoreLastTrade:
                            self.usdt_balance = 50
                            self.ignoreLastTrade = False
                        elif len(last_trade) > 0:
                            if not last_trade[-1]['isBuyer']:
                                self.usdt_balance = last_trade['quoteQty']
                        else:
                            self.usdt_balance = 50
                        self.buy_price = self.GetPrice(self.currency_pair)
                        order = self.SetMarketBuyOrder(self.currency_pair, round(float(self.usdt_balance['free']) / float(self.buy_price), 6)-0.000001)
                        self.logger.info(order)
                        isPosition = True
                    if isPosition:
                        if self.SellOrderCondition():
                            self.first_currency_balance = self.GetBalance(self.first_currency)
                            self.sell_price = self.GetPrice(self.currency_pair)
                            order = self.SetMarketSellOrder(self.currency_pair, round(float(self.self.first_currency_balance['free']), 6) - 0.000001)
                            self.logger.info(order)
                            isPosition = False
                else:
                    if open_order[0]['side'] == "SELL":
                        self.sell_price = open_order[0]['price']
                        isPosition = False
                    if open_order[0]['side'] == "BUY":
                        self.buy_price = open_order[0]['price']
                        isPosition = True
            except ConnectionAbortedError as e:
                WritePrintToFile.Write(self.currency_pair)
                WritePrintToFile.Write(e)
            except ConnectionError as e:
                WritePrintToFile.Write(self.currency_pair)
                WritePrintToFile.Write(e)
            except ConnectionResetError as e:
                WritePrintToFile.Write(self.currency_pair)
                WritePrintToFile.Write(e)
            except BinanceAPIException as e:
                WritePrintToFile.Write(self.currency_pair)
                WritePrintToFile.Write(e)
            except BinanceWithdrawException as e:
                WritePrintToFile.Write(self.currency_pair)
                WritePrintToFile.Write(e)
            except BinanceRequestException as e:
                WritePrintToFile.Write(self.currency_pair)
                WritePrintToFile.Write(e)
            except BinanceOrderException as e:
                WritePrintToFile.Write(self.currency_pair)
                WritePrintToFile.Write(e)
            except Timeout as e:
                WritePrintToFile.Write(self.currency_pair)
                WritePrintToFile.Write(e)
            except TooManyRedirects as e:
                WritePrintToFile.Write(self.currency_pair)
                WritePrintToFile.Write(e)
            except RequestException as e:
                WritePrintToFile.Write(self.currency_pair)
                WritePrintToFile.Write(e)
        # except Exception as e:
        #     traceback.print_exc(file=sys.stdout)
        #     # self.logger.exception(e)


    # def RunTrade(self):
    #     if int(float(self.GetBalance('XRP')['free'])) == 0:
    #         isPosition = False
    #     else:
    #         isPosition = True
    #     while True:
    #         try:
    #             open_order = self.client.get_open_orders(symbol='XRPBNB')
    #             if len(open_order) == 0:
    #                 if not isPosition and (float(self.GetPrice("XRPBNB")) <= float(self.sell_price_xrp) * 0.97 or
    #                         float(self.GetPrice("XRPBNB")) >= float(self.sell_price_xrp) * 1.04):
    #                     self.bnb_balance = self.GetBalance('BNB')
    #                     self.buy_price_xrp = self.GetPrice("XRPBNB")
    #                     order = self.SetMarketBuyOrder("XRPBNB", int(float(self.bnb_balance['free'])/float(self.buy_price_xrp)))
    #                     self.logger.info(order)
    #                 if isPosition:
    #                     if (float(self.GetPrice("XRPBNB")) >= float(self.buy_price_xrp) * 1.03 or
    #                             float(self.GetPrice("XRPBNB")) <= float(self.buy_price_xrp) * 0.96):
    #                         self.xrp_balance = self.GetBalance('XRP')
    #                         self.sell_price_xrp = self.GetPrice("XRPBNB")
    #                         order = self.SetMarketSellOrder("XRPBNB", int(float(self.xrp_balance['free'])))
    #                         self.logger.info(order)
    #                         isPosition = False
    #             else:
    #                 if open_order[0]['side'] == "SELL":
    #                     self.sell_price_xrp = open_order[0]['price']
    #                     isPosition = False
    #                 if open_order[0]['side'] == "BUY":
    #                     self.buy_price_xrp = open_order[0]['price']
    #                     isPosition = True
    #         except ConnectionAbortedError as e:
    #             WritePrintToFile.Write(e)
    #         except ConnectionError as e:
    #             WritePrintToFile.Write(e)
    #         except ConnectionResetError as e:
    #             WritePrintToFile.Write(e)
    #         except BinanceAPIException as e:
    #             WritePrintToFile.Write(e)
    #         except BinanceWithdrawException as e:
    #             WritePrintToFile.Write(e)
    #         except BinanceRequestException as e:
    #             WritePrintToFile.Write(e)
    #         except BinanceOrderException as e:
    #             WritePrintToFile.Write(e)
    #         except Timeout as e:
    #             WritePrintToFile.Write(e)
    #         except TooManyRedirects as e:
    #             WritePrintToFile.Write(e)
    #         except RequestException as e:
    #             WritePrintToFile.Write(e)

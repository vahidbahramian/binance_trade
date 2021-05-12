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

import time
import datetime
from IO import FileWorking
from Algorithm import OnlineAlgorithm

class Algo_1(OnlineAlgorithm):
    def __init__(self, client, bsm, candle, firstCurrency, secondCurrency, ignoreLastTrade):
        super().__init__(client, bsm, candle)
        self.first_currency = firstCurrency
        self.second_currency = secondCurrency
        self.currency_pair = firstCurrency + secondCurrency
        # self.SetLastSellBuyPrice('XRPBNB')
        self.ignoreLastTrade = ignoreLastTrade

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

        self.conn_key = self.bsm.start_kline_socket(self.currency_pair, self.UpdateCandle,
                                                  interval=Client.KLINE_INTERVAL_1HOUR)
        if not self.bsm.is_alive():
            self.bsm.start()

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

    def UpdateCandle(self, msg):#currency_pair, time):
        if msg['e'] == 'error':
            print(msg)
            self.bsm.stop_socket(self.conn_key)
            self.conn_key = self.bsm.start_kline_socket(self.currency_pair, self.UpdateCandle,
                                                        interval=Client.KLINE_INTERVAL_1HOUR)
        else:
            time = datetime.datetime.utcfromtimestamp(msg["k"]["t"] / 1000)
            if time > self.LastTimeOfCandle:
                self.ichi_2_strategy.high_data.pop(0)
                self.ichi_2_strategy.high_data.reset_index(drop=True, inplace=True)
                self.ichi_2_strategy.low_data.pop(0)
                self.ichi_2_strategy.low_data.reset_index(drop=True, inplace=True)
                self.ichi_2_strategy.close_data = numpy.delete(self.ichi_2_strategy.close_data, 0)


                self.ichi_2_strategy.high_data = \
                    self.ichi_2_strategy.high_data.append(pd.Series(float(msg["k"]["h"])), ignore_index=True)
                self.ichi_2_strategy.low_data = \
                    self.ichi_2_strategy.low_data.append(pd.Series(float(msg["k"]["l"])), ignore_index=True)
                self.ichi_2_strategy.close_data = numpy.append(self.ichi_2_strategy.close_data, float(msg["k"]["c"]))

                self.ichi_2_strategy.ComputeIchimoku_A(self.win1, self.win2)
                self.ichi_2_strategy.ComputeIchimoku_B(self.win2, self.win3)
                self.ichi_2_strategy.ComputeIchimoku_Base_Line(self.win1, self.win2)
                self.ichi_2_strategy.ComputeIchimoku_Conversion_Line(self.win1, self.win2)

                self.LastTimeOfCandle = time

                FileWorking.Write(datetime.datetime.now())
                print(datetime.datetime.now())

    def RunTrade(self):
        last_trade = self.client.get_my_trades(symbol=self.currency_pair)
        if len(last_trade) > 0 and last_trade[-1]['isBuyer']:
            isPosition = True
        else:
            isPosition = False
        localtime = datetime.datetime.now()
        while True:
            time.sleep(0.5)
            try:
                if localtime.hour < datetime.datetime.now().hour:
                    print("Thread is Run!!!")
                    localtime = datetime.datetime.now()
                # open_order = self.client.get_open_orders(symbol=self.currency_pair)
                # if len(open_order) == 0:
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
                    order = self.SetMarketBuyOrder(self.currency_pair, round(float(self.usdt_balance) / float(self.buy_price), 6)-0.000001)
                    self.logger.info(order)
                    print(order)
                    isPosition = True
                if isPosition:
                    if self.SellOrderCondition():
                        self.first_currency_balance = self.GetBalance(self.first_currency)
                        self.sell_price = self.GetPrice(self.currency_pair)
                        order = self.SetMarketSellOrder(self.currency_pair, round(self.first_currency_balance, 5) - 0.00001)
                        self.logger.info(order)
                        print(order)
                        isPosition = False
                # else:
                #     if open_order[0]['side'] == "SELL":
                #         self.sell_price = open_order[0]['price']
                #         isPosition = False
                #     if open_order[0]['side'] == "BUY":
                #         self.buy_price = open_order[0]['price']
                #         isPosition = True
            except ConnectionAbortedError as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except ConnectionError as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except ConnectionResetError as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except BinanceAPIException as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except BinanceWithdrawException as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except BinanceRequestException as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except BinanceOrderException as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except Timeout as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except TooManyRedirects as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except RequestException as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)

class Algo_2(OnlineAlgorithm):
    klines = {}
    ichi_2_strategy = {}
    param = {}
    def __init__(self, client, bsm, candle, currency):
        super().__init__(client, bsm, candle)
        self.currency = currency
        self.currency_pair = []
        for i in self.currency[:-1]:
            self.currency_pair.append(i+self.currency[-1])
        self.currency_pair_secondery = []
        for i in self.currency[1:-1]:
            self.currency_pair_secondery.append(i+self.currency[0])
        self.correspond = {}
        for i, item in enumerate(self.currency_pair_secondery):
            self.correspond[item] = self.currency_pair[i+1]
            self.correspond[self.currency_pair[i+1]] = self.currency[i+1]
        pass

    def SetAlgorithmParam(self, currency_pair, window1, window2, window3, t, a, b):
        self.param[currency_pair]["Win1"] = window1
        self.param[currency_pair]["Win2"] = window2
        self.param[currency_pair]["Win3"] = window3
        self.param[currency_pair]["t"] = t
        self.param[currency_pair]["a"] = a
        self.param[currency_pair]["b"] = b

    def InitCandle(self):
        for i in self.currency_pair:
            self.klines[i] = self.candle.getKlines(i, Client.KLINE_INTERVAL_1HOUR, "10 days ago UTC", "")
        for i in self.currency_pair_secondery:
            self.klines[i] = self.candle.getKlines(i, Client.KLINE_INTERVAL_1HOUR, "10 days ago UTC", "")

        for currency, kline in self.klines.items():
            self.candle.unpackCandle(kline)
            high_series = pd.Series(self.candle.high)
            low_series = pd.Series(self.candle.low)
            self.ichi_2_strategy[kline] = ICHIMOKU_2_Strategy(high_series, low_series, self.candle.close)

        for i, p in self.param.items():
            self.ichi_2_strategy[i].ComputeIchimoku_A(p["Win1"], p["Win2"])
            self.ichi_2_strategy[i].ComputeIchimoku_B(p["Win2"], p["Win3"])
            self.ichi_2_strategy[i].ComputeIchimoku_Base_Line(p["Win1"], p["Win2"])
            self.ichi_2_strategy[i].ComputeIchimoku_Conversion_Line(p["Win1"], p["Win2"])

        self.LastTimeOfCandle = self.candle.timeUTC[-1]

    def UpdateCandle(self, msg):
        if msg['e'] == 'error':
            print(msg)
            self.bsm.stop_socket(self.conn_key)
            self.conn_key = self.bsm.start_kline_socket(self.currency_pair, self.UpdateCandle,
                                                        interval=Client.KLINE_INTERVAL_1HOUR)
        else:
            time = datetime.datetime.utcfromtimestamp(msg["k"]["t"] / 1000)
            if time > self.LastTimeOfCandle:
                for i, p in self.param.items():
                    self.ichi_2_strategy[i].high_data.pop(0)
                    self.ichi_2_strategy[i].high_data.reset_index(drop=True, inplace=True)
                    self.ichi_2_strategy[i].low_data.pop(0)
                    self.ichi_2_strategy[i].low_data.reset_index(drop=True, inplace=True)
                    self.ichi_2_strategy[i].close_data = numpy.delete(self.ichi_2_strategy[i].close_data, 0)


                    self.ichi_2_strategy[i].high_data = \
                        self.ichi_2_strategy[i].high_data.append(pd.Series(float(msg["k"]["h"])), ignore_index=True)
                    self.ichi_2_strategy[i].low_data = \
                        self.ichi_2_strategy[i].low_data.append(pd.Series(float(msg["k"]["l"])), ignore_index=True)
                    self.ichi_2_strategy[i].close_data = numpy.append(self.ichi_2_strategy[i].close_data, float(msg["k"]["c"]))

                    self.ichi_2_strategy[i].ComputeIchimoku_A(p["Win1"], p["Win2"])
                    self.ichi_2_strategy[i].ComputeIchimoku_B(p["Win2"], p["Win3"])
                    self.ichi_2_strategy[i].ComputeIchimoku_Base_Line(p["Win1"], p["Win2"])
                    self.ichi_2_strategy[i].ComputeIchimoku_Conversion_Line(p["Win1"], p["Win2"])

                self.LastTimeOfCandle = time

                FileWorking.Write(datetime.datetime.now())
                print(datetime.datetime.now())

    def BuyOrderCondition(self, currency_pair):
        return self.ichi_2_strategy[currency_pair].BuyStrategy(len(self.ichi_2_strategy[currency_pair].close_data) - 1,
                                                               self.t, self.a, self.b)

    def SellOrderCondition(self, currency_pair):
        return self.ichi_2_strategy[currency_pair].SellStrategy(len(self.ichi_2_strategy[currency_pair].close_data) - 1,
                                                                self.t)

    def FindBuySignal(self, currency_pair):
        Buy_Signal = []
        for i in currency_pair:  # for name, age in dictionary.iteritems():  (for Python 2.x)
            if self.BuyOrderCondition(i):
                Buy_Signal.append(i)
        return Buy_Signal

    def FindDiffrentBuySignal(self, source_1, source_2):
        return list(set(source_2) - set(source_1))

    def FindSellSignal(self, currency_pair):
        Sell_Signal = []
        for i in currency_pair:  # for name, age in dictionary.iteritems():  (for Python 2.x)
            if self.SellOrderCondition(i):
                Sell_Signal.append(i)
        return Sell_Signal

    def CheckAllPos(self, pos):
        for _,i in pos.items():
            if not i:
                return False
        return True

    def RunTradeThread(self):
        self.InitCandle()

        self.conn_key = self.bsm.start_kline_socket(self.currency_pair, self.UpdateCandle,
                                                    interval=Client.KLINE_INTERVAL_1HOUR)
        if not self.bsm.is_alive():
            self.bsm.start()

        try:
            th = threading.Thread(target=self.RunTrade, args=())
            th.start()
        except:
            print("Error: unable to start thread")


    def RunTrade(self):
        isPosition = {}
        for i in self.currency_pair_secondery:
            last_trade = self.client.get_my_trades(symbol=i)
            if len(last_trade) > 0 and last_trade[-1]['isBuyer']:
                isPosition[self.correspond[i]] = True
            else:
                isPosition[self.correspond[i]] = False
        currency_balance = {}
        buy_price = {}
        balance = {"Current": 0, "Available": 0}
        for i in self.currency:
            currency_balance[i] = self.GetBalance(i)
        check_quntity_available = lambda x: x if x > balance["Available"] else balance["Available"]
        check_quntity_min = lambda x: x if x > 10 else 10
        localtime = datetime.datetime.now()
        while True:
            time.sleep(0.5)
            try:
                if abs(datetime.now() - localtime) > datetime.timedelta(minutes=15):
                    print(datetime.now(), "   Thread is Run!!!")
                    localtime = datetime.datetime.now()
                if self.BuyOrderCondition(self.currency_pair[0]) and not self.CheckAllPos(isPosition[1:]):
                    balance["Current"] = 0
                    balance["Available"] = self.GetBalance(self.currency[-1])
                    # for i in self.currency[:-1]:
                    #     balance["Available"] += self.GetBalance(i) * self.GetPrice(i+self.currency[-1])
                    Buy_Signal = self.FindBuySignal(self.currency_pair_secondery)
                    if len(Buy_Signal) > 0:
                        for i in Buy_Signal:
                            # buy_price[i] = self.GetPrice(i)
                            buy_price[self.correspond[i]] = self.GetPrice(self.correspond[i])
                            if balance["Available"] > 10:
                                q = check_quntity_min((balance["Available"] + balance["Current"]) / len(Buy_Signal))
                                quntity = q / buy_price[self.correspond[i]]
                                order = self.SetMarketBuyOrder(self.correspond[i], round(quntity, 5))
                                print(order)
                                # currency_balance[self.correspond[self.correspond[i]]]
                                balance["Available"] -= q
                                balance["Current"] += q
                                isPosition[self.correspond[i]] = True
                    else:
                        buy_price[self.currency_pair[0]] = self.GetPrice(self.currency_pair[0])
                        if balance["Available"] > 10:
                            quntity = balance["Available"] / buy_price[i]
                            order = self.SetMarketBuyOrder(self.currency_pair[0], round(quntity, 5))
                            print(order)
                            # currency_balance[self.currency[0]] = quntity
                            balance["Current"] = balance["Available"]
                            balance["Available"] = 0
                            isPosition[self.currency_pair[0]] = True
                if isPosition[self.currency_pair[0]]:
                    if self.SellOrderCondition(self.currency_pair[0]):
                        currency_balance[self.currency[0]] = self.GetBalance(self.currency[0])
                        order = self.SetMarketSellOrder(self.currency_pair[0], round(currency_balance[self.currency[0]], 5))
                        print(order)
                        # balance["Available"] += currency_balance[self.currency[0]] * self.GetPrice(self.currency_pair[0])
                        isPosition[self.currency_pair[0]] = False
                    else:
                        Buy_Signal = self.FindBuySignal(self.currency_pair_secondery)
                        if len(Buy_Signal) > 0:
                            balance["Current"] = 0
                            balance["Available"] = self.GetBalance(self.currency_pair[0])
                            for i in Buy_Signal:
                                buy_price[i] = self.GetPrice(i)
                                if balance["Available"] > 0.00001:
                                    quntity = (balance["Available"] + balance["Current"]) / len(Buy_Signal)
                                    if quntity > 0.00001:
                                        order = self.SetMarketBuyOrder(i, round(quntity / buy_price[i], 5))
                                        print(order)
                                        currency_balance[self.correspond[self.correspond[i]]] = quntity / buy_price[i]
                                    balance["Available"] -= quntity
                                    balance["Current"] += quntity
                                    isPosition[self.correspond[i]] = True
                elif self.CheckAllPos(isPosition):
                    if self.SellOrderCondition(self.currency_pair[0]):
                        for c, i in isPosition.items():
                            if i:
                                currency_balance[self.correspond[self.correspond[c]]] =\
                                    self.GetBalance(self.correspond[self.correspond[c]])
                                order = self.SetMarketSellOrder(
                                    self.correspond[c], round(currency_balance[self.correspond[self.correspond[c]]], 5))
                                print(order)
                                isPosition[self.correspond[c]] = False
                    else:
                        Sell_Signal = self.FindSellSignal(Buy_Signal)
                        if len(Sell_Signal) > 0:
                            for i in Sell_Signal:
                                currency_balance[self.correspond[self.correspond[i]]] = \
                                    self.GetBalance(self.correspond[self.correspond[i]])
                                order = self.SetMarketSellOrder(
                                    i, round(currency_balance[self.correspond[self.correspond[i]]], 5))
                                print(order)
                                isPosition[self.correspond[i]] = False
                            # Buy_Signal_New = self.FindBuySignal(self.currency_pair_secondery)
                            # if len(Buy_Signal_New) > 0:
                            Buy_Signal_New = []
                            for c, i in isPosition.items():
                                if i:
                                    Buy_Signal_New.append(c)
                            if len(Buy_Signal_New) > 0:
                                balance["Current"] = 0
                                balance["Available"] = self.GetBalance(self.currency_pair[0])
                                for i in Buy_Signal_New:
                                    buy_price[i] = self.GetPrice(i)
                                    if balance["Available"] > 0.00001:
                                        quntity = (balance["Available"] + balance["Current"]) / len(Buy_Signal)
                                        if quntity > 0.00001:
                                            order = self.SetMarketBuyOrder(i, round(quntity / buy_price[i], 5))
                                            print(order)
                                            currency_balance[self.correspond[self.correspond[i]]] += quntity / buy_price[
                                                i]
                                        balance["Available"] -= quntity
                                        balance["Current"] += quntity
                                        isPosition[self.correspond[i]] = True
                                Buy_Signal = Buy_Signal_New
                        Buy_Signal_New = self.FindBuySignal(self.currency_pair_secondery)
                        Buy_Signal_New = self.FindDiffrentBuySignal(Buy_Signal, Buy_Signal_New)
                        if len(Buy_Signal_New) > 0:
                            balance["Available"] = 0
                            balance["Current"] = 0
                            for i in Buy_Signal:
                                balance["Available"] += self.GetBalance(self.correspond[self.correspond[i]]) / self.GetPrice(i)
                                # balance["Available"] += currency_balance[self.correspond[self.correspond[i]]] * self.GetPrice(i)
                            for i in Buy_Signal:
                                buy_price[i] = self.GetPrice(i)
                                sell_q = (currency_balance[self.correspond[self.correspond[i]]] * self.GetPrice(i))\
                                         - (balance["Available"] / (len(Buy_Signal) + len(Buy_Signal_New)))
                                order = self.SetMarketSellOrder(i, round(sell_q / buy_price[i], 5))
                                print(order)
                                currency_balance[self.currency_pair[0]] += sell_q
                            balance["Available"] = self.GetPrice(self.currency_pair[0])
                            for i in Buy_Signal_New:
                                buy_price[i] = self.GetPrice(i)
                                if balance["Available"] > 0.00001:
                                    quntity = (balance["Available"] + balance["Current"]) / len(Buy_Signal_New)
                                    if quntity > 0.00001:
                                        order = self.SetMarketBuyOrder(i, round(quntity / buy_price[i], 5))
                                        print(order)
                                    balance["Available"] -= quntity
                                    balance["Current"] += quntity
                                    isPosition[self.correspond[i]] = True
                            Buy_Signal.extend(Buy_Signal_New)
            except ConnectionAbortedError as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except ConnectionError as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except ConnectionResetError as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except BinanceAPIException as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except BinanceWithdrawException as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except BinanceRequestException as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except BinanceOrderException as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except Timeout as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except TooManyRedirects as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
            except RequestException as e:
                FileWorking.Write(self.currency_pair)
                FileWorking.Write(e)
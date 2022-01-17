from datetime import datetime
import threading
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceWithdrawException, BinanceRequestException,\
    BinanceOrderException
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects, RequestException
from kucoin.exceptions import KucoinAPIException
from Strategy import ICHIMOKU_2_Strategy, ICHIMOKU_Strategy_HMA, ICHIMOKU_Strategy_HMA_Keltner
import pandas as pd
import numpy

import time
import datetime
from Algorithm import OnlineAlgorithm
from IO import FileWorking

import sqlite3

class Algo_1(OnlineAlgorithm):
    def __init__(self, exchange, firstCurrency, secondCurrency, ignoreLastTrade):
        super().__init__(exchange)
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
        # klines = self.exchange.GetKlines(self.currency_pair, Client.KLINE_INTERVAL_1HOUR, "10 days ago UTC", "")
        # klines = candle.getKlines("BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "1 hour ago UTC", "")
        # self.candle.unpackCandle(klines)
        self.GetKlines(self.currency_pair, Client.KLINE_INTERVAL_1HOUR, "10 days ago UTC", "")
        high_series = pd.Series(self.exchange.candle.high)
        low_series = pd.Series(self.exchange.candle.low)
        self.close_data = self.exchange.candle.close
        self.ichi_2_strategy = ICHIMOKU_2_Strategy(high_series, low_series, self.close_data)

        self.ichi_2_strategy.ComputeIchimoku_A(self.win1, self.win2)
        self.ichi_2_strategy.ComputeIchimoku_B(self.win2, self.win3)
        self.ichi_2_strategy.ComputeIchimoku_Base_Line(self.win1, self.win2)
        self.ichi_2_strategy.ComputeIchimoku_Conversion_Line(self.win1, self.win2)

        self.LastTimeOfCandle = self.exchange.candle.timeUTC[-1]

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

    def UpdateCandle(self, msg):
        time = datetime.datetime.utcfromtimestamp(msg["Time"] / 1000)
        if time > self.LastTimeOfCandle:
            self.ichi_2_strategy.high_data.pop(0)
            self.ichi_2_strategy.high_data.reset_index(drop=True, inplace=True)
            self.ichi_2_strategy.low_data.pop(0)
            self.ichi_2_strategy.low_data.reset_index(drop=True, inplace=True)
            self.ichi_2_strategy.close_data = numpy.delete(self.ichi_2_strategy.close_data, 0)


            self.ichi_2_strategy.high_data = \
                self.ichi_2_strategy.high_data.append(pd.Series(float(msg["High"])), ignore_index=True)
            self.ichi_2_strategy.low_data = \
                self.ichi_2_strategy.low_data.append(pd.Series(float(msg["Low"])), ignore_index=True)
            self.ichi_2_strategy.close_data = numpy.append(self.ichi_2_strategy.close_data, float(msg["Close"]))

            self.ichi_2_strategy.ComputeIchimoku_A(self.win1, self.win2)
            self.ichi_2_strategy.ComputeIchimoku_B(self.win2, self.win3)
            self.ichi_2_strategy.ComputeIchimoku_Base_Line(self.win1, self.win2)
            self.ichi_2_strategy.ComputeIchimoku_Conversion_Line(self.win1, self.win2)

            self.LastTimeOfCandle = time

            FileWorking.Write(datetime.datetime.now())
            print(datetime.datetime.now())

    def RunTrade(self):
        last_trade = self.exchange.GetMyTrade(self.currency_pair)
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
                    last_trade = self.exchange.GetMyTrade(self.currency_pair)
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
    strategy = {}
    param = {}
    def __init__(self, exchange, currency):
        super().__init__(exchange)
        self.CreateCurrencyPair(currency)
        self.update_candle_event = threading.Event()
        self.update_count = 0

    def SetAlgorithmParam(self, currency_pair, p):
        self.param[currency_pair] = p

    def InitCandle(self):
        for i in self.currency_pair + self.currency_pair_secondery:
            # self.klines[i] = self.candle.getKlines(i, Client.KLINE_INTERVAL_1HOUR, "10 days ago UTC", "")
            self.GetKlines(i, Client.KLINE_INTERVAL_1HOUR, int(datetime.datetime.now().timestamp()) - 864000,
                           int(datetime.datetime.now().timestamp()))

        # for currency, kline in self.klines.items():
        #     self.candle.unpackCandle(kline)
            high_series = pd.Series(numpy.delete(self.exchange.high, -1))
            low_series = pd.Series(numpy.delete(self.exchange.low, -1))
            self.strategy[i] = ICHIMOKU_Strategy_HMA_Keltner(high_series, low_series,
                                                             numpy.delete(self.exchange.close, -1), i)

        self.LastTimeOfCandle = {}
        for i, p in self.param.items():
            self.strategy[i].ComputeIchimoku_A(p["Win1"], p["Win2"])
            self.strategy[i].ComputeIchimoku_B(p["Win2"], p["Win3"])
            self.strategy[i].ComputeIchimoku_Base_Line(p["Win1"], p["Win2"])
            self.strategy[i].ComputeIchimoku_Conversion_Line(p["Win1"], p["Win2"])
            self.strategy[i].ComputeKeltnerChannel(p["keltner_Window"], 12, p["Multi_ATR"])
            self.strategy[i].ComputeMcGinleyDynamic(p["McGinley_Period"])

            self.LastTimeOfCandle[i] = self.exchange.timeUTC[-2]
        self.update_candle_event.set()

    def UpdateCandle(self, msg):
        # time = datetime.datetime.utcfromtimestamp(msg["Time"] / 1000)
        time = msg["Time"]
        # print(time, msg["CurrencyPair"], msg["Close"], msg["High"], msg["Low"])
        # print(self.LastTimeOfCandle[msg["CurrencyPair"]])
        if time > self.LastTimeOfCandle[msg["CurrencyPair"]]:
            # for i in self.currency_pair + self.currency_pair_secondery:
                # self.klines[i] = self.candle.getKlines(i, Client.KLINE_INTERVAL_1HOUR, "10 days ago UTC", "")
            # self.GetKlines(msg["CurrencyPair"], Client.KLINE_INTERVAL_1HOUR,
            #                    int(time.timestamp()) + time.astimezone().utcoffset().seconds - 3600,
            #                int(time.timestamp()) + time.astimezone().utcoffset().seconds)

            self.strategy[msg["CurrencyPair"]].high_data.pop(0)
            self.strategy[msg["CurrencyPair"]].high_data.reset_index(drop=True, inplace=True)
            self.strategy[msg["CurrencyPair"]].low_data.pop(0)
            self.strategy[msg["CurrencyPair"]].low_data.reset_index(drop=True, inplace=True)
            self.strategy[msg["CurrencyPair"]].close_data = numpy.delete(self.strategy[msg["CurrencyPair"]].close_data, 0)

            self.strategy[msg["CurrencyPair"]].high_data = self.strategy[msg["CurrencyPair"]].high_data.append(pd.Series(msg["High"]),
                                                                           ignore_index=True)
            self.strategy[msg["CurrencyPair"]].low_data = self.strategy[msg["CurrencyPair"]].low_data.append(pd.Series(msg["Low"]),
                                                                         ignore_index=True)
            self.strategy[msg["CurrencyPair"]].close_data = numpy.append(self.strategy[msg["CurrencyPair"]].close_data, msg["Close"])

            self.strategy[msg["CurrencyPair"]].ComputeIchimoku_A(self.param[msg["CurrencyPair"]]["Win1"], self.param[msg["CurrencyPair"]]["Win2"])
            self.strategy[msg["CurrencyPair"]].ComputeIchimoku_B(self.param[msg["CurrencyPair"]]["Win2"], self.param[msg["CurrencyPair"]]["Win3"])
            self.strategy[msg["CurrencyPair"]].ComputeIchimoku_Base_Line(self.param[msg["CurrencyPair"]]["Win1"], self.param[msg["CurrencyPair"]]["Win2"])
            self.strategy[msg["CurrencyPair"]].ComputeIchimoku_Conversion_Line(self.param[msg["CurrencyPair"]]["Win1"], self.param[msg["CurrencyPair"]]["Win2"])
            self.strategy[msg["CurrencyPair"]].ComputeKeltnerChannel(self.param[msg["CurrencyPair"]]["keltner_Window"], 12, self.param[msg["CurrencyPair"]]["Multi_ATR"])
            self.strategy[msg["CurrencyPair"]].ComputeMcGinleyDynamic(self.param[msg["CurrencyPair"]]["McGinley_Period"])

            print(datetime.datetime.now(), msg["CurrencyPair"], msg["Close"], msg["High"], msg["Low"])
        # self.update_candle_event.set()
            self.LastTimeOfCandle[msg["CurrencyPair"]] = time
            self.update_count += 1
        if self.update_count == len(self.currency_pair + self.currency_pair_secondery):
            self.update_candle_event.set()
            self.update_count = 0

        # FileWorking.Write(datetime.datetime.now())
        # print(datetime.datetime.now(), msg["CurrencyPair"], msg["Close"])

    def BuyOrderCondition(self, currency_pair):
        # if currency_pair == "BTCUSDT":
        #     return False
        # if currency_pair == "ETHUSDT":
        #     return True
        # if currency_pair == "BNBUSDT":
        #     return True
        # if currency_pair == "ETHBTC":
        #     return True
        # if currency_pair == "BNBBTC":
        #     return True
        return self.strategy[currency_pair].BuyStrategy(len(self.strategy[currency_pair].close_data) - 1,
                                                               self.param[currency_pair]["t"],
                                                               self.param[currency_pair]["a"])

    def SellOrderCondition(self, currency_pair):
        # return not self.BuyOrderCondition(currency_pair)
        # if currency_pair == "BTCUSDT":
        #     return False
        # if currency_pair == "ETHUSDT":
        #     return False
        # if currency_pair == "BNBUSDT":
        #     return False
        # if currency_pair == "ETHBTC":
        #     return False
        # if currency_pair == "BNBBTC":
        #     return False

        return self.strategy[currency_pair].SellStrategy(len(self.strategy[currency_pair].close_data) - 1,
                                                                self.param[currency_pair]["t"])

    def FindBuySignal(self, currency_pair):
        Buy_Signal = []
        for i in currency_pair:
            if self.BuyOrderCondition(i):
                Buy_Signal.append(i)
        return Buy_Signal

    def FindDiffrentBuySignal(self, source_1, source_2):
        return list(set(source_2) - set(source_1))

    def FindSellSignal(self, currency_pair):
        Sell_Signal = []
        for i in currency_pair:
            if self.SellOrderCondition(i):
                Sell_Signal.append(i)
        return Sell_Signal

    def CheckAllPos(self, pos):
        for _,i in pos.items():
            if i:
                return True
        return False

    def SetInitIsPosition(self, currency_balance):
        isPosition = {}
        self.Buy_Signal = []
        if currency_balance[self.currency[0]] * self.GetPrice(self.currency_pair[0]) > 10:
            isPosition[self.currency_pair[0]] = True
        else:
            isPosition[self.currency_pair[0]] = False

        for i in self.currency_pair_secondery:
            if currency_balance[self.correspond[self.correspond[i]]] * self.GetPrice(self.correspond[i]) > 10:
                isPosition[self.correspond[i]] = True
                self.Buy_Signal.append(i)
            else:
                isPosition[self.correspond[i]] = False
        return isPosition

    def RunTradeThread(self):
        self.InitCandle()
        self.CreateWebSocketManager()
        # self.conn_key = {}
        for i, j in self.param.items():
            self.CreateKlineSocket(i, Client.KLINE_INTERVAL_1HOUR)
        # if not self.bsm.is_alive():
        #     self.bsm.start()

        try:
            th = threading.Thread(target=self.RunTrade, args=())
            th.start()
        except:
            print("Error: unable to start thread")


    def RunTrade(self):
        currency_balance = {}
        buy_price = {}
        balance = {"Current": 0, "Available": 0}
        for i in self.currency:
            currency_balance[i] = self.GetBalance(i)

        isPosition = self.SetInitIsPosition(currency_balance)
        check_quntity_min = lambda x: x if x > 10 else 10
        localtime = datetime.datetime.now()
        while True:
            time.sleep(0.5)
            try:
                if abs(datetime.datetime.now() - localtime) > datetime.timedelta(minutes=30):
                    print(datetime.datetime.now(), "   Thread is Run!!!")
                    localtime = datetime.datetime.now()
                if self.BuyOrderCondition(self.currency_pair[0]) and not self.CheckAllPos(isPosition):
                    balance["Current"] = 0
                    balance["Available"] = self.GetBalance(self.currency[-1])
                    self.Buy_Signal = self.FindBuySignal(self.currency_pair_secondery)
                    if len(self.Buy_Signal) > 0:
                        for i in self.Buy_Signal:
                            buy_price[self.correspond[i]] = self.GetPrice(self.correspond[i])
                            if balance["Available"] > 10:
                                q = check_quntity_min((balance["Available"] + balance["Current"]) / len(self.Buy_Signal))
                                quntity = q / buy_price[self.correspond[i]]
                                order = self.SetMarketBuyOrder(self.correspond[i],
                                                               self.SetQuntity(quntity, self.correspond[i]))
                                self.logger.info(order)
                                print(order)
                                balance["Available"] -= q
                                balance["Current"] += q
                                isPosition[self.correspond[i]] = True
                    else:
                        buy_price[self.currency_pair[0]] = self.GetPrice(self.currency_pair[0])
                        if balance["Available"] > 10:
                            quntity = balance["Available"] / buy_price[self.currency_pair[0]]
                            order = self.SetMarketBuyOrder(self.currency_pair[0],
                                                           self.SetQuntity(quntity, self.currency_pair[0]))
                            self.logger.info(order)
                            print(order)
                            balance["Current"] = balance["Available"]
                            balance["Available"] = 0
                            isPosition[self.currency_pair[0]] = True
                if isPosition[self.currency_pair[0]]:
                    if self.SellOrderCondition(self.currency_pair[0]):
                        currency_balance[self.currency[0]] = self.GetBalance(self.currency[0])
                        order = self.SetMarketSellOrder(self.currency_pair[0],
                                                        self.SetQuntity(currency_balance[self.currency[0]],
                                                                                         self.currency_pair[0]))
                        self.logger.info(order)
                        print(order)
                        isPosition[self.currency_pair[0]] = False
                    else:
                        self.Buy_Signal = self.FindBuySignal(self.currency_pair_secondery)
                        if len(self.Buy_Signal) > 0:
                            balance["Current"] = 0
                            balance["Available"] = self.GetBalance(self.currency[0])
                            for i in self.Buy_Signal:
                                buy_price[i] = self.GetPrice(i)
                                if balance["Available"] > 0.00001:
                                    quntity = (balance["Available"] + balance["Current"]) / len(self.Buy_Signal)
                                    if quntity > 0.00001:
                                        order = self.SetMarketBuyOrder(i, self.SetQuntity(quntity / buy_price[i], i))
                                        self.logger.info(order)
                                        print(order)
                                        currency_balance[self.correspond[self.correspond[i]]] = quntity / buy_price[i]
                                    balance["Available"] -= quntity
                                    balance["Current"] += quntity
                                    isPosition[self.correspond[i]] = True
                            isPosition[self.currency_pair[0]] = False
                elif self.CheckAllPos({k: v for k, v in isPosition.items() if k not in {self.currency_pair[0]}}):
                    if self.SellOrderCondition(self.currency_pair[0]):
                        for c, i in list(isPosition.items()):
                            if i:
                                currency_balance[self.correspond[c]] =\
                                    self.GetBalance(self.correspond[c])
                                order = self.SetMarketSellOrder(c, self.SetQuntity(currency_balance[self.correspond[c]],
                                                                                   c))
                                self.logger.info(order)
                                print(order)
                                isPosition[c] = False
                    else:
                        Sell_Signal = self.FindSellSignal(self.Buy_Signal)
                        if len(Sell_Signal) > 0:
                            for i in Sell_Signal:
                                currency_balance[self.correspond[self.correspond[i]]] = \
                                    self.GetBalance(self.correspond[self.correspond[i]])
                                order = self.SetMarketSellOrder(i,
                                                                self.SetQuntity(currency_balance[self.correspond[self.correspond[i]]], i))
                                self.logger.info(order)
                                print(order)
                                isPosition[self.correspond[i]] = False
                            Buy_Signal_New = []
                            for c, i in list(isPosition.items()):
                                if i:
                                    cc = list(self.correspond.keys())[list(self.correspond.values()).index(c)]
                                    Buy_Signal_New.append(cc)
                            if len(Buy_Signal_New) > 0:
                                balance["Current"] = 0
                                balance["Available"] = self.GetBalance(self.currency[0])
                                for i in Buy_Signal_New:
                                    buy_price[i] = self.GetPrice(i)
                                    if balance["Available"] > 0.00001:
                                        quntity = (balance["Available"] + balance["Current"]) / len(Buy_Signal_New)
                                        if quntity > 0.00001:
                                            order = self.SetMarketBuyOrder(i,
                                                                           self.SetQuntity(quntity / buy_price[i], i))
                                            self.logger.info(order)
                                            print(order)
                                            currency_balance[self.correspond[self.correspond[i]]] +=\
                                                quntity / buy_price[i]
                                        balance["Available"] -= quntity
                                        balance["Current"] += quntity
                                        isPosition[self.correspond[i]] = True
                                self.Buy_Signal = Buy_Signal_New
                            else:
                                isPosition[self.currency_pair[0]] = True
                        Buy_Signal_New = self.FindBuySignal(self.currency_pair_secondery)
                        Buy_Signal_New = self.FindDiffrentBuySignal(self.Buy_Signal, Buy_Signal_New)
                        if len(Buy_Signal_New) > 0:
                            balance["Available"] = 0
                            balance["Current"] = 0
                            for i in self.Buy_Signal:
                                balance["Available"] += self.GetBalance(self.correspond[self.correspond[i]]) *\
                                                        self.GetPrice(self.correspond[i])
                            for i in self.Buy_Signal:
                                buy_price[self.correspond[i]] = self.GetPrice(self.correspond[i])
                                sell_q = (currency_balance[self.correspond[self.correspond[i]]] * buy_price[self.correspond[i]])\
                                         - (balance["Available"] / (len(self.Buy_Signal) + len(Buy_Signal_New)))
                                order = self.SetMarketSellOrder(self.correspond[i],
                                                                self.SetQuntity(sell_q / buy_price[self.correspond[i]],
                                                                                self.correspond[i]))
                                self.logger.info(order)
                                print(order)
                                balance["Current"] += sell_q
                            balance["Available"] = balance["Current"]
                            balance["Current"] = 0
                            for i in Buy_Signal_New:
                                buy_price[self.correspond[i]] = self.GetPrice(self.correspond[i])
                                if balance["Available"] > 0.00001:
                                    quntity = (balance["Available"] + balance["Current"]) / len(Buy_Signal_New)
                                    if quntity > 0.00001:
                                        order = self.SetMarketBuyOrder(self.correspond[i],
                                                                       self.SetQuntity(quntity / buy_price[self.correspond[i]],
                                                                                       self.correspond[i]))
                                        self.logger.info(order)
                                        print(order)
                                    balance["Available"] -= quntity
                                    balance["Current"] += quntity
                                    isPosition[self.correspond[i]] = True
                            self.Buy_Signal.extend(Buy_Signal_New)
            except ConnectionAbortedError as e:
                self.LogException(e)
            except ConnectionError as e:
                self.LogException(e)
            except ConnectionResetError as e:
                self.LogException(e)
            except BinanceAPIException as e:
                self.LogException(e)
            except BinanceWithdrawException as e:
                self.LogException(e)
            except BinanceRequestException as e:
                self.LogException(e)
            except BinanceOrderException as e:
                self.LogException(e)
            except Timeout as e:
                self.LogException(e)
            except TooManyRedirects as e:
                self.LogException(e)
            except RequestException as e:
                self.LogException(e)

class Algo_3(Algo_2):

    def __init__(self, exchange, currency):
        super().__init__(exchange, currency)


    def CheckAction(self, Buy_Signal):
        Order = {"Buy": [], "Sell": [], "SellNotAll": []}
        zero_buy_signal = self.GetSpecificBuySignal(Buy_Signal, 0)
        one_buy_signal = self.GetSpecificBuySignal(Buy_Signal, 1)
        two_buy_signal = self.GetSpecificBuySignal(Buy_Signal, 2)
        pos = self.CheckTrueIsPos(self.isPosition)
        if len(pos) == 0 and self.currency[0] in one_buy_signal and len(one_buy_signal + two_buy_signal) == 1:#1
            Order["Buy"] = self.FindKeyFromCurrency(self.currency_pair, self.currency[0])
            # self.isPosition[self.currency[0]] = True
        elif self.currency[0] in pos:#4 6 8
            for i in two_buy_signal:
                Order["Buy"] += self.FindKeyFromCurrency(self.currency_pair_secondery, i)
                # self.isPosition[i] = True
            if self.currency[0] in one_buy_signal:
                for i in one_buy_signal:
                    if i != self.currency[0]:
                        Order["Buy"] += self.FindKeyFromCurrency(self.currency_pair_secondery, i)
                        # self.isPosition[i] = True
            elif self.currency[0] in zero_buy_signal and len(two_buy_signal) == 0:
                Order["Sell"] = self.FindKeyFromCurrency(self.currency_pair, self.currency[0])
                # self.isPosition[self.currency[0]] = False
            # if len(Order["Buy"]) > 0:
                # self.isPosition[self.currency[0]] = False
            return Order
        elif len(pos) > 0 and self.currency[0] not in pos:
            if self.currency[0] in one_buy_signal and len(one_buy_signal + two_buy_signal) == 1:#2
                for i in pos:
                    Order["Sell"] += self.FindKeyFromCurrency(self.currency_pair_secondery, i)
                    # self.isPosition[i] = False
                # self.isPosition[self.currency[0]] = True
            elif self.CheckPosInBuySignal(pos, zero_buy_signal) or \
                    (self.currency[0] in zero_buy_signal and self.CheckPosInBuySignal(pos, one_buy_signal)):#5 7
                currency = self.currency_pair_secondery if self.currency[0] in one_buy_signal else self.currency_pair
                for i in pos:
                    if i in zero_buy_signal or (self.currency[0] in zero_buy_signal and i in one_buy_signal):
                        Order["Sell"] += self.FindKeyFromCurrency(currency, i)
                        # self.isPosition[i] = False
                for i in two_buy_signal:
                    Order["Buy"] += self.FindKeyFromCurrency(currency, i)
                    # self.isPosition[i] = True
                if self.currency[0] in one_buy_signal:
                    for i in one_buy_signal:
                        if i != self.currency[0]:
                            Order["Buy"] += self.FindKeyFromCurrency(currency, i)
                            # self.isPosition[i] = True
        if (len(two_buy_signal) > 0 or len(one_buy_signal) > 1) and \
                self.CheckNewBuy(pos, one_buy_signal, two_buy_signal):#3
            currency = self.currency_pair_secondery if len(pos) > 0 and self.currency[0] in one_buy_signal\
                else self.currency_pair
            for i in two_buy_signal:
                if i in pos:
                    Order["SellNotAll"] += self.FindKeyFromCurrency(currency, i)
                else:
                    if not set(self.FindKeyFromCurrency(currency, i)).issubset(Order["Buy"]):
                        Order["Buy"] += self.FindKeyFromCurrency(currency, i)
                        # self.isPosition[i] = True
            if self.currency[0] in one_buy_signal:
                for i in one_buy_signal:
                    if i in pos and i != self.currency[0]:
                        Order["SellNotAll"] += self.FindKeyFromCurrency(currency, i)
                    elif i != self.currency[0]:
                        Order["Buy"] += self.FindKeyFromCurrency(currency, i)
                        # self.isPosition[i] = True

        return Order

    def ComputeBuySignal(self):
        b = []
        bs = {}
        for i in self.currency_pair + self.currency_pair_secondery:
            if self.currency[-1] in i:
                c = i.replace(self.currency[-1], '')
            else:
                c = i.replace(self.currency[0], '')
            isBuy = self.BuyOrderCondition(i)
            isSell = self.SellOrderCondition(i)
            if isBuy and not isSell:
                b.append(i)
            # if (isBuy and not self.isPosition[c]) or (self.isPosition[c] and not isSell):
            #     b.append(i)

        if self.currency_pair[0] in b:
            bs[self.currency[0]] = 1
        else:
            bs[self.currency[0]] = 0
        for j in self.currency[1:-1]:
            matching = [s for s in b if j in s]
            if len(matching) > 1:
                bs[j] = 2
            elif len(matching) == 1 and matching[0] != j + self.currency[-1]:
                bs[j] = 1
            else:
                bs[j] = 0
        return bs

    def GetSpecificBuySignal(self, Buy_Signal, state):
        return [c for c, s in Buy_Signal.items() if s == state]

    def CheckTrueIsPos(self, isPos):
        return [k for k, s in isPos.items() if s]

    def FindKeyFromCurrency(self, currency_pair, currency):
        return [s for s in currency_pair if currency in s]

    def CheckPosInBuySignal(self, pos, buy_signal_list):
        for i in pos:
            if i in buy_signal_list:
                return True
        return False

    def CheckNewBuy(self, pos, one_buy_signal, two_buy_signal):
        for i in two_buy_signal:
            if i not in pos:
                return True
        for i in one_buy_signal:
            if self.currency[0] in one_buy_signal and i != self.currency[0]:
                if i not in pos:
                    return True
        return False

    def RunTradeThread(self):
        self.InitCandle()
        c = threading.Thread(target=self.CreateWebSocketManager, args=())
        c.start()
        # self.CreateWebSocketManager()
        # self.conn_key = {}
        # time.sleep(5)
        # for i in self.currency_pair + self.currency_pair_secondery:
        #     # self.CreateKlineSocket(i, Client.KLINE_INTERVAL_1HOUR)
        #     k = threading.Thread(target=self.CreateKlineSocket, args=(i, Client.KLINE_INTERVAL_1HOUR))
        #     k.start()
        #     time.sleep(1)
        #     self.conn_key[i] = self.bsm.start_kline_socket(i, self.UpdateCandle,
        #                                                 interval=Client.KLINE_INTERVAL_1HOUR)
        # if not self.bsm.is_alive():
        #     self.bsm.start()

        try:
            th = threading.Thread(target=self.RunTrade, args=())
            th.start()
        except:
            print("Error: unable to start thread")

    def SetIsPosition(self, currency_balance):
        is_position = {}
        for i in self.currency[:-1]:
            if currency_balance[i] * self.GetPrice(i + self.currency[-1]) > 10:
                is_position[i] = True
            else:
                is_position[i] = False
        return is_position

    def RunTrade(self):
        currency_balance = {}
        localtime = datetime.datetime.now()
        while True:
            time.sleep(1)
            try:
                # if abs(datetime.datetime.now() - localtime) > datetime.timedelta(minutes=3):
                #     # print(datetime.datetime.now(), "    Thread is run!!!")
                #     localtime = datetime.datetime.now()
                #     for i in self.currency_pair + self.currency_pair_secondery:
                #         if localtime - self.LastTimeOfCandle[i] > datetime.timedelta(minutes=60):
                #             self.StopAllKlineSocket()
                #             time.sleep(21)
                #             self.exchange.close_websocket = False
                #             time.sleep(21)
                #             c = threading.Thread(target=self.CreateWebSocketManager, args=())
                #             c.start()
                #             time.sleep(2)
                #             for i in self.currency_pair + self.currency_pair_secondery:
                #                 k = threading.Thread(target=self.CreateKlineSocket, args=(i, Client.KLINE_INTERVAL_1HOUR))
                #                 k.start()
                #                 time.sleep(1)
                #             print(datetime.datetime.now(), "    ReCreate Kline Socket!!!")
                #             self.logger.info("ReCreate Kline Socket!!!")
                #             break
                if self.update_candle_event.is_set():
                    self.update_candle_event.clear()
                    print(datetime.datetime.now(), "    Event was set!!!")
                    for i in self.currency:
                        currency_balance[i] = self.GetBalance(i)

                    self.isPosition = self.SetIsPosition(currency_balance)

                    buy_signal = self.ComputeBuySignal()
                    print(buy_signal)
                    action = self.CheckAction(buy_signal)
                    print(action)
                    if len(action["Sell"]) > 0 or len(action["SellNotAll"]) > 0 or len(action["Buy"]) > 0:
                        self.logger.info(action)
                    for j in action["Sell"]:
                        if self.currency[-1] in j:
                            c = j.replace(self.currency[-1], '')
                        else:
                            c = j.replace(self.currency[0], '')
                        currency_balance[c] = self.GetBalance(c)
                        order = self.SetMarketSellOrder(j, self.SetQuntity(self.GetBalance(c), j))
                        self.logger.info(order)
                        print(order)
                    time.sleep(3)
                    for j in action["SellNotAll"]:
                        if self.currency[-1] in j:
                            c = j.replace(self.currency[-1], '')
                        else:
                            c = j.replace(self.currency[0], '')
                        currency_balance[c] = self.GetBalance(c)
                        cb = (currency_balance[c] / len(action["SellNotAll"] + action["Buy"])) * len(action["Buy"])
                        order = self.SetMarketSellOrder(j, self.SetQuntity(cb, j))
                        self.logger.info(order)
                        print(order)
                    time.sleep(3)
                    for i, j in enumerate(action["Buy"]):
                        if self.currency[-1] in j:
                            c = self.currency[-1]
                        else:
                            c = self.currency[0]
                        if i == 0:
                            currency_balance[c] = self.GetBalance(c)
                        order = self.SetMarketBuyOrder(j, self.SetQuntity((currency_balance[c] / len(action["Buy"])) /
                                                                          self.GetPrice(j), j))
                        self.logger.info(order)
                        print(order)
            except ConnectionAbortedError as e:
                self.LogException(e)
            except ConnectionError as e:
                self.LogException(e)
            except ConnectionResetError as e:
                self.LogException(e)
            except BinanceAPIException as e:
                self.LogException(e)
            except BinanceWithdrawException as e:
                self.LogException(e)
            except BinanceRequestException as e:
                self.LogException(e)
            except BinanceOrderException as e:
                self.LogException(e)
            except Timeout as e:
                self.LogException(e)
            except TooManyRedirects as e:
                self.LogException(e)
            except RequestException as e:
                self.LogException(e)
            except KucoinAPIException as e:
                self.LogException(e)

class Algo_4(Algo_3):

    def __init__(self, exchange, currency):
        super().__init__(exchange, currency)
        self.update_candle_event = {}
        for i in self.currency[:-1]:
            self.update_candle_event[i + self.currency[-1]] = threading.Event()

    def SetAlgorithmParam(self):
        s = [36, 360, 480, 720]
        e = [360, 480, 720, 2160]
        w = [36, 48, 72, 216]
        self.param["4Hour"] = {"S": s, "E": e, "W": w, "Priority": 1}

    def InitCandle(self):
        self.LastTimeOfCandle = {}
        for i in self.currency_pair:
            # self.klines[i] = self.candle.getKlines(i, Client.KLINE_INTERVAL_1HOUR, "10 days ago UTC", "")
            self.GetKlines(i, Client.KLINE_INTERVAL_1HOUR, int(datetime.datetime.now().timestamp()) - 7776000,
                           int(datetime.datetime.now().timestamp()))

            high_series = pd.Series(numpy.delete(self.exchange.high, -1))
            low_series = pd.Series(numpy.delete(self.exchange.low, -1))
            close_series = pd.Series(numpy.delete(self.exchange.close, -1))
            open_series = pd.Series(numpy.delete(self.exchange.open, -1))
            time_series = pd.Series(numpy.delete(self.exchange.timeUTC, -1))
            self.strategy[i] = ICHIMOKU_Strategy_HMA_Keltner(high_series, low_series, close_series, open_series,
                                                             time_series , i)

            self.strategy[i].ComputeATR(12)
            self.strategy[i].ComputeIchimoku_A(216, 624)
            self.strategy[i].ComputeIchimoku_B(624, 1248)
            self.strategy[i].ComputeIchimoku_Base_Line(216, 624)
            self.strategy[i].ComputeIchimoku_Conversion_Line(216, 624)
            self.strategy[i].ComputeSuperTrend(12, 3)

            self.LastTimeOfCandle[i] = self.exchange.timeUTC[-2]
            self.update_candle_event[i].set()

    def UpdateCandle(self, msg):
        time = msg["Time"]
        if time > self.LastTimeOfCandle[msg["CurrencyPair"]]:
            self.strategy[msg["CurrencyPair"]].high_data.pop(0)
            self.strategy[msg["CurrencyPair"]].high_data.reset_index(drop=True, inplace=True)
            self.strategy[msg["CurrencyPair"]].low_data.pop(0)
            self.strategy[msg["CurrencyPair"]].low_data.reset_index(drop=True, inplace=True)
            self.strategy[msg["CurrencyPair"]].close_data.pop(0)
            self.strategy[msg["CurrencyPair"]].close_data.reset_index(drop=True, inplace=True)
            # self.strategy[msg["CurrencyPair"]].close_data = numpy.delete(self.strategy[msg["CurrencyPair"]].close_data, 0)

            self.strategy[msg["CurrencyPair"]].high_data = self.strategy[msg["CurrencyPair"]].high_data.append(pd.Series(msg["High"]),
                                                                           ignore_index=True)
            self.strategy[msg["CurrencyPair"]].low_data = self.strategy[msg["CurrencyPair"]].low_data.append(pd.Series(msg["Low"]),
                                                                         ignore_index=True)
            self.strategy[msg["CurrencyPair"]].close_data = self.strategy[msg["CurrencyPair"]].close_data.append(pd.Series(msg["Close"]),
                                                                         ignore_index=True)
            # self.strategy[msg["CurrencyPair"]].close_data = numpy.append(self.strategy[msg["CurrencyPair"]].close_data, msg["Close"])

            self.strategy[msg["CurrencyPair"]].ComputeATR(12)
            self.strategy[msg["CurrencyPair"]].ComputeIchimoku_A(216, 624)
            self.strategy[msg["CurrencyPair"]].ComputeIchimoku_B(624, 1248)
            self.strategy[msg["CurrencyPair"]].ComputeIchimoku_Base_Line(216, 624)
            self.strategy[msg["CurrencyPair"]].ComputeIchimoku_Conversion_Line(216, 624)
            self.strategy[msg["CurrencyPair"]].ComputeSuperTrend(12, 3)

            print(datetime.datetime.now(), msg["CurrencyPair"], msg["Close"], msg["High"], msg["Low"])
            self.LastTimeOfCandle[msg["CurrencyPair"]] = time
            # self.update_count += 1
        # if self.update_count == len(self.currency_pair):
            self.update_candle_event[msg["CurrencyPair"]].set()
            # self.update_count = 0

    def Calculate_R_S_T(self, currency_pair):
        input_max = []
        input_min = []
        atr = self.strategy[currency_pair].atr

        result_max, result_min = self.CalculateMinMax(input_max, input_min, self.param["4Hour"])
        final_result = self.RangeForCloseData(result_max, result_min, atr.iat[-1])
        R, S, T = self.CreateRS(final_result, self.close_data[-1])
        return R, S, T

    def CheckAction(self, R, S, T, currency, isPos):
        order = ""
        volume = 0
        currency_pair = currency + self.currency[-1]
        balance = {"USDT": self.GetBalance(self.currency[-1]), "Currency": self.GetCurrencyBalance()}
        atr = self.strategy[currency_pair].atr
        if len(R) == 0:
            R.append({"Range": [999900, 1000000, 1000100], "Priority": 100})
        if isPos:
            if len(R) > 0 and R[0]["Range"][1] < self.database_data[currency_pair]["TP"] and len(T) == 0:
                self.database_data[currency_pair]["TP"] = R[0]["Range"][0]
                self.database_data[currency_pair]["Valid_ExitCondition2"] = False
            if len(R) > 0 and self.database_data[currency_pair]["TP"] < self.high_data[-1]:
                self.database_data[currency_pair]["Valid_ExitCondition2"] = True
            if len(S) > 0 and S[-1]["Range"][1] > self.database_data[currency_pair]["SL"]:
                self.database_data[currency_pair]["SL"] = S[-1]["Range"][0]
                self.database_data[currency_pair]["Valid_ExitCondition2"] = False
            if self.close_data[-1] - atr.iat[-1] > self.database_data[currency_pair]["Buy_Price"] and\
                    self.database_data[currency_pair]["TS"] < self.close_data[-1] - atr.iat[-1]:
                self.database_data[currency_pair]["TS"] = self.close_data[-1] - atr.iat[-1]
            if (self.database_data[currency_pair]["Valid_ExitCondition2"] and
                self.ExitCondition_2(self.database_data[currency_pair]["TP"], atr, T)) or \
                    self.ExitCondition_1(self.database_data[currency_pair]["SL"]) or self.ExitCondition_3(R, T) \
                    or self.ExitCondition_4(R, T) or self.ExitCondition_5(R, T, self.database_data[currency_pair]["TS"]):
                self.database_data[currency_pair]["Valid_ExitCondition2"] = False
                order = "Sell"
        elif self.EnterCondition_1_4(S) and self.EnterCondition_2(T) and \
                self.EnterCondition_3(R, atr):
            buy_ratio = 0.005 / ((self.close_data[-1] - S[-1]["Range"][0]) / self.close_data[-1])
            volume = buy_ratio * (balance["USDT"] + balance["Currency"])
            if balance["USDT"] > volume and volume > 10:
                volume = balance["USDT"]
            elif balance["USDT"] < 10:
                return order, volume
            self.database_data[currency_pair]["Valid_ExitCondition2"] = False
            self.database_data[currency_pair]["SL"] = S[-1]["Range"][0]
            self.database_data[currency_pair]["TP"] = R[0]["Range"][0]
            order = "Buy"
        return order, volume

    def EnterCondition_1_1(self, S):
        if len(S) == 0:
            return False
        index = len(self.close_data) - 1
        if self.close_data[index - 1] < self.open_data[index - 1] \
                and self.high_data[index - 1] - self.open_data[index - 1] <= self.open_data[index - 1] - self.close_data[index - 1] \
                and self.close_data[index - 1] - self.low_data[index - 1] <= self.open_data[index - 1] - self.close_data[index - 1] \
                and self.high_data[index] - self.close_data[index] <= self.close_data[index] - self.open_data[index] \
                and self.open_data[index] - self.low_data[index] <= self.close_data[index] - self.open_data[index] \
                and self.open_data[index] < self.close_data[index] \
                and self.close_data[index] > self.open_data[index - 1] \
                and self.high_data[index] > self.high_data[index - 1] \
                and self.low_data[index - 1] <= S[-1]["Range"][2] < self.close_data[index]\
                and (self.close_data[index - 2] > S[-1]["Range"][2] or self.close_data[index - 3] > S[-1]["Range"][2]):
            self.enter_number = 1
            return True
        else:
            return False
    def EnterCondition_1_2(self, S):
        if len(S) == 0:
            return False
        index = len(self.close_data) - 1
        if self.close_data[index - 2] < self.open_data[index - 2] \
                and self.high_data[index - 1] <= self.open_data[index - 2] \
                and numpy.abs(self.open_data[index - 1] - self.close_data[index - 1]) <= (self.open_data[index - 2] - self.close_data[index - 2])/5 \
                and self.close_data[index] > self.open_data[index] \
                and self.close_data[index] > self.open_data[index - 2] \
                and (self.open_data[index - 2] > S[-1]["Range"][2] or self.open_data[index - 3] > S[-1]["Range"][2]
                     or self.open_data[index - 4] > S[-1]["Range"][2] or self.open_data[index - 3] > S[-1]["Range"][2])\
                and (self.low_data[index] <= S[-1]["Range"][2] or self.low_data[index - 1] <= S[-1]["Range"][2]
                     or self.low_data[index - 2] <= S[-1]["Range"][2]):
            self.enter_number = 2
            return True
        else:
            return False

    def EnterCondition_1_3(self, S):
        if len(S) == 0:
            return False
        index = len(self.close_data) - 1
        if self.close_data[index - 3] < self.open_data[index - 3]\
                and self.close_data[index - 2] < self.open_data[index - 2]\
                and self.close_data[index - 1] < self.open_data[index - 1]\
                and self.close_data[index] > self.open_data[index]\
                and self.close_data[index] > self.open_data[index - 3]\
                and self.close_data[index] > S[-1]["Range"][2]\
                and (self.low_data[index] <= S[-1]["Range"][2] or self.low_data[index - 1] <= S[-1]["Range"][2]
                     or self.low_data[index - 2] <= S[-1]["Range"][2] or self.low_data[index - 3] <= S[-1]["Range"][2]):
            self.enter_number = 3
            return True
        else:
            return False

    def EnterCondition_1_4(self, S):
        if len(S) == 0:
            return False
        index = len(self.close_data) - 1
        if self.close_data[index] > S[-1]["Range"][2] > self.low_data[index] \
                and self.close_data[index] > self.open_data[index]:
             #for i in range(1, 9):
                #if S[-1]["Range"][1] < self.close_data[index - i]:
            self.enter_number = 4
            return True
        else:
            return False

    def EnterCondition_2(self, T):
        if len(T) == 0:
            return True
        else:
            return False

    def EnterCondition_3(self, R, atr):
        if len(R) == 0:
            return False
        index = len(self.close_data) - 1
        if (R[0]["Range"][0] - self.close_data[index]) > atr[index]:
            return True
        else:
            return False

    def EnterCondition_4(self, R, S):
        if len(S) == 0 or len(R) == 0:
            return False
        index = len(self.close_data) - 1
        if (R[0]["Range"][0] - self.close_data[index]) / (self.close_data[index] - S[-1]["Range"][0]) > 1:
            return True
        else:
            return False

    def ExitCondition_1(self, sl):
        index = len(self.close_data) - 1
        if self.close_data[index] < sl:
            self.exit_number = 1
            return True
        else:
            return False

    def ExitCondition_2(self, tp, atr, T):
        index = len(self.close_data) - 1
        if tp - self.close_data[index] > atr[index] and len(T) > 0:
            self.exit_number = 2
            return True
        else:
            return False

    def ExitCondition_3(self, R, T):
        if len(R) == 0 or len(T) > 0:
            return False
        index = len(self.close_data) - 1
        if self.close_data[index - 1] > self.open_data[index - 1] \
                and self.high_data[index - 1] - self.close_data[index - 1] <= self.close_data[index - 1] - self.open_data[index - 1] \
                and self.open_data[index - 1] - self.low_data[index - 1] <= self.close_data[index - 1] - self.open_data[index - 1] \
                and self.high_data[index] - self.open_data[index] <= self.open_data[index] - self.close_data[index] \
                and self.close_data[index] - self.low_data[index] <= self.open_data[index] - self.close_data[index] \
                and self.open_data[index] > self.close_data[index] \
                and self.close_data[index] < self.open_data[index - 1] \
                and (self.high_data[index - 1] >= R[0]["Range"][0] or self.high_data[index] >= R[0]["Range"][0]) \
                and self.close_data[index] < R[0]["Range"][0]:
            self.exit_number = 3
            return True
        else:
            return False

    def ExitCondition_4(self, R, T):
        if len(R) == 0 or len(T) > 0:
            return False
        index = len(self.close_data) - 1
        if self.close_data[index] < R[0]["Range"][0] < self.open_data[index] \
                and self.close_data[index] < self.open_data[index]:
            self.exit_number = 4
            return True
        else:
            return False

    def ExitCondition_5(self, R, T, TS):
        if len(R) == 0 or len(T) > 0 or R[0]["Priority"] != 100:
            return False
        index = len(self.close_data) - 1
        if self.close_data[index] < TS:
            self.exit_number = 5
            return True
        else:
            return False

    def CalculateMinMax(self, input_max, input_min, param):
        result_max = []
        result_min = []
        close = self.close_data[::-1]
        time = self.candle_time[::-1]
        for j, _ in enumerate(param["S"]):
            if len(self.close_data) >= param["E"][j] + param["W"][j]:
                for i in range(param["S"][j], param["E"][j]):
                    index_max = numpy.where(close[i - param["W"][j]:i + param["W"][j]] ==
                                            numpy.amax(close[i - param["W"][j]:i + param["W"][j]]))
                    index_min = numpy.where(close[i - param["W"][j]:i + param["W"][j]] ==
                                            numpy.amin(close[i - param["W"][j]:i + param["W"][j]]))
                    if (index_max[0] + (i - param["W"][j]) == i).any():
                        find = False
                        for x in result_max + input_max:
                            if x["Time"] == time[i]:
                                find = True
                        if not find:
                            result_max.append({"Close": close[i], "Time": time[i], "Priority": param["Priority"]})
                    if (index_min[0] + (i - param["W"][j]) == i).any():
                        find = False
                        for x in result_min + input_min:
                            if x["Time"] == time[i]:
                                find = True
                        if not find:
                            result_min.append({"Close": close[i], "Time": time[i], "Priority": param["Priority"]})
            else:
                break
        max = input_max + result_max
        min = input_min + result_min
        max.sort(key=lambda x: x["Close"])
        min.sort(key=lambda x: x["Close"])
        return max, min

    def RangeForCloseData(self, max, min, atr):
        data = max + min
        for i in data:
            i["Close"] = [i["Close"]-atr/2, i["Close"], i["Close"]+atr/2]
        data.sort(key=lambda x: x["Close"][1])
        # print(data)
        result = []
        while len(data) > 0:
            temp = data[0]["Close"]
            priority = data[0]["Priority"]
            data.pop(0)
            must_removed = []
            for i in data:
                if i["Close"][0] > temp[2] or i["Close"][2] < temp[0]:
                    continue
                else:
                    if temp[0] >= i["Close"][0]:
                        temp[0] = i["Close"][0]
                    if temp[2] <= i["Close"][2]:
                        temp[2] = i["Close"][2]
                    priority += i["Priority"]
                    must_removed.append(i)
            for j in must_removed:
                data.remove(j)
            result.append({"Range": temp, "Priority": priority})
        return result

    def CreateRS(self, input, close_data):
        R = []
        S = []
        T = []
        for i in input:
            if i["Range"][0] > close_data:
                R.append(i)
            elif i["Range"][2] < close_data:
                S.append(i)
            else:
                T.append(i)
        return R, S, T

    def SetIsPosition(self, currency, currency_balance):
        is_position = False
        if currency_balance[currency] * self.GetPrice(currency + self.currency[-1]) > 10:
            is_position = True
        return is_position

    def GetCurrencyBalance(self):
        balance = 0
        for i in self.currency[:-1]:
            balance += self.GetBalance(i) * self.GetPrice(i+self.currency[-1])
        return balance

    def SetOrder(self, order, volume, currency_pair):
        if order == "Buy":
            buy_price = self.GetPrice(currency_pair)
            order = self.SetMarketBuyOrder(currency_pair,
                                           self.SetQuntity(volume / buy_price, currency_pair))
            self.database_data[currency_pair]["Buy_Price"] = buy_price
            self.logger.info(order)
            print(order)
        if order == "Sell":
            order = self.SetMarketSellOrder(currency_pair,
                                            self.SetQuntity(self.GetBalance(currency_pair), currency_pair))
            self.logger.info(order)
            print(order)

    def RunTrade(self):
        currency_balance = {}
        isPosition = {}
        self.database_data = {}
        for c in self.currency[:-1]:
            self.database_data[c + self.currency[-1]] = {}
            self.database_data[c + self.currency[-1]]["Buy_Price"] = 0
            self.database_data[c + self.currency[-1]]["TP"] = 1000000
            self.database_data[c + self.currency[-1]]["SL"] = 0
            self.database_data[c + self.currency[-1]]["TS"] = 0
            self.database_data[c + self.currency[-1]]["Valid_ExitCondition2"] = False
        localtime = datetime.datetime.now()
        self.db = sqlite3.connect('database.db')
        self.db_cur = self.db.cursor()
        self.db_cur.execute('''CREATE TABLE IF NOT EXISTS log
                       (Currency text PRIMARY KEY , Buy_Price double, TP double, SL double, TS double,
                        Valid_ExitCondition2 bool)''')
        self.db_cur.execute("SELECT * FROM log")
        rows = self.db_cur.fetchall()
        for r in rows:
            self.database_data[r[0]] = {}
            self.database_data[r[0]]["Buy_Price"] = r[1]
            self.database_data[r[0]]["TP"] = r[2]
            self.database_data[r[0]]["SL"] = r[3]
            self.database_data[r[0]]["TS"] = r[4]
            self.database_data[r[0]]["Valid_ExitCondition2"] = r[5]
        self.InsertToDatabase()
        update_candle_set = False
        while True:
            time.sleep(1)
            try:
                for i in self.currency[:-1]:
                    if self.update_candle_event[i + self.currency[-1]].is_set():
                        update_candle_set = True
                        self.update_candle_event[i + self.currency[-1]].clear()
                        print(datetime.datetime.now(), i + self.currency[-1], " Event was set!!!")
                        currency_balance[self.currency[-1]] = self.GetBalance(self.currency[-1])
                        self.close_data = numpy.array(self.strategy[i+self.currency[-1]].close_data.values.tolist())
                        self.candle_time = numpy.array(self.strategy[i+self.currency[-1]].time_data.values.tolist())
                        self.high_data = numpy.array(self.strategy[i+self.currency[-1]].high_data.values.tolist())
                        self.low_data = numpy.array(self.strategy[i+self.currency[-1]].low_data.values.tolist())
                        self.open_data = numpy.array(self.strategy[i+self.currency[-1]].open_data.values.tolist())
                        currency_balance[i] = self.GetBalance(i)
                        isPosition[i] = self.SetIsPosition(i, currency_balance)
                        R, S, T = self.Calculate_R_S_T(i+self.currency[-1])
                        order, volume = self.CheckAction(R, S, T, i, isPosition[i])
                        self.SetOrder(order, volume, i + self.currency[-1])
                if update_candle_set:
                    update_candle_set = False
                    self.UpdateDatabase()
            except ConnectionAbortedError as e:
                self.LogException(e)
            except ConnectionError as e:
                self.LogException(e)
            except ConnectionResetError as e:
                self.LogException(e)
            except BinanceAPIException as e:
                self.LogException(e)
            except BinanceWithdrawException as e:
                self.LogException(e)
            except BinanceRequestException as e:
                self.LogException(e)
            except BinanceOrderException as e:
                self.LogException(e)
            except Timeout as e:
                self.LogException(e)
            except TooManyRedirects as e:
                self.LogException(e)
            except RequestException as e:
                self.LogException(e)
            except KucoinAPIException as e:
                self.LogException(e)

    def UpdateDatabase(self):
        for k, v in self.database_data.items():
            sql = ''' UPDATE log
                      SET Buy_Price = ? ,
                          TP = ? ,
                          SL = ? ,
                          TS = ? ,
                          Valid_ExitCondition2 = ?
                      WHERE Currency = ?'''
            cur = self.db.cursor()
            cur.execute(sql, (v['Buy_Price'], v['TP'], v['SL'], v['TS'], v['Valid_ExitCondition2'], k))
            self.db.commit()

    def InsertToDatabase(self):
        for k, v in self.database_data.items():
            sql = ''' INSERT OR IGNORE INTO log(Currency,Buy_Price,TP,SL,TS,Valid_ExitCondition2)
                      VALUES(?,?,?,?,?,?) '''
            cur = self.db.cursor()
            cur.execute(sql, ( k, v['Buy_Price'], v['TP'], v['SL'], v['TS'], v['Valid_ExitCondition2']))
            self.db.commit()

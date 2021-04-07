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

class Trade:
    def __init__(self, client, firstCurrency, secondCurrency):
        self.client = client
        # self.SetLastSellBuyPrice('BTCUSDT')
        self.first_currency = firstCurrency
        self.second_currency = secondCurrency
        self.currency_pair = firstCurrency + secondCurrency

        self.candle = Candles(client)
        klines = self.candle.getKlines(self.currency_pair, Client.KLINE_INTERVAL_1HOUR, "10 days ago UTC", "")
        # klines = candle.getKlines("BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "1 hour ago UTC", "")
        self.candle.unpackCandle(klines)
        high_series = pd.Series(self.candle.high)
        low_series = pd.Series(self.candle.low)

        self.close_data = self.candle.close
        self.ichi_2_strategy = ICHIMOKU_2_Strategy(high_series, low_series, self.close_data)
        self.win1 = 36
        self.win2 = 48
        self.win3 = 144
        self.ichi_2_strategy.ComputeIchimoku_A(self.win1, self.win2)
        self.ichi_2_strategy.ComputeIchimoku_B(self.win2, self.win3)
        self.ichi_2_strategy.ComputeIchimoku_Base_Line(self.win1, self.win2)
        self.ichi_2_strategy.ComputeIchimoku_Conversion_Line(self.win1, self.win2)

        self.LastTimeOfCandle = self.candle.timeUTC[-1]

        self.InitLogger()

    def InitLogger(self):
        # Create a logging instance
        self.logger = logging.getLogger('my_application')
        self.logger.setLevel(logging.ERROR)  # you can set this to be DEBUG, INFO, ERROR

        # Assign a file-handler to that instance
        fh = logging.FileHandler("log.log")
        fh.setLevel(logging.ERROR)  # again, you can set this differently

        # Format your logs (optional)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)  # This will set the format to the file handler

        # Add the handler to your logging instance
        self.logger.addHandler(fh)

    def SetLastSellBuyPrice(self, currency_pair):
        my_trade = self.client.get_my_trades(symbol=currency_pair)
        setSell = False
        setBuy = False
        for i,item in enumerate(reversed(my_trade)):
            if item['isBuyer'] and not setBuy:
                self.buy_price = item['price']
                setBuy = True
            elif not item['isBuyer'] and not setSell:
                self.sell_price = item['price']
                setSell = True
            elif setBuy and setSell:
                break
            elif i == len(my_trade) and not setSell:
                self.sell_price = 0
            elif i == len(my_trade) and not setBuy:
                self.buy_price = 0

    def GetPrice(self, currency_Pair):
        symbol_info = self.client.get_recent_trades(symbol=currency_Pair)
        return symbol_info[-1]['price']
        # # symbol_info = self.client.get_klines(symbol=currencyPair, interval=time_frame)
        # for i in range(len(symbol_info)):
        #     symbol_info[i]['time']= datetime.utcfromtimestamp(int(symbol_info[i]['time'])/ 1000)
        # pass

    def GetBalance(self, currency):
        return self.client.get_asset_balance(asset=currency)

    def SetLimitBuyOrder(self, currency_Pair, quantity, price):
        order = self.client.order_limit_buy(symbol=currency_Pair, quantity=quantity, price=price)

    def SetLimitSellOrder(self, currency_Pair, quantity, price):
        order = self.client.order_limit_sell(symbol=currency_Pair, quantity=quantity, price=price)

    def SetMarketBuyOrder(self, currency_Pair, quantity):
        return self.client.order_market_buy(symbol=currency_Pair, quantity=quantity)

    def SetMarketSellOrder(self, currency_Pair, quantity):
        return self.client.order_market_sell(symbol=currency_Pair, quantity=quantity)

    def RunTradeThread(self):
        try:
            th = threading.Thread(target=self.RunTrade_1, args=())
            th.start()
            # self.updateCandleTimer = threading.Timer(10, self.UpdateCandle, [self.currency_pair, "1 hour ago UTC"])
            # self.updateCandleTimer.start()
        except:
            print("Error: unable to start thread")

    def BuyOrderCondition(self):
        return self.ichi_2_strategy.BuyStrategy(len(self.ichi_2_strategy.close_data) - 1, 18, 0, 0.04)

    def SellOrderCondition(self):
        return self.ichi_2_strategy.SellStrategy(len(self.ichi_2_strategy.close_data) - 1, 18)

    def UpdateCandle(self, currency_pair, time):
        print(datetime.datetime.now())
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

    def RunTrade_1(self):
        # try:
        if round(float(self.GetBalance(self.first_currency)['free']), 6)-0.000001 > 0:
            isPosition = True
        else:
            isPosition = False
        while True:
            self.UpdateCandle(self.currency_pair, "1 hour ago UTC")
            time.sleep(1)
            try:
                open_order = self.client.get_open_orders(symbol=self.currency_pair)
                if len(open_order) == 0:
                    if not isPosition and self.BuyOrderCondition():
                        self.usdt_balance = self.GetBalance(self.second_currency)
                        self.buy_price = self.GetPrice(self.currency_pair)
                        order = self.SetMarketBuyOrder(self.currency_pair, round(float(self.usdt_balance['free']) / float(self.buy_price), 6)-0.000001)
                        print(order)
                        isPosition = True
                    if isPosition:
                        if self.SellOrderCondition():
                            self.btc_balance = self.GetBalance(self.first_currency)
                            self.sell_price = self.GetPrice(self.currency_pair)
                            order = self.SetMarketSellOrder(self.currency_pair, round(float(self.btc_balance['free']),6)-0.000001)
                            print(order)
                            isPosition = False
                else:
                    if open_order[0]['side'] == "SELL":
                        self.sell_price = open_order[0]['price']
                        isPosition = False
                    if open_order[0]['side'] == "BUY":
                        self.buy_price = open_order[0]['price']
                        isPosition = True
            except ConnectionAbortedError as e:
                WritePrintToFile.Write(e)
            except ConnectionError as e:
                WritePrintToFile.Write(e)
            except ConnectionResetError as e:
                WritePrintToFile.Write(e)
            except BinanceAPIException as e:
                WritePrintToFile.Write(e)
            except BinanceWithdrawException as e:
                WritePrintToFile.Write(e)
            except BinanceRequestException as e:
                WritePrintToFile.Write(e)
            except BinanceOrderException as e:
                WritePrintToFile.Write(e)
            except Timeout as e:
                WritePrintToFile.Write(e)
            except TooManyRedirects as e:
                WritePrintToFile.Write(e)
            except RequestException as e:
                WritePrintToFile.Write(e)
        # except Exception as e:
        #     traceback.print_exc(file=sys.stdout)
        #     # self.logger.exception(e)


    def RunTrade(self):
        if int(float(self.GetBalance('DOGE')['free'])) == 0:
            isPosition = False
        else:
            isPosition = True
        while True:
            try:
                open_order = self.client.get_open_orders(symbol='DOGEBTC')
                if len(open_order) == 0:
                    if not isPosition and (float(self.GetPrice("DOGEBTC")) <= float(self.sell_price) * 0.99 or
                            float(self.GetPrice("DOGEBTC")) >= float(self.sell_price) * 1.03):
                        self.btc_balance = self.GetBalance('BTC')
                        self.buy_price = self.GetPrice("DOGEBTC")
                        self.SetLimitBuyOrder("DOGEBTC", int(float(self.btc_balance['free'])/float(self.buy_price)), self.buy_price)
                        isPosition = True
                    if isPosition:
                        if (float(self.GetPrice("DOGEBTC")) >= float(self.buy_price) * 1.01 or
                                float(self.GetPrice("DOGEBTC")) <= float(self.buy_price) * 0.97):
                            self.doge_balance = self.GetBalance('DOGE')
                            self.sell_price = self.GetPrice("DOGEBTC")
                            self.SetLimitSellOrder("DOGEBTC", int(float(self.doge_balance['free'])), self.sell_price)
                            isPosition = False
                else:
                    if open_order[0]['side'] == "SELL":
                        self.sell_price = open_order[0]['price']
                        isPosition = False
                    if open_order[0]['side'] == "BUY":
                        self.buy_price = open_order[0]['price']
                        isPosition = True
            except BinanceAPIException as e:
                print(e)
            except BinanceWithdrawException as e:
                print(e)
            except BinanceRequestException as e:
                print(e)
            except BinanceOrderException as e:
                print(e)
            except Timeout as e:
                print(e)
            except TooManyRedirects as e:
                print(e)
            except RequestException as e:
                print(e)

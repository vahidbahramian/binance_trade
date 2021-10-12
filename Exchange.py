import abc
import time
from threading import Lock

import numpy
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException, BinanceOrderException
from binance.websockets import BinanceSocketManager
from kucoin.asyncio import KucoinSocketManager
from requests.exceptions import ConnectionError, Timeout, RequestException
import datetime

from IO import FileWorking

import kucoin.client
import asyncio
from events import Events
from kucoin.exceptions import KucoinAPIException

class Exchange(abc.ABC):
    events = Events()
    @abc.abstractmethod
    def CreateCorrespondCurrencyPair(self, currency):
        pass

    @abc.abstractmethod
    def Connect(self):
        pass

    @abc.abstractmethod
    def GetPrice(self, currency_Pair):
        pass

    @abc.abstractmethod
    def GetBalance(self, currency):
        pass

    @abc.abstractmethod
    def GetKlines(self, currency, kline_interval, start_date, end_date):
        pass

    @abc.abstractmethod
    def GetMyTrade(self, currency):
        pass

    @abc.abstractmethod
    def SetLimitOrder(self, currency_pair, side, quantity, price):
        pass

    @abc.abstractmethod
    def SetMarketOrder(self, currency_pair, side, quantity):
        pass

    @abc.abstractmethod
    def CreateWebSocketManager(self):
        pass

    @abc.abstractmethod
    def CreateKlineSocket(self):
        pass

class Binance(Exchange):

    def __init__(self, config):
        self.API_Key = config["API_Key"]
        self.Secret_Key = config["Secret_Key"]
        self.mutex = Lock()
        self.close_websocket = True

    def CreateCorrespondCurrencyPair(self, currency):
        pass

    def Connect(self):
        try:
            self.client = Client(self.API_Key, self.Secret_Key, {"timeout": 500})
        except ConnectionError as e:
            FileWorking.Write(e)
            return False
        except ConnectionResetError as e:
            FileWorking.Write(e)
            return False
        except BinanceAPIException as e:
            FileWorking.Write(e)
            return False
        except BinanceRequestException as e:
            FileWorking.Write(e)
            return False
        except Timeout as e:
            FileWorking.Write(e)
            return False
        except RequestException as e:
            FileWorking.Write(e)
            return False
        else:
            str = "Success Connection" + "   Time: " + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            FileWorking.Write(str)
            print("Success Connection" + "   Time: " + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
            return True

    def GetPrice(self, currency_pair):
        symbol_info = self.client.get_recent_trades(symbol=currency_pair)
        return float(symbol_info[-1]['price'])

    def GetBalance(self, currency):
        return float(self.client.get_asset_balance(asset=currency)['free'])

    def GetKlines(self, currency_pair, kline_interval, start_date, end_date):
        self.mutex.acquire()
        historical_klines = self.client.get_historical_klines(currency_pair, kline_interval, start_date, end_date)
        self.mutex.release()
        self.UnpackCandle(historical_klines)
        return historical_klines

    def UnpackCandle(self, klines):
        _timeUTC = []
        _close = []
        _open = []
        _high = []
        _low = []
        _volume = []
        for i in range(len(klines)):
            _timeUTC.append(datetime.datetime.utcfromtimestamp(int(klines[i][0]) / 1000))
            _close.append(float(klines[i][4]))
            _open.append(float(klines[i][1]))
            _high.append(float(klines[i][2]))
            _low.append(float(klines[i][3]))
            _volume.append(float(klines[i][5]))

        self.timeUTC = _timeUTC
        self.close = numpy.array(_close)
        self.open = numpy.array(_open)
        self.high = numpy.array(_high)
        self.low = numpy.array(_low)
        self.volume = numpy.array(_volume)

    def GetMyTrade(self, currency_pair):
        return self.client.get_my_trades(symbol=currency_pair)

    def SetLimitOrder(self, currency_pair, side, quantity, price):
        if side == "Buy":
            return self.client.order_limit_buy(symbol=currency_pair, quantity=quantity, price=price)
        elif side == "Sell":
            return self.client.order_limit_sell(symbol=currency_pair, quantity=quantity, price=price)

    def SetMarketOrder(self, currency_pair, side, quantity):
        if side == "Buy":
            return self.client.order_market_buy(symbol=currency_pair, quantity=quantity)
        elif side == "Sell":
            return self.client.order_market_sell(symbol=currency_pair, quantity=quantity)

    def CreateWebSocketManager(self):
        self.bsm = BinanceSocketManager(self.client)
        self.conn_key = {}

    def CreateKlineSocket(self, currency_pair, interval):
        self.conn_key[currency_pair] = self.bsm.start_kline_socket(currency_pair, self.UpdateCandle,
                                                  interval=interval)
        if not self.bsm.is_alive():
            self.bsm.start()

    def UpdateCandle(self, msg):
        if msg['e'] == 'error':
            print(msg)
            self.bsm.stop_socket(self.conn_key[msg['s']])
            self.conn_key[msg['s']] = self.bsm.start_kline_socket(self.conn_key[msg['s']], self.UpdateCandle,
                                                        interval=Client.KLINE_INTERVAL_1HOUR)
        else:
            result = {"CurrencyPair": msg['s'], "Time": msg["k"]["t"], "High": msg["k"]["h"], "Low": msg["k"]["l"],
                      "Close": msg["k"]["c"]}
            self.events.on_change(result)

class KuCoin(Exchange):

    KLINE_INTERVAL_CORRESPOND = {"1m": "1min", "3m": "3min", "5m": "5min", "15m": "15min", "30m": "30min",
                                 "1h": "1hour", "2h": "2hour", "4h": "4hour", "6h": "6hour", "8h": "8hour",
                                 "12h": "12hour", "1d": "1day", "1w": "1week"}
    def __init__(self, config):
        self.API_Key = config["API_Key"]
        self.Secret_Key = config["Secret_Key"]
        self.API_Passphrase = config["API_Passpharse"]
        self.Correspond = {}
        self.mutex = Lock()

    def CreateCorrespondCurrencyPair(self, currency):
        for i in currency[:-1]:
            self.Correspond[i + currency[-1]] = i + "-" + currency[-1]
        for i in currency[1:-1]:
            self.Correspond[i + currency[0]] = i + "-" + currency[0]
    def Connect(self):
        try:
            self.client = kucoin.client.Client(self.API_Key, self.Secret_Key, self.API_Passphrase)
        except KucoinAPIException as e:
            FileWorking.Write(e)
            return False
        else:
            str = "Success Connection" + "   Time: " + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            FileWorking.Write(str)
            print("Success Connection" + "   Time: " + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
            return True

    def GetPrice(self, currency_pair):
        return float(self.client.get_ticker(self.Correspond[currency_pair])["price"])

    def GetBalance(self, currency):
        accounts = self.client.get_accounts()
        for item in accounts:
            if item['currency'] == currency and item['type'] == 'trade':
                return float(item['balance'])
        return float(0)

    def GetKlines(self, currency_pair, kline_interval, start_date, end_date):
        # self.mutex.acquire()
        klines = self.client.get_kline_data(self.Correspond[currency_pair],
                                            self.KLINE_INTERVAL_CORRESPOND[kline_interval], start_date, end_date)
        # self.mutex.release()
        self.UnpackCandle(klines)
        time.sleep(1)

    def UnpackCandle(self, klines):
        _timeUTC = []
        _close = []
        _open = []
        _high = []
        _low = []
        _volume = []
        for i in range(len(klines)):
            _timeUTC.append(datetime.datetime.utcfromtimestamp(int(klines[i][0])))
            _open.append(float(klines[i][1]))
            _close.append(float(klines[i][2]))
            _high.append(float(klines[i][3]))
            _low.append(float(klines[i][4]))
            _volume.append(float(klines[i][6]))

        _timeUTC.reverse()
        _close.reverse()
        _open.reverse()
        _high.reverse()
        _low.reverse()
        _volume.reverse()

        self.timeUTC = _timeUTC
        self.close = numpy.array(_close)
        self.open = numpy.array(_open)
        self.high = numpy.array(_high)
        self.low = numpy.array(_low)
        self.volume = numpy.array(_volume)

    def GetMyTrade(self, currency_pair):
        return self.client.get_trade_histories(symbol=self.Correspond[currency_pair])

    def SetLimitOrder(self, currency_pair, side, quantity, price):
        if side == "Buy":
            return self.client.create_limit_order(symbol=self.Correspond[currency_pair], side=Client.SIDE_BUY,
                                           price=str(price), size=str(quantity))
        elif side == "Sell":
            return self.client.create_limit_order(symbol=self.Correspond[currency_pair], side=Client.SIDE_SELL,
                                           price=str(price), size=str(quantity))

    def SetMarketOrder(self, currency_pair, side, quantity):
        if side == "Buy":
            return self.client.create_market_order(symbol=self.Correspond[currency_pair], side=Client.SIDE_BUY,
                                            size=str(quantity))
        elif side == "Sell":
            return self.client.create_market_order(symbol=self.Correspond[currency_pair], side=Client.SIDE_SELL,
                                            size=str(quantity))

    def CreateWebSocketManager(self):
        self.close_websocket = True
        self.close_klinesocket = {}
        self.loop_klinesocket = {}
        self.loop_web_socket = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop_web_socket)
        self.loop_web_socket = asyncio.get_event_loop()
        try:
            self.loop_web_socket.run_until_complete(self.CreateWebSocket())
        except asyncio.CancelledError as e:
            pass
        self.loop_web_socket.stop()
        for task in asyncio.Task.all_tasks():
            task.cancel()

    async def CreateWebSocket(self):
        # self.ksm = await KucoinSocketManager.create(self.loop_web_socket, self.client, self.HandleEvent)
        # while self.close_websocket:
        #     await asyncio.sleep(20, loop=self.loop_web_socket)


        while self.close_websocket:
            for key, value in self.Correspond.items():
                try:
                    self.GetKlines(key, '1h', int(datetime.datetime.now().timestamp()) - 3600,
                                                   int(datetime.datetime.now().timestamp()))
                    if len(self.timeUTC) > 0:
                        await self.HandleEvent(key)
                    await asyncio.sleep(0.5)
                except KucoinAPIException as e:
                    print(e)

    def CreateKlineSocket(self, currency_pair, interval):

        self.loop_klinesocket[currency_pair] = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop_klinesocket[currency_pair])
        self.loop_klinesocket[currency_pair] = asyncio.get_event_loop()
        self.loop_klinesocket[currency_pair].run_until_complete(self.KlineSubscribe(currency_pair, interval))

        # self.UnSubscribeKlineSocket(currency_pair, interval)
        # asyncio.sleep(1, loop=self.loop_klinesocket[currency_pair])

        self.loop_klinesocket[currency_pair].stop()
        for task in asyncio.Task.all_tasks():
            task.cancel()

    def UnSubscribeKlineSocket(self, currency_pair, interval):
        self.loop_klinesocket[currency_pair] = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop_klinesocket[currency_pair])
        self.loop_klinesocket[currency_pair] = asyncio.get_event_loop()
        self.loop_klinesocket[currency_pair].run_until_complete(self.KlineUnSubscribe(currency_pair, interval))

    def StopAllKlineSocket(self):
        self.close_klinesocket = dict.fromkeys(self.close_klinesocket, False)

    async def KlineSubscribe(self, currency_pair, interval):
        await self.ksm.subscribe('/market/candles:' + str(self.Correspond[currency_pair]) + "_" +
                                 self.KLINE_INTERVAL_CORRESPOND[interval])
        self.close_klinesocket[currency_pair] = True
        while self.close_klinesocket[currency_pair]:
            await asyncio.sleep(20, loop=self.loop_klinesocket[currency_pair])

    async def KlineUnSubscribe(self, currency_pair, interval):
        await self.ksm.unsubscribe('/market/candles:' + str(self.Correspond[currency_pair]) + "_" +
                                 self.KLINE_INTERVAL_CORRESPOND[interval])


    async def HandleEvent(self, msg):
        # if msg['subject'] == 'trade.candles.update':
        #     currency_pair = [k for k, v in self.Correspond.items() if v == msg['data']['symbol']][0]
        #     # time_1 = datetime.datetime.utcfromtimestamp(int(msg['data']['candles'][0]))
        #     time_1 = int(msg['data']['candles'][0]) * 1000
        #     high = float(msg['data']['candles'][3])
        #     low = float(msg['data']['candles'][4])
        #     close = float(msg['data']['candles'][2])
        #     result = {"CurrencyPair": currency_pair, "Time": time_1, "High": high, "Low": low, "Close": close}
        #     self.events.on_change(result)
        currency_pair = msg
        time = self.timeUTC[-1]
        high = self.high[-1]
        low = self.low[-1]
        close = self.close[-1]
        result = {"CurrencyPair": currency_pair, "Time": time, "High": high, "Low": low, "Close": close}
        self.events.on_change(result)
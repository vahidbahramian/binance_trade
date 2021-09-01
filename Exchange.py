import abc
import time
from threading import Lock

import numpy
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceWithdrawException, BinanceRequestException, \
    BinanceOrderException
from binance.websockets import BinanceSocketManager
from kucoin.asyncio import KucoinSocketManager
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects, RequestException
import datetime

from Candles import Candles
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
        self.close_websocket = True

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
        self.mutex.acquire()
        klines = self.client.get_kline_data(self.Correspond[currency_pair],
                                            self.KLINE_INTERVAL_CORRESPOND[kline_interval],
                                            int(datetime.datetime.now().timestamp()) - 864000,
                                            int(datetime.datetime.now().timestamp()))
        self.mutex.release()
        self.UnpackCandle(klines)

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
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.CreateWebSocket())

    async def CreateWebSocket(self):
        # global loop
        self.ksm = await KucoinSocketManager.create(self.loop, self.client, self.HandleEvent)
        # await self.ksm.subscribe('/market/candles:' + str(self.Correspond['BTCUSDT']) + "_" +
        #                          self.KLINE_INTERVAL_CORRESPOND['1m'])
        while self.close_websocket:
            # print("sleeping to keep loop open")
            await asyncio.sleep(20, loop=self.loop)
        self.ksm._conn.cancel()
        # await self.ksm.subscribe('/market/ticker:ETH-USDT')
        # for private topics such as '/account/balance' pass private=True
        # self.ksm_private = await KucoinSocketManager.create(self.loop, self.client, self.HandleEvent, private=True)

    def CreateKlineSocket(self, currency_pair, interval, re_create):
        if re_create:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.KlineUnSubscribe(currency_pair, interval))

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.KlineSubscribe(currency_pair, interval))
        # await self.ksm.subscribe('/market/candles:BTC-USDT' + "_" + self.KLINE_INTERVAL_CORRESPOND[interval])

    def ReCreateKlineSocket(self):
        pass

    async def KlineSubscribe(self, currency_pair, interval):
        # pass
        await self.ksm.subscribe('/market/candles:' + str(self.Correspond[currency_pair]) + "_" +
                                 self.KLINE_INTERVAL_CORRESPOND[interval])

    async def KlineUnSubscribe(self, currency_pair, interval):
        # pass
        await self.ksm.unsubscribe('/market/candles:' + str(self.Correspond[currency_pair]) + "_" +
                                 self.KLINE_INTERVAL_CORRESPOND[interval])

    async def HandleEvent(self, msg):
        if msg['subject'] == 'trade.candles.update':
            currency_pair = [k for k, v in self.Correspond.items() if v == msg['data']['symbol']][0]
            # time_1 = datetime.datetime.utcfromtimestamp(int(msg['data']['candles'][0]))
            time_1 = int(msg['data']['candles'][0]) * 1000
            high = float(msg['data']['candles'][3])
            low = float(msg['data']['candles'][4])
            close = float(msg['data']['candles'][2])
            result = {"CurrencyPair": currency_pair, "Time": time_1, "High": high, "Low": low, "Close": close}
            self.events.on_change(result)
        # else:
        #     print(msg)
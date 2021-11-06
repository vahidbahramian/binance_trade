import abc
from binance.client import Client
import logging
import sys
from datetime import datetime
from IO import FileWorking

FLoatingPointCurrencyPair = {"BTCUSDT": 6, "ETHUSDT": 5, "ETHBTC": 3, "BNBUSDT": 4, "BNBBTC": 2, "LTCUSDT": 5,
                             "LTCBTC": 2, "XRPUSDT": 2, "XRPBTC": 1, "TRXUSDT": 1, "TRXBTC": 0, "ADAUSDT": 2,
                             "ADABTC": 1, "DOGEUSDT": 1, "DOGEBTC": 0, "ALGOUSDT": 2, "ALGOBTC": 1, "FTMUSDT": 2,
                             "FTMBTC": 1, "DOTUSDT": 3, "DOTBTC": 1, "XTZUSDT": 2, "XTZBTC": 1, "MATICUSDT": 2,
                             "MATICBTC": 1}
class OfflineAlgorithm(abc.ABC):
    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    def RunAlgorithm(self):
        pass

    # @abc.abstractmethod
    # def BuyStrategy(self):
    #     pass

    # @abc.abstractmethod
    # def CheckProfitOrLoss(self):
    #     pass

    @abc.abstractmethod
    def WriteResult(self):
        pass

class OnlineAlgorithm(abc.ABC):
    def __init__(self, exchange):
        self.exchange = exchange
        self.InitLogger()
        self.exchange.events.on_change += self.UpdateCandle

    def CreateCurrencyPair(self, currency):
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

        self.exchange.CreateCorrespondCurrencyPair(currency)

    def CreateWebSocketManager(self):
        self.exchange.CreateWebSocketManager()

    def CreateKlineSocket(self, currency_pair, interval):
        self.exchange.CreateKlineSocket(currency_pair, interval)

    def StopAllKlineSocket(self):
        self.exchange.StopAllKlineSocket()

    def GetPrice(self, currency_Pair):
        return self.exchange.GetPrice(currency_Pair)

    def GetBalance(self, currency):
        return self.exchange.GetBalance(currency)

    def GetKlines(self, currency, kline_interval, start_date, end_date):
        return self.exchange.GetKlines(currency, kline_interval, start_date, end_date)

    def GetMyTrade(self, currency_pair):
        return self.exchange.GetMyTrade(currency_pair)

    def SetQuntity(self, quntity, currency):
        a = pow(10, -1 * (FLoatingPointCurrencyPair[currency] + 1)) * 5
        return round(quntity - a, FLoatingPointCurrencyPair[currency])

    def SetLimitBuyOrder(self, currency_pair, quantity, price):
        return self.exchange.SetLimitOrder(currency_pair, "Buy", quantity, price)

    def SetLimitSellOrder(self, currency_pair, quantity, price):
        return self.exchange.SetLimitOrder(currency_pair, "Sell", quantity, price)

    def SetMarketBuyOrder(self, currency_Pair, quantity):
        return self.exchange.SetMarketOrder(currency_Pair, "Buy", quantity)

    def SetMarketSellOrder(self, currency_Pair, quantity):
        return self.exchange.SetMarketOrder(currency_Pair, "Sell", quantity)

    @abc.abstractmethod
    def BuyOrderCondition(self):
        pass

    @abc.abstractmethod
    def SellOrderCondition(self):
        pass

    @abc.abstractmethod
    def UpdateCandle(self, msg):
        pass

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

    def LogException(self, e):
        exception_type, exception_object, exception_traceback = sys.exc_info()
        FileWorking.Write(datetime.now())
        FileWorking.Write("Line number: " + str(exception_traceback.tb_lineno))
        FileWorking.Write(e)

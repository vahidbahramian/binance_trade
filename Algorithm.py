import abc
from binance.client import Client
import logging
import sys
from datetime import datetime
from IO import FileWorking

FLoatingPointCurrencyPair = {"BTCUSDT": 6, "ETHUSDT": 5, "ETHBTC": 3, "BNBUSDT": 4, "BNBBTC": 2}
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
    def __init__(self, client, bsm, candle):
        self.client = client
        self.candle = candle
        self.bsm = bsm
        self.InitLogger()

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

    def GetPrice(self, currency_Pair):
        symbol_info = self.client.get_recent_trades(symbol=currency_Pair)
        return float(symbol_info[-1]['price'])

    def GetBalance(self, currency):
        return float(self.client.get_asset_balance(asset=currency)['free'])

    def SetQuntity(self, quntity, currency):
        a = pow(10, -1 * (FLoatingPointCurrencyPair[currency] + 1)) * 5
        return round(quntity - a, FLoatingPointCurrencyPair[currency])

    def SetLimitBuyOrder(self, currency_Pair, quantity, price):
        return self.client.order_limit_buy(symbol=currency_Pair, quantity=quantity, price=price)

    def SetLimitSellOrder(self, currency_Pair, quantity, price):
        return self.client.order_limit_sell(symbol=currency_Pair, quantity=quantity, price=price)

    def SetMarketBuyOrder(self, currency_Pair, quantity):
        return self.client.order_market_buy(symbol=currency_Pair, quantity=quantity)

    def SetMarketSellOrder(self, currency_Pair, quantity):
        return self.client.order_market_sell(symbol=currency_Pair, quantity=quantity)

    @abc.abstractmethod
    def BuyOrderCondition(self):
        pass

    @abc.abstractmethod
    def SellOrderCondition(self):
        pass

    @abc.abstractmethod
    def UpdateCandle(self, currency_pair, time):
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

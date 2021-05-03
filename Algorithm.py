import abc
from binance.client import Client
import logging

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

    def GetPrice(self, currency_Pair):
        symbol_info = self.client.get_recent_trades(symbol=currency_Pair)
        return symbol_info[-1]['price']

    def GetBalance(self, currency):
        return self.client.get_asset_balance(asset=currency)

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

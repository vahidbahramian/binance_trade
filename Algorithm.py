import abc
from binance.client import Client

class OfflineAlgorithm(abc.ABC):
    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    def RunAlgorithm(self):
        pass

    @abc.abstractmethod
    def BuyStrategy(self):
        pass

    # @abc.abstractmethod
    # def CheckProfitOrLoss(self):
    #     pass

    @abc.abstractmethod
    def WriteResult(self):
        pass

class OnlineAlgorithm(abc.ABC):
    def __init__(self, client, bsm, candle, firstCurrency, secondCurrency):
        self.client = client
        self.candle = candle
        self.bsm = bsm
        self.first_currency = firstCurrency
        self.second_currency = secondCurrency
        self.currency_pair = firstCurrency + secondCurrency
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

from datetime import datetime
import threading

from binance.exceptions import BinanceAPIException, BinanceWithdrawException, BinanceRequestException,\
    BinanceOrderException


class Trade:
    def __init__(self, client):
        self.client = client
        self.SetLastSellBuyPrice('DOGEBTC')

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

    def RunTradeThread(self):
        try:
            th = threading.Thread(target=self.RunTrade, args=())
            th.start()
        except:
            print("Error: unable to start thread")

    def RunTrade(self):
        isPosition = False
        b = self.GetBalance('DOGE')

        while True:
            try:
                open_order = self.client.get_open_orders(symbol='DOGEBTC')
                if len(open_order) == 0:
                    if not isPosition and (float(self.GetPrice("DOGEBTC")) <= float(self.sell_price) * 0.97 or
                            float(self.GetPrice("DOGEBTC")) >= float(self.sell_price) * 1.02):
                        self.btc_balance = self.GetBalance('BTC')
                        self.buy_price = self.GetPrice("DOGEBTC")
                        self.SetLimitBuyOrder("DOGEBTC", int(float(self.btc_balance['free'])/float(self.buy_price)), self.buy_price)
                        isPosition = True
                    if isPosition:
                        if (float(self.GetPrice("DOGEBTC")) >= float(self.buy_price) * 1.03 or
                                float(self.GetPrice("DOGEBTC")) <= float(self.buy_price) * 0.95):
                            self.doge_balance = self.GetBalance('DOGE')
                            self.sell_price = self.GetPrice("DOGEBTC")
                            self.SetLimitSellOrder("DOGEBTC", int(float(self.doge_balance['free'])), self.sell_price)
                            isPosition = False
            except BinanceAPIException as e:
                print(e)
            except BinanceWithdrawException as e:
                print(e)
            except BinanceRequestException as e:
                print(e)
            except BinanceOrderException as e:
                print(e)
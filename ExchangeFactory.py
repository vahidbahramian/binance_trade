from Connect import Connect
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceWithdrawException, BinanceRequestException, \
    BinanceOrderException
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects, RequestException
import datetime
from IO import FileWorking

import kucoin.client

class ExchangeFactory:

    @staticmethod
    def Create(exchange, config):
        if exchange == "Binance":
            return Binance(config)
        elif exchange == "KuCoin":
            return KuCoin(config)


class Binance(Connect):
        def __init__(self, config):
            self.API_Key = config["API_Key"]
            self.Secret_Key = config["Secret_Key"]
        def ConnectTo(self):
            try:
                client = Client(self.API_Key, self.Secret_Key, {"timeout": 500})
            except ConnectionError as e:
                FileWorking.Write(e)
            except ConnectionResetError as e:
                FileWorking.Write(e)
            except BinanceAPIException as e:
                FileWorking.Write(e)
            except BinanceRequestException as e:
                FileWorking.Write(e)
            except Timeout as e:
                FileWorking.Write(e)
            except RequestException as e:
                FileWorking.Write(e)
            else:
                str = "Success Connection" + "   Time: " + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
                FileWorking.Write(str)
                print("Success Connection" + "   Time: " + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
                return client

class KuCoin(Connect):
    def __init__(self, config):
        self.API_Key = config["API_Key"]
        self.Secret_Key = config["Secret_Key"]
        self.API_Passphrase = config["API_Passpharse"]
    def ConnectTo(self):
        client = kucoin.client.Client(self.API_Key, self.Secret_Key, self.API_Passphrase)
        return client
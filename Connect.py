from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceWithdrawException, BinanceRequestException, \
    BinanceOrderException
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects, RequestException
import datetime
from IO import WritePrintToFile

api_key = "NfjCKix0SSnVigM7dPhluUKxpFZnmd3s5bUVdfZMer4KlSZGpnMdw2815Oa5BiMR"
api_secret = "ChEyzzYY7EMtbrmKvZ3Jltfip1loihGoaT2UtGEeLHHI5bMfSNqDHPQuPq7I7Ezi"


class Connect:
    @property
    def ConnectTo(self):
        try:
            global client
            client = Client(api_key, api_secret, {"timeout": 500})
        except ConnectionError as e:
            WritePrintToFile.Write(e)
        except ConnectionResetError as e:
            WritePrintToFile.Write(e)
        except BinanceAPIException as e:
            WritePrintToFile.Write(e)
        except BinanceRequestException as e:
            WritePrintToFile.Write(e)
        except Timeout as e:
            WritePrintToFile.Write(e)
        except RequestException as e:
            WritePrintToFile.Write(e)
        else:
            str = "Success Connection" + "   Time: " + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            WritePrintToFile.Write(str)
            print("Success Connection" + "   Time: " + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
            return client

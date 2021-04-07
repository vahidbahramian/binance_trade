from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceWithdrawException
import datetime
from IO import WritePrintToFile

api_key = "NfjCKix0SSnVigM7dPhluUKxpFZnmd3s5bUVdfZMer4KlSZGpnMdw2815Oa5BiMR"
api_secret = "ChEyzzYY7EMtbrmKvZ3Jltfip1loihGoaT2UtGEeLHHI5bMfSNqDHPQuPq7I7Ezi"


class Connect:

    @property
    def ConnectTo(self):
        try:
            client = Client(api_key, api_secret, {"timeout": 500})
        except BinanceAPIException as e:
            print(e)
        except BinanceWithdrawException as e:
            print(e)
        else:
            str = "Success Connection" + "   Time: " + datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            WritePrintToFile.Write(str)
            return client

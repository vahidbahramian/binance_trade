from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceWithdrawException

api_key = "NfjCKix0SSnVigM7dPhluUKxpFZnmd3s5bUVdfZMer4KlSZGpnMdw2815Oa5BiMR"
api_secret = "ChEyzzYY7EMtbrmKvZ3Jltfip1loihGoaT2UtGEeLHHI5bMfSNqDHPQuPq7I7Ezi"


class Connect:

    @property
    def ConnectTo(self):
        try:
            client = Client(api_key, api_secret)
        except BinanceAPIException as e:
            print(e)
        except BinanceWithdrawException as e:
            print(e)
        else:
            print("Success Connection")
            return client

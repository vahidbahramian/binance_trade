import requests
from events import Events


class API():
    def __init__(self):
        # self.events = Events()
        # self.events.on_change()
        self.api_url = "http://192.168.1.140:8080"
    def GetAllUsers(self):
        response = requests.get(self.api_url+"/api/all_user")
        result = response.json()
        return result

    def PostOrder(self, order_side, currency_pair, buy_ratio):
        data = {"Side": order_side, "Currency": currency_pair, "Ratio": buy_ratio}
        requests.post(self.api_url+"/api/order", json=data)

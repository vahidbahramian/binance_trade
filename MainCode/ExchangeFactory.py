from MainCode.Exchange import Binance, KuCoin

class ExchangeFactory:

    @staticmethod
    def Create(exchange, config, user_id):
        if exchange == "Binance":
            return Binance(config, user_id)
        elif exchange == "KuCoin":
            return KuCoin(config, user_id)
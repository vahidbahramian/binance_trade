from Exchange import Binance, KuCoin

class ExchangeFactory:

    @staticmethod
    def Create(exchange, config):
        if exchange == "Binance":
            return Binance(config)
        elif exchange == "KuCoin":
            return KuCoin(config)
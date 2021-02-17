import talib


class Indicator:

    @staticmethod
    def EMA(self, data, tp=9):
        return talib.EMA(data, timeperiod=tp)

    @staticmethod
    def RSI(self, data):
        return talib.RSI(data)

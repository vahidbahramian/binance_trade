import talib


class Indicator:

    @staticmethod
    def EMA(data, time_period=9):
        return talib.EMA(data, timeperiod=time_period)

    @staticmethod
    def RSI(data):
        return talib.RSI(data)

    @staticmethod
    def MACD(data, fast_period=12, slow_period=26, signal_period=9):
        """

        :rtype: macd, macdsignal, macdhist
        """
        return talib.MACD(data, fastperiod=fast_period, slowperiod=slow_period, signalperiod=signal_period)

    @staticmethod
    def MFI(high_data, low_data, close_data, volume_data):
        return talib.MFI(high_data, low_data, close_data, volume_data)

    @staticmethod
    def STOCASTIC(high_data, low_data, close_data, fastk, fastd):
        return talib.STOCHF(high_data, low_data, close_data, fastk_period=fastk, fastd_period=fastd,
                                    fastd_matype=0)

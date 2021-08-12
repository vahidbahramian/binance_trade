import talib
from ta import trend, momentum
from talipp.indicators import HMA

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
    def STOCASTICFast(high_data, low_data, close_data, fastk, fastd):
        return talib.STOCHF(high_data, low_data, close_data, fastk_period=fastk, fastd_period=fastd,
                                    fastd_matype=0)

    @staticmethod
    def STOCASTIC(high_data, low_data, close_data, fastk, slowk, slowd):
        return talib.STOCH(high_data, low_data, close_data, fastk_period=fastk, slowk_period=slowk,
                                    slowd_period=slowd)

    @staticmethod
    def ICHIMOKU_A(high_data, low_data, win1, win2):
        return trend.ichimoku_a(high_data, low_data, win1, win2, False, True)

    @staticmethod
    def ICHIMOKU_B(high_data, low_data, win2, win3):
        return trend.ichimoku_b(high_data, low_data, win2, win3, False, True)

    @staticmethod
    def ICHIMOKU_Base_Line(high_data, low_data, win1, win2):
        return trend.ichimoku_base_line(high_data, low_data, win1, win2)

    @staticmethod
    def ICHIMOKU_Conversion_Line(high_data, low_data, win1, win2):
        return trend.ichimoku_conversion_line(high_data, low_data, win1, win2)

    @staticmethod
    def WilliamsR(high_data, low_data, close_data, timeperiod = 14):
        return momentum.williams_r(high_data, low_data, close_data, timeperiod)

    @staticmethod
    def CCI(high_data, low_data, close_data):
        return trend.cci(high_data, low_data, close_data)

    @staticmethod
    def HMA(close_data, period):
        return HMA(period, close_data)

from Indicator import Indicator
import abc
class IStrategy(abc.ABC):
    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    def RunStrategy(self):
        pass


class EMA_Strategy(IStrategy):

    def __init__(self, close_data):
        self.data = close_data

    def ComputeEMAArray_1(self, time_period):
        self.ema_arr_1 = Indicator.EMA(self.data, timeperiod=time_period)

    def ComputeEMAArray_2(self, time_period):
        self.ema_arr_2 = Indicator.EMA(self.data, timeperiod=time_period)

    def RunStrategy(self, i):
        if self.ema_arr_1[i - 1] < self.ema_arr_2[i - 1]:
            if self.ema_arr_1[i] > self.ema_arr_2[i]:
                return True

        return False

class EMA_Stocastic_Strategy(IStrategy):

    def __init__(self, close, high, low):
        self.close_data = close
        self.high_data = high
        self.low_data = low

    def ComputeEMAArray_1(self, time_period):
        self.ema_arr_1 = Indicator.EMA(self.close_data, time_period=time_period)

    def ComputeEMAArray_2(self, time_period):
        self.ema_arr_2 = Indicator.EMA(self.close_data, time_period=time_period)

    def ComputeStocasticArray(self, fastk, fastd):
        self.slowk, self.slowd = Indicator.STOCASTIC(self.high_data, self.low_data, self.close_data, fastk, fastd)

    def RunStrategy(self, i):
        if self.slowk[i - 1] < self.slowd[i - 1]:
            if self.slowk[i] > self.slowd[i]:
                if self.ema_arr_1[i] > self.ema_arr_2[i]:
                    return True
        return False

class ICHIMOKU_2_Strategy(IStrategy):

    def __init__(self, high, low, close):
        self.high_data = high
        self.low_data = low
        self.close_data = close

    def ComputeIchimoku_A(self, win1, win2):
        self.ich_a = Indicator.ICHIMOKU_A(self.high_data, self.low_data, win1, win2)

    def ComputeIchimoku_B(self, win2, win3):
        self.ich_b = Indicator.ICHIMOKU_B(self.high_data, self.low_data, win2, win3)

    def ComputeIchimoku_Base_Line(self, win1, win2):
        self.ich_base_line = Indicator.ICHIMOKU_Base_Line(self.high_data, self.low_data, win1, win2)

    def ComputeIchimoku_Conversion_Line(self, win1, win2):
        self.ich_conversion_line = Indicator.ICHIMOKU_Conversion_Line(self.high_data, self.low_data, win1, win2)

    def RunStrategy(self, i, t, a, b):
        if i - t - 1 > 0:
            if (self.close_data[i] > self.ich_conversion_line[i] and self.close_data[i] > self.ich_base_line[i] and
                    self.ich_a[i - t - 1] < self.close_data[i] and
                    self.close_data[i] > self.ich_b[i - t - 1] > self.ich_a[i - t - 1] and
                    self.ich_a[i] > self.ich_b[i] and self.ich_conversion_line[i] > self.ich_base_line[i] > self.ich_a[i - t - 1]):
                if i - t > 0:
                    if a < (self.close_data[i] - self.close_data[i - t]) / self.close_data[i] < b:
                        return True
        return False

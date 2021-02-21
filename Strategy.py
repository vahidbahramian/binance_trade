from Indicator import Indicator


class EMA_Strategy:

    def __init__(self, close_data):
        self.data = close_data

    def ComputeEMAArray_1(self, time_period):
        self.ema_arr_1 = Indicator.EMA(self.data, timeperiod=time_period)

    def ComputeEMAArray_2(self, time_period):
        self.ema_arr_2 = Indicator.EMA(self.data, timeperiod=time_period)

    def Check(self, i):
        if self.ema_arr_1[i - 1] < self.ema_arr_2[i - 1]:
            if self.ema_arr_1[i] > self.ema_arr_2[i]:
                return True
        else:
            return False

class EMA_Stocastic_Strategy:

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

    def Check(self, i):
        if self.slowk[i - 1] < self.slowd[i - 1]:
            if self.slowk[i] > self.slowd[i]:
                if self.ema_arr_1[i] > self.ema_arr_2[i]:
                    return True
        else:
            return False

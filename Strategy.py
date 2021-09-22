import ast
import configparser
import json
import sys

import pandas as pd

from Indicator import Indicator
import abc
import numpy as np
from math import sqrt, ceil

class IStrategy(abc.ABC):
    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    def BuyStrategy(self):
        pass

    @abc.abstractmethod
    def SellStrategy(self):
        pass

    def ReadConfigFile(self, currency_pair):
        config = configparser.ConfigParser()
        config.read('Config.ini')
        section = str(sys.argv[1])
        return ast.literal_eval(config[section]["Strategy"])[currency_pair]


    def WriteConfigFile(self, currency_pair, param, value):
        config = configparser.ConfigParser()
        config.read('Config.ini')
        section = str(sys.argv[1])
        strategy_param = ast.literal_eval(config[section]["Strategy"])
        strategy_param[currency_pair][param] = value
        config.set(section, "Strategy", str(strategy_param))
        with open('Config.ini', 'w') as configfile:
            config.write(configfile)

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

    def ComputeMACD(self, fast, slow, signal):
        self.macd, self.macd_signal, self.macd_hist = Indicator.MACD(self.close_data, fast_period=fast, slow_period=slow,
                                                                     signal_period=signal)

    def ComputeCCI(self):
        self.cci = Indicator.CCI(self.high_data, self.low_data, self.close_data)

    def ComputeWilliamsR(self, r_period):
        self.WilliamsR_high = Indicator.WilliamsR(self.high_data, self.low_data, self.high_data, r_period)
        self.WilliamsR_low = Indicator.WilliamsR(self.high_data, self.low_data, self.low_data, r_period)

    def ComputeSTOCASTIC(self, fastk, slowk, slowd):
        self.stocastic_k, self.stocastic_d = Indicator.STOCASTIC(self.high_data, self.low_data, self.close_data, fastk,
                                                                 slowk, slowd)

    def ComputeEMA(self, time_period):
        self.ema = Indicator.EMA(self.close_data, time_period=time_period)

    def ComputeHMA(self, period):
        self.hma = Indicator.HMA(self.close_data, period=period)
        self.hma = np.pad(self.hma.output_values, int(period + int(sqrt(period)-1) + ceil(sqrt(period))-1)-1, 'constant')

    def ComputeTEMA(self, period):
        self.tema = Indicator.TEMA(self.close_data, period=period)

    def ComputeDEMA(self, period):
        self.dema = Indicator.DEMA(self.close_data, period=period)

    def ComputeKeltnerChannel(self, window, window_atr, multi_atr):
        self.keltner = Indicator.KeltnerChannel(self.high_data, self.low_data, pd.Series(self.close_data), window,
                                                window_atr, multi_atr)

    def ComputeMcGinleyDynamic(self, period):
        self.mc_ginley = Indicator.McGinleyDynamic(self.close_data, period=period)
        self.mc_ginley = np.pad(self.mc_ginley.output_values, int(period)-1, 'constant')

    def BuyStrategy(self, i, t, a, b):
        if i - t + 1 > 0:
            if (self.close_data[i] >= self.ich_base_line[i] and self.ich_a[i] >= self.ich_b[i] and
                    self.close_data[i] >= self.ich_b[i - t + 1] and self.close_data[i] >= self.ich_a[i - t + 1] and
                    self.ich_conversion_line[i] >= self.ich_base_line[i] >= self.ich_a[i - t + 1]):
                # if i - t + 1 > 0:
                #     if a <= (self.close_data[i] - self.close_data[i - t + 1]) / self.close_data[i] <= b:
                if a >= (self.close_data[i] - self.ich_a[i - t + 1]) / self.close_data[i] and\
                        a >= (self.close_data[i] - self.ich_b[i - t + 1]) / self.close_data[i]:
                    return True
        return False
    def SellStrategy(self, i, t):
        if i - t + 1 > 0:
            if ((self.close_data[i] < self.ich_b[i - t + 1] and
                    self.close_data[i] < self.ich_a[i - t + 1])):
                return True
        return False

class ICHIMOKU_CCI_WilliamsR_Strategy(ICHIMOKU_2_Strategy):

    def __init__(self, high, low, close):
        super().__init__(high, low, close)
        self.buy_ichi = False
        self.buy_cci = False
        self.buy_WilliamsR = False

    def BuyStrategy(self, i, t, a, b, r_down, cci_down):
        if i - t + 1 > 0:
            if (self.close_data[i] >= self.ich_base_line[i] and self.ich_a[i] >= self.ich_b[i] and
                    self.close_data[i] >= self.ich_b[i - t + 1] and self.close_data[i] >= self.ich_a[i - t + 1] and
                    self.ich_conversion_line[i] >= self.ich_base_line[i] >= self.ich_a[i - t + 1]):
                # if i - t + 1 > 0:
                #     if a <= (self.close_data[i] - self.close_data[i - t + 1]) / self.close_data[i] <= b:
                if a >= (self.close_data[i] - self.ich_a[i - t + 1]) / self.close_data[i] and\
                        a >= (self.close_data[i] - self.ich_b[i - t + 1]) / self.close_data[i]:
                    self.buy_ichi = True
                    return True
        if not self.buy_ichi:
            if (self.WilliamsR[i - 1] < r_down and self.WilliamsR[i] > r_down) or self.buy_WilliamsR:
                self.buy_WilliamsR = True
            if ((self.WilliamsR[i - 1] > r_down and self.WilliamsR[i] < r_down)):
                self.buy_WilliamsR = False
            if (self.cci[i - 1] < cci_down and self.cci[i] > cci_down) or self.buy_cci:
                self.buy_cci = True
            if (self.cci[i - 1] > cci_down and self.cci[i] < cci_down):
                self.buy_cci = False
            if self.buy_WilliamsR and self.buy_cci:
                return True
        return False

    def SellStrategy(self, i, t, r_down, r_up, cci_down, cci_up):
        if i - t + 1 > 0 and self.buy_ichi:
            if ((self.close_data[i] < self.ich_b[i - t + 1] and
                    self.close_data[i] < self.ich_a[i - t + 1])):
                self.buy_ichi = False
                return True
        if not self.buy_ichi:
            if ((self.WilliamsR[i - 1] > r_down and self.WilliamsR[i] < r_down)) or \
                    ((self.WilliamsR[i - 1] > r_up and self.WilliamsR[i] < r_up)):
                self.buy_WilliamsR = False
            if (self.cci[i - 1] > cci_down and self.cci[i] < cci_down) or\
                    (self.cci[i - 1] > cci_up and self.cci[i] < cci_up):
                self.buy_cci = False
            if not self.buy_WilliamsR or not self.buy_cci:
                return True
        return False

class ICHIMOKU_STOCASTIC_Strategy(ICHIMOKU_2_Strategy):

    def __init__(self, high, low, close):
        super().__init__(high, low, close)
        self.buy_ichi = False

    def BuyStrategy(self, i, t, a, b, r, r_period):
        if i - t + 1 > 0:
            if (self.close_data[i] >= self.ich_base_line[i] and self.ich_a[i] >= self.ich_b[i] and
                    self.close_data[i] >= self.ich_b[i - t + 1] and self.close_data[i] >= self.ich_a[i - t + 1] and
                    self.ich_conversion_line[i] >= self.ich_base_line[i] >= self.ich_a[i - t + 1]):
                if a >= (self.close_data[i] - self.ich_a[i - t + 1]) / self.close_data[i] and\
                        a >= (self.close_data[i] - self.ich_b[i - t + 1]) / self.close_data[i]:
                    self.buy_ichi = True
                    return True
        # if not self.buy_ichi:
        #     if (self.stocastic_k[i - 1] < self.stocastic_d[i - 1]) and (self.stocastic_k[i] > self.stocastic_d[i]) and\
        #             (self.WilliamsR_low[i] < r):
        #         return True
        # if not self.buy_ichi:
        #     if (self.macd_hist[i - 1] < 0) and (self.macd_hist[i] > 0) and (self.WilliamsR_low[i] < r):
        #         return True
            # max
            # for j in range(1, r_period):
            #     if self.close_data[i - j] < self.close_data[i]:
            #         return True
        return False

    def SellStrategy(self, i, t, r, r_down, r_up):
        if i - t + 1 > 0 and self.buy_ichi:
            if ((self.close_data[i] < self.ich_b[i - t + 1] and
                    self.close_data[i] < self.ich_a[i - t + 1])):
                self.buy_ichi = False
                return True
        # if not self.buy_ichi:
        #     if ((self.WilliamsR_low[i - 1] > r_down and self.WilliamsR_low[i] < r_down)) or \
        #             ((self.WilliamsR_high[i - 1] > r_up and self.WilliamsR_high[i] < r_up)) or \
        #             ((self.macd_hist[i - 1] > 0) and (self.macd_hist[i] < 0)):
        #         return True
        return False

class ICHIMOKU_Strategy_Test(ICHIMOKU_2_Strategy):

    def __init__(self, high, low, close):
        super().__init__(high, low, close)
        self.buy_ichi = False
        self.buy_ema = True

    def BuyStrategy(self, i, t, a, b, r, r_period):
        if i - t + 1 > 0:
            if self.buy_ema and not self.buy_ichi:
                if (self.close_data[i] >= self.ich_base_line[i] and self.ich_a[i] >= self.ich_b[i] and
                        self.close_data[i] >= self.ich_b[i - t + 1] and self.close_data[i] >= self.ich_a[i - t + 1] and
                        self.ich_conversion_line[i] >= self.ich_base_line[i] >= self.ich_a[i - t + 1]):
                    if a >= (self.close_data[i] - self.ich_a[i - t + 1]) / self.close_data[i] and\
                            a >= (self.close_data[i] - self.ich_b[i - t + 1]) / self.close_data[i]:
                        self.buy_ichi = True
                        return True
        if not self.buy_ema and self.buy_ichi:
            if self.ema[i] < self.close_data[i] and self.macd_hist[i] > 0:
                return True
        return False

    def SellStrategy(self, i, t, r, r_down, r_up):
        if i - t + 1 > 0 and self.buy_ichi:
            if ((self.close_data[i] < self.ich_b[i - t + 1] and
                    self.close_data[i] < self.ich_a[i - t + 1])):
                self.buy_ichi = False
                self.buy_ema = True
                return True
        if self.ema[i] > self.close_data[i] and self.buy_ichi:
            self.buy_ema = False
            return True
        return False

class ICHIMOKU_Strategy_HMA(ICHIMOKU_2_Strategy):

    def __init__(self, high, low, close):
        super().__init__(high, low, close)
        self.buy_ichi = False
        self.buy_hma = True

    def BuyStrategy(self, i, t, a):
        if i - t + 1 > 0:
            if not self.buy_ichi:
                if (self.close_data[i] >= self.ich_base_line[i] and self.ich_a[i] >= self.ich_b[i] and
                        self.close_data[i] >= self.ich_b[i - t + 1] and self.close_data[i] >= self.ich_a[i - t + 1] and
                        self.ich_conversion_line[i] >= self.ich_base_line[i] >= self.ich_a[i - t + 1]):
                    if a >= (self.close_data[i] - self.ich_a[i - t + 1]) / self.close_data[i] and\
                            a >= (self.close_data[i] - self.ich_b[i - t + 1]) / self.close_data[i]:
                        self.buy_ichi = True
                        return True
        if self.hma[i] < self.dema[i] < self.close_data[i]:
            return True
        return False

    def SellStrategy(self, i, t):
        if i - t + 1 > 0 and self.buy_ichi:
            if ((self.close_data[i] < self.ich_b[i - t + 1] and
                    self.close_data[i] < self.ich_a[i - t + 1])):
                self.buy_ichi = False
                self.buy_hma = True
                return True
        elif self.hma[i] > self.close_data[i]:
            self.buy_hma = False
            return True
        return False


class ICHIMOKU_Strategy_HMA_Keltner(ICHIMOKU_2_Strategy):

    def __init__(self, high, low, close, cp):
        super().__init__(high, low, close)
        self.currency_pair = cp
        if sys.argv[2] == "o" or sys.argv[2] == "O":
            strategy_param = self.ReadConfigFile(self.currency_pair)
            self.buy_ichi = strategy_param["Buy_1"]
            self.buy_1 = strategy_param["Buy_2"]
        else:
            self.buy_ichi = False
            self.buy_1 = False

    def BuyStrategy(self, i, t, a):
        if i - t + 1 > 0:
            # if not self.buy_ichi:
            if (self.close_data[i] >= self.ich_base_line[i] and self.ich_a[i] >= self.ich_b[i] and
                    self.close_data[i] >= self.ich_b[i - t + 1] and self.close_data[i] >= self.ich_a[i - t + 1] and
                    self.ich_conversion_line[i] >= self.ich_base_line[i] >= self.ich_a[i - t + 1]):
                self.buy_ichi = True
                if sys.argv[2] == "o" or sys.argv[2] == "O":
                    self.WriteConfigFile(self.currency_pair, "Buy_1", True)
                return True
            else:
                self.buy_ichi = False
                if sys.argv[2] == "o" or sys.argv[2] == "O":
                    self.WriteConfigFile(self.currency_pair, "Buy_1", False)
            # if not self.buy_1:
            if (self.mc_ginley[i] < self.keltner.keltner_channel_hband()[i] < self.close_data[i]) and \
                    (self.close_data[i] >= self.ich_b[i - t + 1] and self.close_data[i] >= self.ich_a[i - t + 1]):
                self.buy_1 = True
                if sys.argv[2] == "o" or sys.argv[2] == "O":
                    self.WriteConfigFile(self.currency_pair, "Buy_2", True)
                return True
            else:
                self.buy_1 = False
                if sys.argv[2] == "o" or sys.argv[2] == "O":
                    self.WriteConfigFile(self.currency_pair, "Buy_2", False)
        return False

    def SellStrategy(self, i, t):
        if i - t + 1 > 0:
            if self.buy_ichi:
                if ((self.close_data[i] < self.ich_b[i - t + 1] and
                        self.close_data[i] < self.ich_a[i - t + 1])):
                    self.buy_ichi = False
                    if sys.argv[2] == "o" or sys.argv[2] == "O":
                        self.WriteConfigFile(self.currency_pair, "Buy_1", False)
                    return True
            elif self.buy_1:
                if (self.close_data[i] < self.ich_b[i - t + 1] and self.close_data[i] < self.ich_a[i - t + 1]) \
                    or self.mc_ginley[i] > self.close_data[i]:
                    self.buy_1 = False
                    if sys.argv[2] == "o" or sys.argv[2] == "O":
                        self.WriteConfigFile(self.currency_pair, "Buy_2", False)
                    return True
        return False


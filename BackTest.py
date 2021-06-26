import threading
from datetime import datetime, date
import time

import numpy
import pandas as pd

from binance.client import Client
from Algorithm import OfflineAlgorithm
from Strategy import ICHIMOKU_2_Strategy
from IO import CSVFiles, FileWorking


class Algorithm_1(OfflineAlgorithm):

    def __init__(self, candle):
        self.window1 = [9, 18, 24, 36]
        self.window2 = [24, 48, 72]
        self.window3_ = [48, 96, 144]
        self.t = [18, 26, 48]
        self.a = [0, 0.01]
        self.b = [0.04, 0.05, 0.06]
        self.SL_arr = [0.025, 0.05]
        # self.RR_arr = [1, 1.5, 2, 2.5, 3]

        # self.window1 = [36]
        # self.window2 = [48]
        # self.window3_ = [144]
        # self.t = [18]
        # self.a = [0]
        # self.b = [0.04]
        # self.SL_arr = [0.025, 0.05]

        self.fast = [12]
        self.slow = [78]
        self.signal = [18]

        global klines
        use_offline_data = True
        if use_offline_data:
            klines = FileWorking.ReadKlines("Data\\BTCUSDT_1HOUR_1.1.2019_1.1.2020.txt")
        else:
            klines = candle.getKlines("BNBUSDT", Client.KLINE_INTERVAL_1HOUR, "1 Jan, 2018", "1 Jan, 2020")
            FileWorking.WriteKlines(klines, "Data\\BNBUSDT_1HOUR_1.1.2018_1.1.2020.txt")
        candle.unpackCandle(klines)
        high = pd.Series(candle.high)
        low = pd.Series(candle.low)

        self.klines = klines
        self.close_data = candle.close

        self.ichi_2_strategy = ICHIMOKU_2_Strategy(high, low, self.close_data)

        self.file = CSVFiles("Strategy_2-New-2019_2020-BTCUSDT.csv")

    def BuyStrategy(self, i, win1, win2, win3, t, a, b, computeIndicator):
        if computeIndicator:
            self.ichi_2_strategy.ComputeIchimoku_A(win1, win2)
            self.ichi_2_strategy.ComputeIchimoku_B(win2, win3)
            self.ichi_2_strategy.ComputeIchimoku_Base_Line(win1, win2)
            self.ichi_2_strategy.ComputeIchimoku_Conversion_Line(win1, win2)
            self.ichi_2_strategy.ComputeMACD(self.fast[0], self.slow[0], self.signal[0])
        return self.ichi_2_strategy.BuyStrategy(i, t, a, b)

    def WriteResult(self, header, rows):
        self.file.SetCSVFieldName(header)
        self.file.WriteHeader()
        self.file.WriteRows(rows)

    def RunAlgorithm(self):
        fieldnames = ['Strategy', 'Win1', 'Win2', 'Win3', 'T', 'A', 'B', 'Total Net Profit',
                      'Gross Profit', 'Max Profit', 'Gross Loss', 'Max Loss', 'Profit Factor',
                      'Profit Trade (%)', 'Loss Trade (%)', 'Total Trade', 'Expected Payoff', 'Max Consecutive Wins',
                      'Avg Consecutive Wins', 'Max Consecutive Loss', 'Avg Consecutive Loss',
                      'Max Draw Down (%)', "Missing Profit"]
        rows = []
        for win1 in self.window1:
            for win2 in self.window2:
                for win3 in self.window3_:
                    for t in self.t:
                        print(win1, " ", win2, " ", win3, " ", t, " ")
                        for a in self.a:
                            for b in self.b:
                                # for SL in self.SL_arr:
                                ICHIMOKU_fill = True
                                balance = 1000
                                isNotPos = True
                                balance_arr = []
                                max_balance = balance
                                min_balance = balance
                                Max_DD_arr = [0]
                                profit = 0
                                profit_arr = [0]
                                loss = 0
                                loss_arr = [0]
                                profit_count = 0
                                loss_count = 0
                                temp_profit_count = 0
                                max_profit_count = 0
                                avg_profit_count = []
                                temp_loss_count = 0
                                max_loss_count = 0
                                avg_loss_count = []
                                max_price = 0
                                buy_price = 0
                                missing_profit = []
                                for i in range(1, len(self.klines) - 1):
                                    if self.BuyStrategy(i, win1, win2, win3, t, a, b, ICHIMOKU_fill) and isNotPos:
                                        isNotPos = False
                                        buy_price = self.close_data[i]
                                        max_price = buy_price
                                        order_time = datetime.utcfromtimestamp(self.klines[i][0] / 1000)
                                        # print("Win1=", win1, " Win2=", win2, "T=", t, " Win3=", win3)
                                        # print("Order ", profit_count + loss_count, " Buy_Price = ", buy_price,
                                        #       "Date = ", order_time)
                                        i += 1
                                        volume = balance
                                    if not isNotPos:
                                        if self.ichi_2_strategy.SellStrategy(i, t):# or\
                                        #     ((buy_price - self.close_data[i]) / buy_price) > SL:
                                            if self.close_data[i] - buy_price < 0:
                                                loss += ((buy_price - self.close_data[i]) / buy_price) * volume
                                                loss_arr.append(((buy_price - self.close_data[i]) / buy_price) * volume)
                                                balance -= ((buy_price - self.close_data[i]) / buy_price) * volume
                                                balance_arr.append(balance)
                                                # print("(Loss) Balance = ", balance, "Date = ",  datetime.utcfromtimestamp(self.klines[i][0] / 1000),
                                                #       "Sell Price = ", self.close_data[i] , "Max Price = ", max_price,
                                                #       "Missing Profit = ",(max_price - self.close_data[i]) / max_price)
                                                loss_count += 1
                                                temp_loss_count += 1
                                                if max_profit_count < temp_profit_count:
                                                    max_profit_count = temp_profit_count
                                                if temp_profit_count != 0:
                                                    avg_profit_count.append(temp_profit_count)
                                                temp_profit_count = 0
                                                if min_balance > balance:
                                                    min_balance = balance
                                                    Max_DD_arr[-1] = ((max_balance - min_balance) / max_balance)
                                                isNotPos = True
                                                # writer.writerow({'Order': profit_count + loss_count, 'Price': buy_price,
                                                #                  'Time': order_time, 'Sell Time': klines[i][0],
                                                #                  'Loss/Profit': "Loss", 'Sell Price': close_arr[i],
                                                #                  'Volume': volume})
                                            else:
                                                profit += ((self.close_data[i] - buy_price) / buy_price) * volume
                                                profit_arr.append(((self.close_data[i] - buy_price) / buy_price) * volume)
                                                balance += ((self.close_data[i] - buy_price) / buy_price) * volume
                                                balance_arr.append(balance)
                                                # print("(Profit) Balance = ", balance, "Date = ",  datetime.utcfromtimestamp(self.klines[i][0] / 1000),
                                                #       "Sell Price = ", self.close_data[i] , "Max Price = ", max_price,
                                                #       "Missing Profit = ",(max_price - self.close_data[i]) / max_price)
                                                profit_count += 1
                                                temp_profit_count += 1
                                                if max_loss_count < temp_loss_count:
                                                    max_loss_count = temp_loss_count
                                                if temp_loss_count != 0:
                                                    avg_loss_count.append(temp_loss_count)
                                                temp_loss_count = 0
                                                if max_balance < balance:
                                                    max_balance = balance
                                                    min_balance = balance
                                                    Max_DD_arr.append((max_balance - min_balance) / max_balance)
                                                isNotPos = True
                                            missing_profit.append((max_price - self.close_data[i]) / max_price)
                                                # writer.writerow({'Order': profit_count + loss_count, 'Price': buy_price,
                                                #                  'Time': order_time, 'Sell Time': klines[i][0],
                                                #                  'Loss/Profit': "Profit", 'Sell Price': close_arr[i],
                                                #                  'Volume': volume})
                                    if max_price < self.close_data[i]:
                                        max_price = self.close_data[i]
                                    ICHIMOKU_fill = False
                                # plt.imshow(balance)

                                # plt.plot(balance_arr)
                                # plt.show()
                                trade_count = profit_count + loss_count
                                if temp_profit_count != 0:
                                    avg_profit_count.append(temp_profit_count)
                                avg_profit = numpy.average(avg_profit_count)
                                if temp_loss_count != 0:
                                    avg_loss_count.append(temp_loss_count)
                                avg_loss = numpy.average(avg_loss_count)
                                # print("Total order = ", trade_count ,"SL =", SL, "RR = ", RR, "Balance = ", balance)
                                if loss == 0:
                                    profit_factor = profit
                                else:
                                    profit_factor = profit / loss

                                try:
                                    row = ["ICHIMOKU_Strategy", str(win1), str(win2), str(win3), t, a, b,
                                           balance - 1000, profit, numpy.max(profit_arr), loss, numpy.max(loss_arr),
                                           profit_factor, profit_count / trade_count, loss_count / trade_count, trade_count,
                                           (balance - 1000) / trade_count, max_profit_count, avg_profit, max_loss_count,
                                           avg_loss, numpy.max(Max_DD_arr) * 100, sum(missing_profit)]
                                    rows.append(row)
                                except ZeroDivisionError:
                                    row_zero_division = ["ICHIMOKU_Strategy", str(win1), str(win2), str(win3), t,
                                                         a, b, balance - 1000, profit, numpy.max(profit_arr), loss,
                                                         numpy.max(loss_arr), profit_factor, 0, 0, trade_count, 0,
                                                         max_profit_count, avg_profit, max_loss_count, avg_loss,
                                                         numpy.max(Max_DD_arr) * 100, sum(missing_profit)]
                                    rows.append(row_zero_division)
        self.WriteResult(fieldnames, rows)

class Algorithm_2(OfflineAlgorithm):
    klines = []
    ichi_2_strategy = []
    def __init__(self, candle, currency):
        self.window1 = [9, 18, 24, 36]
        self.window2 = [24, 48, 72]
        self.window3 = [48, 96, 144]
        self.t = [18, 26, 48]
        self.a = [0, 0.01]
        self.b = [0.04, 0.05, 0.06]
        # self.SL_arr = [0.025, 0.05]

        # self.window1 = [18]
        # self.window2 = [24]
        # self.window3 = [96]
        # self.t = [18]
        # self.a = [0]
        # self.b = [0.05]

        start_time = "1.1.2020"
        end_time = "1.1.2021"

        self.currency = currency
        use_offline_data = True
        for i in self.currency:
            if use_offline_data:
                self.klines.append(FileWorking.ReadKlines("Data\\" + i + "_1HOUR_" + start_time + "_" + end_time + ".txt"))
            else:
                self.klines.append(candle.getKlines(i, Client.KLINE_INTERVAL_1HOUR, "1 Jan, 2018", "1 Jan, 2020"))
                FileWorking.WriteKlines(klines[-1], "Data\\" + i + "_1HOUR_" + start_time + "_" + end_time + ".txt")
            candle.unpackCandle(self.klines[-1])
            high = pd.Series(candle.high)
            low = pd.Series(candle.low)

            self.close_data = candle.close

            self.ichi_2_strategy.append(ICHIMOKU_2_Strategy(high, low, self.close_data))

        self.file = CSVFiles("Strategy_2-New-2020_2021-BNBBTC.csv")
        self.result_row = []

    def CreateThread(self, main_param, second_param):
        try:
            self.th_sec = threading.Thread(target=self.SecondThread, args=(second_param,))
            self.th_sec.start()
            time.sleep(1)
            self.th_main = threading.Thread(target=self.MainThread, args=(main_param, second_param,))
            self.th_main.start()
        except:
            print("Error: unable to start thread")

    def RunAlgorithm(self):
        fieldnames = ['Strategy', 'Win1', 'Win2', 'Win3', 'T', 'A', 'B', 'Total Net Profit',
                      'Gross Profit', 'Max Profit', 'Gross Loss', 'Max Loss', 'Profit Factor',
                      'Profit Trade (%)', 'Loss Trade (%)', 'Total Trade', 'Expected Payoff', 'Max Consecutive Wins',
                      'Avg Consecutive Wins', 'Max Consecutive Loss', 'Avg Consecutive Loss',
                      'Max Draw Down (%)', 'Max Draw Down (Time)', 'ETH Profit', 'ETH Loss', 'ETH Profit Trade (%)',
                      'ETH Loss Trade (%)', 'ETH Total Trade', 'ETH Missing Profit']

        main_thread_param = {"Win1": 36, "Win2": 72, "Win3": 96, "t": 26, "a": 0.01, "b": 0.06}
        for win1 in self.window1:
            for win2 in self.window2:
                for win3 in self.window3:
                    for t in self.t:
                        print(win1, " ", win2, " ", win3, " ", t, " ")
                        for a in self.a:
                            for b in self.b:
                                second_thread_param = {"Win1": win1, "Win2": win2, "Win3": win3, "t": t, "a": a, "b": b}
                                self.CreateThread(main_thread_param, second_thread_param)
                                self.th_main.join()
                                self.th_sec.join()
        self.WriteResult(fieldnames, self.result_row)

    def SecondThread(self, param):
        self.BuySignal = [False] * len(self.klines[-1])
        update_strategy = True
        isNotPos = True
        j = 1
        while j < len(self.klines[-1]) - 1:
            # print("EB = ", i)
            # BuySignal = False
            if update_strategy:
                self.ichi_2_strategy[-1].ComputeIchimoku_A(param["Win1"], param["Win2"])
                self.ichi_2_strategy[-1].ComputeIchimoku_B(param["Win2"], param["Win3"])
                self.ichi_2_strategy[-1].ComputeIchimoku_Base_Line(param["Win1"], param["Win2"])
                self.ichi_2_strategy[-1].ComputeIchimoku_Conversion_Line(param["Win1"], param["Win2"])
            if self.ichi_2_strategy[-1].BuyStrategy(j, param["t"], param["a"], param["b"]) and isNotPos:
                self.BuySignal[j] = True
                isNotPos = False
            elif not isNotPos:
                if j - param["t"] - 1 > 0:
                    if self.ichi_2_strategy[-1].SellStrategy(j, param["t"]):
                        self.BuySignal[j] = False
                        isNotPos = True
                    else:
                        self.BuySignal[j] = True
            update_strategy = False
            j += 1

    def MainThread(self, param, second_param):
        update_strategy = True
        balance_dict = {"Current": 1000, "Max": 1000, "Min": 1000}

        isNotPos = {self.currency[0]: True, self.currency[1]: True}
        balance_arr = []
        buy_price = {}
        Max_DD_arr = []
        profit_arr = []
        loss_arr = []
        profit_count = 0
        profit_count_arr = []
        loss_count = 0
        loss_count_arr = []
        secondery_max_price = 0
        secondery_missing_profit = []
        secondery_profit = []
        secondery_loss = []
        for i in range(1, len(self.klines[0]) - 1):
            if update_strategy:
                self.ichi_2_strategy[0].ComputeIchimoku_A(param["Win1"], param["Win2"])
                self.ichi_2_strategy[0].ComputeIchimoku_B(param["Win2"], param["Win3"])
                self.ichi_2_strategy[0].ComputeIchimoku_Base_Line(param["Win1"], param["Win2"])
                self.ichi_2_strategy[0].ComputeIchimoku_Conversion_Line(param["Win1"], param["Win2"])
            if self.ichi_2_strategy[0].BuyStrategy(i, param["t"], param["a"], param["b"])\
                    and isNotPos[self.currency[0]] and isNotPos[self.currency[1]]:
                if self.BuySignal[i]:
                    buy_price[self.currency[1]] = self.ichi_2_strategy[1].close_data[i]
                    isNotPos[self.currency[1]] = False
                    secondery_max_price = self.ichi_2_strategy[-1].close_data[i]
                    # print("Order ", len(profit_count_arr) + len(loss_count_arr),
                    #       " Buy_Price_" + self.currency[1] + " = ",
                    #       buy_price[self.currency[1]], " Volume = ",
                    #       balance_dict["Current"], " Date = ",
                    #       datetime.utcfromtimestamp(self.klines[0][i][0] / 1000))
                else:
                    buy_price[self.currency[0]] = self.ichi_2_strategy[0].close_data[i]
                    isNotPos[self.currency[0]] = False
                    # print("Order ", len(profit_count_arr) + len(loss_count_arr),
                    #       " Buy_Price_" + self.currency[0] + " = ",
                    #       buy_price[self.currency[0]], " Volume = ",
                    #       balance_dict["Current"], " Date = ",
                    #       datetime.utcfromtimestamp(self.klines[0][i][0] / 1000))
                i += 1
                self.volume = balance_dict["Current"]
            if not isNotPos[self.currency[1]]:
                if self.ichi_2_strategy[0].SellStrategy(i, param["t"]):  # or\
                    # ((buy_price - close_arr[i]) / buy_price) > SL:
                    if self.ichi_2_strategy[1].close_data[i] - buy_price[self.currency[1]] < 0:
                        loss = ((buy_price[self.currency[1]] - self.ichi_2_strategy[1].close_data[i]) /
                                buy_price[self.currency[1]]) * self.volume
                        loss_arr.append(loss)
                        balance_dict["Current"] -= loss
                        balance_arr.append(balance_dict["Current"])
                        # print("(Loss) Balance = ", balance_dict["Current"], "Sell_Price_" + self.currency[1] + " = ",
                        #       self.ichi_2_strategy[1].close_data[i],
                        #       "Date = ", datetime.utcfromtimestamp(self.klines[0][i][0] / 1000))
                        loss_count += 1
                        profit_count_arr.append(profit_count)
                        profit_count = 0
                        if balance_dict["Min"] > balance_dict["Current"]:
                            balance_dict["Min"] = balance_dict["Current"]
                            Max_DD_arr.append((balance_dict["Max"] - balance_dict["Min"]) / balance_dict["Max"])
                        isNotPos[self.currency[1]] = True
                        secondery_loss.append((buy_price[self.currency[1]] - self.ichi_2_strategy[1].close_data[i]) /
                                buy_price[self.currency[1]])
                        # writer.writerow({'Order': profit_count + loss_count, 'Price': buy_price,
                        #                  'Time': order_time, 'Sell Time': klines[i][0],
                        #                  'Loss/Profit': "Loss", 'Sell Price': close_arr[i],
                        #                  'Volume': volume})
                    else:
                        profit = ((self.ichi_2_strategy[1].close_data[i] - buy_price[self.currency[1]]) /
                                  buy_price[self.currency[1]]) * self.volume
                        profit_arr.append(profit)
                        balance_dict["Current"] += profit
                        balance_arr.append(balance_dict["Current"])
                        # print("(Profit) Balance = ", balance_dict["Current"], "Sell_Price_" + self.currency[1] + " = ",
                        #       self.ichi_2_strategy[1].close_data[i],
                        #       "Date = ", datetime.utcfromtimestamp(self.klines[0][i][0] / 1000))
                        profit_count += 1
                        loss_count_arr.append(loss_count)
                        loss_count = 0
                        if balance_dict["Max"] < balance_dict["Current"]:
                            balance_dict["Max"] = balance_dict["Current"]
                            balance_dict["Min"] = balance_dict["Current"]
                            Max_DD_arr.append((balance_dict["Max"] - balance_dict["Min"]) / balance_dict["Max"])
                        isNotPos[self.currency[1]] = True
                        secondery_profit.append((self.ichi_2_strategy[1].close_data[i] -
                                                 buy_price[self.currency[1]]) / buy_price[self.currency[1]])
                        # writer.writerow({'Order': profit_count + loss_count, 'Price': buy_price,
                        #                  'Time': order_time, 'Sell Time': klines[i][0],
                        #                  'Loss/Profit': "Profit", 'Sell Price': close_arr[i],
                        #                  'Volume': volume})
                elif not self.BuySignal[i]:  # (close_arr_EB[i] < ich_b_EB[i - t_EB - 1] and close_arr_EB[i] < ich_a_EB[i - t_EB - 1]):
                    self.volume = (self.volume / buy_price[self.currency[1]]) * self.ichi_2_strategy[1].close_data[i]
                    balance_dict["Current"] = self.volume
                    buy_price[self.currency[0]] = self.ichi_2_strategy[0].close_data[i]
                    isNotPos[self.currency[1]] = True
                    isNotPos[self.currency[0]] = False
                    if self.ichi_2_strategy[1].close_data[i] - buy_price[self.currency[1]] < 0:
                        secondery_loss.append((buy_price[self.currency[1]] - self.ichi_2_strategy[1].close_data[i]) /
                                              buy_price[self.currency[1]])
                        secondery_missing_profit.append((buy_price[self.currency[1]] - self.ichi_2_strategy[1].close_data[i]) /
                                                        buy_price[self.currency[1]])
                    else:
                        secondery_profit.append((self.ichi_2_strategy[1].close_data[i] - buy_price[self.currency[1]]) /
                                                buy_price[self.currency[1]])
                    secondery_missing_profit.append((secondery_max_price - self.ichi_2_strategy[-1].close_data[i]) / secondery_max_price)
                    # print("Volume = ", balance_dict["Current"],
                    #       "Sell_Price_" + self.currency[1] + "= ",
                    #       self.ichi_2_strategy[1].close_data[i],
                    #       "Buy_Price_" + self.currency[0] + " = ",
                    #       buy_price[self.currency[0]],
                    #       "Date = ", datetime.utcfromtimestamp(self.klines[0][i][0] / 1000))
            elif not isNotPos[self.currency[0]]:
                if self.ichi_2_strategy[0].SellStrategy(i, param["t"]):
                    if self.ichi_2_strategy[0].close_data[i] - buy_price[self.currency[0]] < 0:
                        loss = ((buy_price[self.currency[0]] - self.ichi_2_strategy[0].close_data[i]) /
                                buy_price[self.currency[0]]) * self.volume
                        loss_arr.append(loss)
                        balance_dict["Current"] -= loss
                        balance_arr.append(balance_dict["Current"])
                        # print("(Loss) Balance = ", balance_dict["Current"], "Sell_Price_" + self.currency[0] + " = ",
                        #       self.ichi_2_strategy[0].close_data[i],
                        #       "Date = ", datetime.utcfromtimestamp(self.klines[0][i][0] / 1000))
                        loss_count += 1
                        profit_count_arr.append(profit_count)
                        profit_count = 0
                        if balance_dict["Min"] > balance_dict["Current"]:
                            balance_dict["Min"] = balance_dict["Current"]
                            Max_DD_arr.append((balance_dict["Max"] - balance_dict["Min"]) / balance_dict["Max"])

                        isNotPos[self.currency[0]] = True
                        # writer.writerow({'Order': profit_count + loss_count, 'Price': buy_price,
                        #                  'Time': order_time, 'Sell Time': klines[i][0],
                        #                  'Loss/Profit': "Loss", 'Sell Price': close_arr[i],
                        #                  'Volume': volume})
                    else:
                        profit = ((self.ichi_2_strategy[0].close_data[i] - buy_price[self.currency[0]]) /
                                  buy_price[self.currency[0]]) * self.volume
                        profit_arr.append(profit)
                        balance_dict["Current"] += profit
                        balance_arr.append(balance_dict["Current"])
                        # print("(Profit) Balance = ", balance_dict["Current"], "Sell_Price_" + self.currency[0] + " = ",
                        #       self.ichi_2_strategy[0].close_data[i],
                        #       "Date = ", datetime.utcfromtimestamp(self.klines[0][i][0] / 1000))
                        profit_count += 1
                        loss_count_arr.append(loss_count)
                        loss_count = 0
                        if balance_dict["Max"] < balance_dict["Current"]:
                            balance_dict["Max"] = balance_dict["Current"]
                            balance_dict["Min"] = balance_dict["Current"]
                            Max_DD_arr.append((balance_dict["Max"] - balance_dict["Min"]) / balance_dict["Max"])
                        isNotPos[self.currency[0]] = True
                        # writer.writerow({'Order': profit_count + loss_count, 'Price': buy_price,
                        #                  'Time': order_time, 'Sell Time': klines[i][0],
                        #                  'Loss/Profit': "Profit", 'Sell Price': close_arr[i],
                        #                  'Volume': volume})
                elif self.BuySignal[i]:  # ICHIMOKU_2_EB(i, 24, 48, 144, 0.01, 0.06, ICHIMOKU_fill_EB):
                    self.volume = (self.volume / buy_price[self.currency[0]]) * self.ichi_2_strategy[0].close_data[i]
                    balance_dict["Current"] = self.volume
                    buy_price[self.currency[1]] = self.ichi_2_strategy[1].close_data[i]
                    isNotPos[self.currency[0]] = True
                    isNotPos[self.currency[1]] = False
                    secondery_max_price = self.ichi_2_strategy[2].close_data[i]
                    # print("Volume = ", balance_dict["Current"],
                    #       "Sell_Price_" + self.currency[0] + "= ",
                    #       self.ichi_2_strategy[0].close_data[i],
                    #       "Buy_Price_" + self.currency[1] + " = ",
                    #       buy_price[self.currency[1]],
                    #       "Date = ", datetime.utcfromtimestamp(self.klines[0][i][0] / 1000))
            if secondery_max_price < self.ichi_2_strategy[2].close_data[i]:
                secondery_max_price = self.ichi_2_strategy[2].close_data[i]
            update_strategy = False
            # th.join()
        # plt.imshow(balance)

        # plt.plot(balance_arr)
        # plt.show()
        trade_count = len(profit_arr) + len(loss_arr)
        profit_count_arr.append(profit_count)
        avg_profit = numpy.average(profit_count_arr)
        loss_count_arr.append(loss_count)
        avg_loss = numpy.average(loss_count_arr)
        # print("Total order = ", trade_count ,"SL =", SL, "RR = ", RR, "Balance = ", balance)
        if len(loss_arr) == 0:
            profit_factor = sum(profit_arr)
        else:
            profit_factor = sum(profit_arr) / sum(loss_arr)
        try:
            row = ["Algorithm_2", second_param["Win1"], second_param["Win2"], second_param["Win3"], second_param["t"], second_param["a"],
                          second_param["b"], balance_dict["Current"] - 1000, sum(profit_arr), max(profit_arr), sum(loss_arr),
                          max(loss_arr), profit_factor, len(profit_arr) / trade_count, len(loss_arr) / trade_count,
                          trade_count, (balance_dict["Current"] - 1000) / trade_count, max(profit_count_arr),
                          avg_profit, max(loss_count_arr), avg_loss, max(Max_DD_arr) * 100, 0,sum(secondery_profit),
                          sum(secondery_loss), len(secondery_profit) / (len(secondery_profit) + len(secondery_loss)),
                          len(secondery_loss) / (len(secondery_profit) + len(secondery_loss)),
                          len(secondery_profit) + len(secondery_loss), sum(secondery_missing_profit)]
        except ZeroDivisionError:
            row = ["Algorithm_2", second_param["Win1"], second_param["Win2"], second_param["Win3"], second_param["t"], second_param["a"],
                          second_param["b"], balance_dict["Current"] - 1000, sum(profit_arr), max(profit_arr), sum(loss_arr),
                          max(loss_arr), profit_factor, 0, 0, trade_count, 0, max(profit_count_arr), avg_profit,
                          max(loss_count_arr), avg_loss, max(Max_DD_arr) * 100, 0, sum(secondery_profit), sum(secondery_loss),
                          0, 0, len(secondery_profit) + len(secondery_loss), sum(secondery_missing_profit)]

        self.result_row.append(row)

    def WriteResult(self, header, rows):
        self.file.SetCSVFieldName(header)
        self.file.WriteHeader()
        self.file.WriteRows(rows)

class Algorithm_3(OfflineAlgorithm):
    klines = {}
    ichi_2_strategy = {}
    Buy_Signal = {}
    def __init__(self, candle, currency, currency_pair, correspond):
        self.window1 = [9, 18, 24, 36]
        self.window2 = [24, 48, 72]
        self.window3 = [48, 96, 144]
        self.t = [18, 26, 48]
        self.a = [0, 0.01]
        self.b = [0.04, 0.05, 0.06]
        self.SL_arr = [0.025, 0.05]

        # self.window1 = [18]
        # self.window2 = [24]
        # self.window3 = [96]
        # self.t = [18]
        # self.a = [0]
        # self.b = [0.05]

        start_time = "1.1.2018"
        end_time = "1.1.2020"

        self.currency = currency
        self.currency_pair = currency_pair
        self.correspond_currency = correspond
        use_offline_data = True
        for i in self.currency:
            if use_offline_data:
                self.klines[i] = (FileWorking.ReadKlines("Data\\" + i + "_1HOUR_" + start_time + "_" + end_time + ".txt"))
            else:
                self.klines[i] = (candle.getKlines(i, Client.KLINE_INTERVAL_1HOUR, "1 Jan, 2018", "1 Jan, 2020"))
                FileWorking.WriteKlines(self.klines[i], "Data\\" + i + "_1HOUR_" + start_time + "_" + end_time + ".txt")
            candle.unpackCandle(self.klines[i])
            high = pd.Series(candle.high)
            low = pd.Series(candle.low)

            self.close_data = candle.close

            self.ichi_2_strategy[i] = (ICHIMOKU_2_Strategy(high, low, self.close_data))

        for i in self.currency_pair:
            if use_offline_data:
                self.klines[i] = (FileWorking.ReadKlines("Data\\" + i + "_1HOUR_" + start_time + "_" + end_time + ".txt"))
            else:
                self.klines[i] = (candle.getKlines(i, Client.KLINE_INTERVAL_1HOUR, "1 Jan, 2018", "1 Jan, 2020"))
                FileWorking.WriteKlines(self.klines[i], "Data\\" + i + "_1HOUR_" + start_time + "_" + end_time + ".txt")
            candle.unpackCandle(self.klines[i])
            high = pd.Series(candle.high)
            low = pd.Series(candle.low)

            self.close_data = candle.close

            self.ichi_2_strategy[i] = (ICHIMOKU_2_Strategy(high, low, self.close_data))

        self.file = CSVFiles("Strategy_2-2018_2020-ETHBNBBTC.csv")
        self.result_row = []
        self.Buy_Signal = {}

    def CreateThread(self, main_param, second_param):
        self.th_sec = {}
        try:
            for i in self.currency_pair:
                self.th_sec[i] = threading.Thread(target=self.SecondThread, args=(second_param, i,))
                self.th_sec[i].start()
            time.sleep(1)
            self.th_main = threading.Thread(target=self.MainThread, args=(main_param, second_param, ))
            self.th_main.start()
        except:
            print("Error: unable to start thread")

    def RunAlgorithm(self):
        fieldnames = ['Strategy', 'Win1', 'Win2', 'Win3', 'T', 'A', 'B', 'Total Net Profit',
                      'Gross Profit', 'Max Profit', 'Gross Loss', 'Max Loss', 'Profit Factor',
                      'Profit Trade (%)', 'Loss Trade (%)', 'Total Trade', 'Expected Payoff', 'Max Consecutive Wins',
                      'Avg Consecutive Wins', 'Max Consecutive Loss', 'Avg Consecutive Loss',
                      'Max Draw Down (%)', 'Max Draw Down (Time)']

        main_thread_param = {"Win1": 36, "Win2": 48, "Win3": 144, "t": 18, "a": 0, "b": 0.04}
        for win1 in self.window1:
            for win2 in self.window2:
                for win3 in self.window3:
                    for t in self.t:
                        print(win1, " ", win2, " ", win3, " ", t, " ")
                        for a in self.a:
                            for b in self.b:
                                second_thread_param = {"Win1": win1, "Win2": win2, "Win3": win3, "t": t, "a": a, "b": b}
                                self.CreateThread(main_thread_param, second_thread_param)
                                time.sleep(10)
                                self.th_main.join()
                                for i in self.currency_pair:
                                    self.th_sec[i].join()
        self.WriteResult(fieldnames, self.result_row)

    def SecondThread(self, param, currency):
        self.Buy_Signal[currency] = [False] * len(self.klines[currency])
        update_strategy = True
        isNotPos = True
        j = 1
        while j < len(self.klines[currency]) - 1:
            if update_strategy:
                self.ichi_2_strategy[currency].ComputeIchimoku_A(param["Win1"], param["Win2"])
                self.ichi_2_strategy[currency].ComputeIchimoku_B(param["Win2"], param["Win3"])
                self.ichi_2_strategy[currency].ComputeIchimoku_Base_Line(param["Win1"], param["Win2"])
                self.ichi_2_strategy[currency].ComputeIchimoku_Conversion_Line(param["Win1"], param["Win2"])
            if self.ichi_2_strategy[currency].BuyStrategy(j, param["t"], param["a"], param["b"]) and isNotPos:
                self.Buy_Signal[currency][j] = True
                isNotPos = False
            elif not isNotPos:
                if j - param["t"] - 1 > 0:
                    if self.ichi_2_strategy[currency].SellStrategy(j, param["t"]):
                        self.Buy_Signal[currency][j] = False
                        isNotPos = True
                    else:
                        self.Buy_Signal[currency][j] = True
            update_strategy = False
            j += 1

    def MainThread(self, param, second_param):
        update_strategy = True
        balance_dict = {"Current": 1000, "Max": 1000, "Min": 1000, "Available": 1000}
        isNotPos = {}
        for i in self.currency:
            isNotPos[i] = True
        balance_arr = []
        buy_price = {}
        Max_DD_arr = []
        profit_arr = []
        loss_arr = []
        profit_count = 0
        profit_count_arr = []
        loss_count = 0
        loss_count_arr = []
        True_Buy_Signal = []
        order_count = 0
        for i in range(1, len(self.klines[self.currency[0]]) - 1):
            if update_strategy:
                self.ichi_2_strategy[self.currency[0]].ComputeIchimoku_A(param["Win1"], param["Win2"])
                self.ichi_2_strategy[self.currency[0]].ComputeIchimoku_B(param["Win2"], param["Win3"])
                self.ichi_2_strategy[self.currency[0]].ComputeIchimoku_Base_Line(param["Win1"], param["Win2"])
                self.ichi_2_strategy[self.currency[0]].ComputeIchimoku_Conversion_Line(param["Win1"], param["Win2"])
            if self.ichi_2_strategy[self.currency[0]].BuyStrategy(i, param["t"], param["a"], param["b"]) \
                    and self.CheckAllPos(isNotPos):
                True_Buy_Signal = self.FindBuySignal(self.Buy_Signal, i)
                if len(True_Buy_Signal) != 0:
                    for j in True_Buy_Signal:
                        buy_price[self.correspond_currency[j]] = \
                        self.ichi_2_strategy[self.correspond_currency[j]].close_data[i]
                        isNotPos[self.correspond_currency[j]] = False
                        # print("Order ", order_count, " Buy_Price_" + self.correspond_currency[j] + " = ",
                        #       buy_price[self.correspond_currency[j]], " Volume = ",
                        #       balance_dict["Current"] / len(True_Buy_Signal), " Date = ",
                        #       datetime.utcfromtimestamp(self.klines[self.currency[0]][i][0] / 1000))
                    self.volume = balance_dict["Current"] / len(True_Buy_Signal)
                else:
                    buy_price[self.currency[0]] = self.ichi_2_strategy[self.currency[0]].close_data[i]
                    isNotPos[self.currency[0]] = False
                    self.volume = balance_dict["Current"]
                    # print("Order ", order_count, " Buy_Price_" + self.currency[0] + " = ",
                    #       buy_price[self.currency[0]], " Volume = ", self.volume,
                    #       "Date = ", datetime.utcfromtimestamp(self.klines[self.currency[0]][i][0] / 1000))
                balance_dict["Available"] = 0
                i += 1
            if not isNotPos[self.currency[0]]:
                if self.ichi_2_strategy[self.currency[0]].SellStrategy(i, param["t"]):
                    if self.ichi_2_strategy[self.currency[0]].close_data[i] - buy_price[self.currency[0]] < 0:
                        loss = ((buy_price[self.currency[0]] - self.ichi_2_strategy[self.currency[0]].close_data[i]) /
                                buy_price[self.currency[0]]) * self.volume
                        loss_arr.append(loss)
                        balance_dict["Current"] -= loss
                        balance_arr.append(balance_dict["Current"])
                        # print("(Loss) Balance = ", balance_dict["Current"], "Sell_Price_" + self.currency[0] + " = ",
                        #       self.ichi_2_strategy[self.currency[0]].close_data[i],
                        #       "Date = ", datetime.utcfromtimestamp(self.klines[self.currency[0]][i][0] / 1000))
                        loss_count += 1
                        profit_count_arr.append(profit_count)
                        profit_count = 0
                        isNotPos[self.currency[0]] = True
                        # writer.writerow({'Order': profit_count + loss_count, 'Price': buy_price,
                        #                  'Time': order_time, 'Sell Time': klines[i][0],
                        #                  'Loss/Profit': "Loss", 'Sell Price': close_arr[i],
                        #                  'Volume': volume})
                    else:
                        profit = ((self.ichi_2_strategy[self.currency[0]].close_data[i] - buy_price[self.currency[0]]) /
                                  buy_price[self.currency[0]]) * self.volume
                        profit_arr.append(profit)
                        balance_dict["Current"] += profit
                        balance_arr.append(balance_dict["Current"])
                        # print("(Profit) Balance = ", balance_dict["Current"], "Sell_Price_" + self.currency[0] + " = ",
                        #       self.ichi_2_strategy[self.currency[0]].close_data[i],
                        #       "Date = ", datetime.utcfromtimestamp(self.klines[self.currency[0]][i][0] / 1000))
                        profit_count += 1
                        loss_count_arr.append(loss_count)
                        loss_count = 0
                        isNotPos[self.currency[0]] = True
                        # writer.writerow({'Order': profit_count + loss_count, 'Price': buy_price,
                        #                  'Time': order_time, 'Sell Time': klines[i][0],
                        #                  'Loss/Profit': "Profit", 'Sell Price': close_arr[i],
                        #                  'Volume': volume})
                    order_count += 1
                else:
                    True_Buy_Signal = self.FindBuySignal(self.Buy_Signal, i)
                    if len(True_Buy_Signal) != 0:
                        balance_dict["Available"] = (self.volume / buy_price[self.currency[0]]) * \
                                                    self.ichi_2_strategy[self.currency[0]].close_data[i]
                        for j in True_Buy_Signal:
                            buy_price[self.correspond_currency[j]] = \
                            self.ichi_2_strategy[self.correspond_currency[j]].close_data[i]
                            isNotPos[self.correspond_currency[j]] = False
                            # print("Volume = ", balance_dict["Available"] / len(True_Buy_Signal),
                            #       "Sell_Price_" + self.currency[0] + "= ",
                            #       self.ichi_2_strategy[self.currency[0]].close_data[i],
                            #       "Buy_Price_" + self.correspond_currency[j] + " = ",
                            #       buy_price[self.correspond_currency[j]],
                            #       "Date = ", datetime.utcfromtimestamp(self.klines[self.currency[0]][i][0] / 1000))
                        self.volume = balance_dict["Available"] / len(True_Buy_Signal)
                        balance_dict["Current"] = balance_dict["Available"]
                        balance_dict["Available"] = 0
                        isNotPos[self.currency[0]] = True
            elif not self.CheckAllPos(isNotPos):
                if self.ichi_2_strategy[self.currency[0]].SellStrategy(i, param["t"]):
                    balance_dict["Available"] = (self.volume * len(True_Buy_Signal))
                    for j in True_Buy_Signal:
                        if self.ichi_2_strategy[self.correspond_currency[j]].close_data[i] - \
                                buy_price[self.correspond_currency[j]] < 0:
                            loss = ((buy_price[self.correspond_currency[j]] -
                                     self.ichi_2_strategy[self.correspond_currency[j]].close_data[i]) /
                                    buy_price[self.correspond_currency[j]]) * self.volume
                            loss_arr.append(loss)
                            balance_dict["Available"] -= loss
                            loss_count += 1
                            profit_count_arr.append(profit_count)
                            profit_count = 0
                            # print("(Loss) Balance = ", balance_dict["Current"],
                            #       "Sell_Price_" + self.correspond_currency[j] + " = ",
                            #       self.ichi_2_strategy[self.correspond_currency[j]].close_data[i], "Date = ",
                            #       datetime.utcfromtimestamp(self.klines[self.currency[0]][i][0] / 1000))
                        else:
                            profit = ((self.ichi_2_strategy[self.correspond_currency[j]].close_data[i] -
                                       buy_price[self.correspond_currency[j]]) / buy_price[
                                          self.correspond_currency[j]]) * self.volume
                            profit_arr.append(profit)
                            balance_dict["Available"] += profit
                            profit_count += 1
                            loss_count_arr.append(loss_count)
                            loss_count = 0
                            # print("(Profit) Balance = ", balance_dict["Current"],
                            #       "Sell_Price_" + self.correspond_currency[j] + " = ",
                            #       self.ichi_2_strategy[self.correspond_currency[j]].close_data[i], "Date = ",
                            #       datetime.utcfromtimestamp(self.klines[self.currency[0]][i][0] / 1000))
                        balance_dict["Current"] = balance_dict["Available"]
                        balance_arr.append(balance_dict["Current"])
                        isNotPos[self.correspond_currency[j]] = True
                    order_count += 1
                elif len(True_Buy_Signal) != 0:
                    Sell_Signal_True = self.FindSellSignal(self.Buy_Signal, True_Buy_Signal, i)
                    Buy_Signal_New = self.FindBuySignal(self.Buy_Signal, i)
                    if len(Sell_Signal_True) != 0:
                        for j in Sell_Signal_True:
                            balance_dict["Available"] += (self.volume / buy_price[self.correspond_currency[j]]) * \
                                                        self.ichi_2_strategy[self.correspond_currency[j]].close_data[i]
                            isNotPos[self.correspond_currency[j]] = True
                        if len(Sell_Signal_True) == len(True_Buy_Signal):
                            buy_price[self.currency[0]] = self.ichi_2_strategy[self.currency[0]].close_data[i]
                            isNotPos[self.currency[0]] = False
                            self.volume = balance_dict["Available"]
                            balance_dict["Current"] = balance_dict["Available"]
                            balance_dict["Available"] = 0
                            # print("Volume = ", self.volume, "Sell_Price_" + self.correspond_currency[j] + "= ",
                            #       self.ichi_2_strategy[self.correspond_currency[j]].close_data[i],
                            #       "Buy_Price_" + self.currency[0] + " = ", buy_price[self.currency[0]],
                            #       "Date = ", datetime.utcfromtimestamp(self.klines[self.currency[0]][i][0] / 1000))
                        else:
                            True_Buy_Signal = self.FindBuySignal(self.Buy_Signal, i)
                            if len(True_Buy_Signal) != 0:
                                for j in True_Buy_Signal:
                                    balance_dict["Available"] += (self.volume / buy_price[self.correspond_currency[j]])\
                                                                 * self.ichi_2_strategy[self.correspond_currency[j]].close_data[i]
                                    buy_price[self.correspond_currency[j]] = \
                                    self.ichi_2_strategy[self.correspond_currency[j]].close_data[i]
                                    # print("Volume = ", self.volume,
                                    #       "Sell_Price",
                                    #       "Buy_Price_" + self.correspond_currency[j] + " = ",
                                    #       buy_price[self.correspond_currency[j]],
                                    #       "Date = ", datetime.utcfromtimestamp(self.klines[self.currency[0]][i][0] / 1000))
                                    isNotPos[self.correspond_currency[j]] = False
                                self.volume = balance_dict["Available"] / len(True_Buy_Signal)
                                balance_dict["Current"] = balance_dict["Available"]
                                balance_dict["Available"] = 0
                    elif len(True_Buy_Signal) != len(Buy_Signal_New) and len(Buy_Signal_New) != 0:
                        Buy_Signal_New = self.FindDiffrentBuySignal(True_Buy_Signal, Buy_Signal_New)
                        for j in True_Buy_Signal:
                            balance_dict["Available"] += (self.volume / buy_price[self.correspond_currency[j]]) * \
                                                         self.ichi_2_strategy[self.correspond_currency[j]].close_data[i]
                            buy_price[self.correspond_currency[j]] = self.ichi_2_strategy[self.correspond_currency[j]].close_data[i]
                        for k in Buy_Signal_New:
                            buy_price[self.correspond_currency[k]] = self.ichi_2_strategy[self.correspond_currency[k]].close_data[i]
                            isNotPos[self.correspond_currency[j]] = False
                        self.volume = balance_dict["Available"] / (len(Buy_Signal_New) + len(True_Buy_Signal))
                        balance_dict["Current"] = balance_dict["Available"]
                        balance_dict["Available"] = 0
                        # print("Volume = ", self.volume,
                        #       "Sell_Price_" + self.correspond_currency[j] + "= ",
                        #       self.ichi_2_strategy[self.correspond_currency[j]].close_data[i],
                        #       "Buy_Price_" + self.correspond_currency[Buy_Signal_New[0]] + " = ",
                        #       buy_price[self.correspond_currency[k]], "Date = ",
                        #       datetime.utcfromtimestamp(self.klines[self.currency[0]][i][0] / 1000))
                        True_Buy_Signal.extend(Buy_Signal_New)
            update_strategy = False
        trade_count = len(profit_arr) + len(loss_arr)
        profit_count_arr.append(profit_count)
        avg_profit = numpy.average(profit_count_arr)
        loss_count_arr.append(loss_count)
        avg_loss = numpy.average(loss_count_arr)
        # print("Total order = ", trade_count ,"SL =", SL, "RR = ", RR, "Balance = ", balance)
        if len(loss_arr) == 0:
            profit_factor = sum(profit_arr)
        else:
            profit_factor = sum(profit_arr) / sum(loss_arr)
        try:
            row = ["Algorithm_2", second_param["Win1"], second_param["Win2"], second_param["Win3"], second_param["t"], second_param["a"],
                          second_param["b"], balance_dict["Current"] - 1000, sum(profit_arr), max(profit_arr), sum(loss_arr),
                          max(loss_arr), profit_factor, len(profit_arr) / trade_count, len(loss_arr) / trade_count,
                          trade_count, (balance_dict["Current"] - 1000) / trade_count, max(profit_count_arr),
                          avg_profit, max(loss_count_arr), avg_loss, 0, 0]
        except ZeroDivisionError:
            row = ["Algorithm_2", second_param["Win1"], second_param["Win2"], second_param["Win3"], second_param["t"], second_param["a"],
                          second_param["b"], balance_dict["Current"] - 1000, sum(profit_arr), max(profit_arr), sum(loss_arr),
                          max(loss_arr), profit_factor, 0, 0, trade_count, 0, max(profit_count_arr), avg_profit,
                          max(loss_count_arr), avg_loss, 0, 0]

        self.result_row.append(row)
        print(row)

    def CheckAllPos(self, pos):
        for _,i in pos.items():
            if not i:
                return False
        return True

    def FindBuySignal(self, buy_signal, i):
        Buy_Signal_True = []
        for currency, yes in buy_signal.items():  # for name, age in dictionary.iteritems():  (for Python 2.x)
            if yes[i] == True:
                Buy_Signal_True.append(currency)
        return Buy_Signal_True

    def FindSellSignal(self, buy_signal, buy_currency, i):
        dict = {key: buy_signal[key] for key in buy_currency}
        Sell_Signal_True = []
        for currency, yes in dict.items():  # for name, age in dictionary.iteritems():  (for Python 2.x)
            if yes[i] == False:
                Sell_Signal_True.append(currency)
        return Sell_Signal_True

    def FindDiffrentBuySignal(self, source_1, source_2):
        return list(set(source_2) - set(source_1))

    def WriteResult(self, header, rows):
        self.file.SetCSVFieldName(header)
        self.file.WriteHeader()
        self.file.WriteRows(rows)

class Algorithm_4(Algorithm_3):

    def __init__(self, candle, currency):

        start_time = date(2021, 1, 1)
        end_time = date(2021, 6, 20)

        self.currency = currency
        self.currency_pair = []
        for i in self.currency[:-1]:
            self.currency_pair.append(i+self.currency[-1])
        self.currency_pair_secondery = []
        for i in self.currency[1:-1]:
            self.currency_pair_secondery.append(i+self.currency[0])

        self.correspond_currency = {}
        for i, item in enumerate(self.currency_pair_secondery):
            self.correspond_currency[self.currency[i+1]] = self.currency_pair[i+1]
            self.correspond_currency[self.currency_pair[i+1]] = item

        use_offline_data = True
        for i in self.currency_pair + self.currency_pair_secondery:
            if use_offline_data:
                self.klines[i] = (FileWorking.ReadKlines("Data\\" + i + "_1HOUR_" + start_time.isoformat() + "_" +
                                                         end_time.isoformat() + ".txt"))
            else:
                self.klines[i] = (candle.getKlines(i, Client.KLINE_INTERVAL_1HOUR, start_time.strftime("%d %b, %Y"),
                                                   end_time.strftime("%d %b, %Y")))
                FileWorking.WriteKlines(self.klines[i], "Data\\" + i + "_1HOUR_" + start_time.isoformat() + "_" +
                                        end_time.isoformat() + ".txt")
            candle.unpackCandle(self.klines[i])
            high = pd.Series(candle.high)
            low = pd.Series(candle.low)

            self.close_data = candle.close

            self.ichi_2_strategy[i] = (ICHIMOKU_2_Strategy(high, low, self.close_data))

        self.file = CSVFiles("Algorithm_4-" + start_time.strftime("%Y-%m-%d_") + end_time.strftime("%Y-%m-%d_") +
                             self.currency_pair[0] +"_Balance.csv")
        self.result_row = []
        self.Buy_Signal = {}
        self.param = {}
        self.BS = {}

    def SetAlgorithmParam(self, currency_pair, window1, window2, window3, t, a, b):
        p = {"Win1": window1, "Win2": window2, "Win3": window3, "t": t, "a": a, "b": b}
        self.param[currency_pair] = p

    def Run(self):
        self.CreateThread(self.param)
        for i in self.currency_pair + self.currency_pair_secondery:
            self.th[i].join()
        self.ComputeBuySignal()
        self.RunAlgorithm()

    def LogResult(self):
        # fieldnames = ['Strategy', 'Win1', 'Win2', 'Win3', 'T', 'A', 'B', 'Total Net Profit',
        #               'Gross Profit', 'Max Profit', 'Gross Loss', 'Max Loss', 'Profit Factor',
        #               'Profit Trade (%)', 'Loss Trade (%)', 'Total Trade', 'Expected Payoff', 'Max Consecutive Wins',
        #               'Avg Consecutive Wins', 'Max Consecutive Loss', 'Avg Consecutive Loss',
        #               'Max Draw Down (%)', 'Max Draw Down (Time)']

        fieldnames = ["Win1", "Win2", "Win3", "t", "a", "b"]
        fieldnames = fieldnames + ["Order" + str(k + 1) for k in range(0, 200)]
        self.WriteResult(fieldnames, self.result_row)

    def CreateThread(self, param):
        self.th = {}
        try:
            for i in self.currency_pair + self.currency_pair_secondery:
                self.th[i] = threading.Thread(target=self.BuySignalThread, args=(param, i,))
                self.th[i].start()
        except:
            print("Error: unable to start thread")

    def BuySignalThread(self, param, currency):
        self.BS[currency] = [False] * len(self.klines[currency])
        update_strategy = True
        isNotPos = True
        j = 1
        while j < len(self.klines[currency]) - 1:
            if update_strategy:
                self.ichi_2_strategy[currency].ComputeIchimoku_A(param[currency]["Win1"], param[currency]["Win2"])
                self.ichi_2_strategy[currency].ComputeIchimoku_B(param[currency]["Win2"], param[currency]["Win3"])
                self.ichi_2_strategy[currency].ComputeIchimoku_Base_Line(param[currency]["Win1"], param[currency]["Win2"])
                self.ichi_2_strategy[currency].ComputeIchimoku_Conversion_Line(param[currency]["Win1"], param[currency]["Win2"])
            if self.ichi_2_strategy[currency].BuyStrategy(j, param[currency]["t"], param[currency]["a"], param[currency]["b"]) and isNotPos:
                self.BS[currency][j] = True
                isNotPos = False
            elif not isNotPos:
                if j - param[currency]["t"] - 1 > 0:
                    if self.ichi_2_strategy[currency].SellStrategy(j, param[currency]["t"]):
                        self.BS[currency][j] = False
                        isNotPos = True
                    else:
                        self.BS[currency][j] = True
            update_strategy = False
            j += 1

    def ComputeBuySignal(self):
        self.Buy_Signal = []
        BS = {}
        for i in range(0, len(self.BS[self.currency_pair[0]])):
            b = self.FindBuySignal(self.BS, i)
            if self.currency_pair[0] in b:
                BS[self.currency[0]] = 1
            else:
                BS[self.currency[0]] = 0
            for j in self.currency[1:-1]:
                matching = [s for s in b if j in s]
                if len(matching) > 1:
                    BS[j] = 2
                elif len(matching) == 1 and matching[0] != j+self.currency[-1]:
                    BS[j] = 1
                else:
                    BS[j] = 0
            self.Buy_Signal.append(BS.copy())

    def FindKeyFromCurrency(self, currency_pair, currency):
        return [s for s in currency_pair if currency in s]

    def CheckAction(self, iter):
        Order = {"Buy": [], "Sell": [], "SellNotAll": []}
        zero_buy_signal = self.GetSpecificBuySignal(iter, 0)
        one_buy_signal = self.GetSpecificBuySignal(iter, 1)
        two_buy_signal = self.GetSpecificBuySignal(iter, 2)
        pos = self.CheckTrueIsPos()
        if len(pos) == 0 and self.currency[0] in one_buy_signal and len(one_buy_signal + two_buy_signal) == 1:#1
            Order["Buy"] = self.FindKeyFromCurrency(self.currency_pair, self.currency[0])
            self.isPos[self.currency[0]] = True
        elif self.currency[0] in pos:#4 6 8
            for i in two_buy_signal:
                Order["Buy"] += self.FindKeyFromCurrency(self.currency_pair_secondery, i)
                self.isPos[i] = True
            if self.currency[0] in one_buy_signal:
                for i in one_buy_signal:
                    if i != self.currency[0]:
                        Order["Buy"] += self.FindKeyFromCurrency(self.currency_pair_secondery, i)
                        self.isPos[i] = True
            elif self.currency[0] in zero_buy_signal and len(two_buy_signal) == 0:
                Order["Sell"] = self.FindKeyFromCurrency(self.currency_pair, self.currency[0])
                self.isPos[self.currency[0]] = False
            if len(Order["Buy"]) > 0:
                self.isPos[self.currency[0]] = False
            return Order
        elif len(pos) > 0 and self.currency[0] not in pos:
            if self.currency[0] in one_buy_signal and len(one_buy_signal + two_buy_signal) == 1:#2
                for i in pos:
                    Order["Sell"] += self.FindKeyFromCurrency(self.currency_pair_secondery, i)
                    self.isPos[i] = False
                self.isPos[self.currency[0]] = True
            elif self.CheckPosInBuySignal(pos, zero_buy_signal) or \
                    (self.currency[0] in zero_buy_signal and self.CheckPosInBuySignal(pos, one_buy_signal)):#5 7
                currency = self.currency_pair_secondery if self.currency[0] in one_buy_signal else self.currency_pair
                for i in pos:
                    if i in zero_buy_signal or (self.currency[0] in zero_buy_signal and i in one_buy_signal):
                        Order["Sell"] += self.FindKeyFromCurrency(currency, i)
                        self.isPos[i] = False
                for i in two_buy_signal:
                    Order["Buy"] += self.FindKeyFromCurrency(currency, i)
                    self.isPos[i] = True
                if self.currency[0] in one_buy_signal:
                    for i in one_buy_signal:
                        if i != self.currency[0]:
                            Order["Buy"] += self.FindKeyFromCurrency(currency, i)
                            self.isPos[i] = True
        if (len(two_buy_signal) > 0 or len(one_buy_signal) > 1) and \
                self.CheckNewBuy(pos, one_buy_signal, two_buy_signal):#3
            currency = self.currency_pair_secondery if len(pos) > 0 and self.currency[0] in one_buy_signal\
                else self.currency_pair
            for i in two_buy_signal:
                if i in pos:
                    Order["SellNotAll"] += self.FindKeyFromCurrency(currency, i)
                else:
                    Order["Buy"] += self.FindKeyFromCurrency(currency, i)
                    self.isPos[i] = True
            if self.currency[0] in one_buy_signal:
                for i in one_buy_signal:
                    if i in pos and i != self.currency[0]:
                        Order["SellNotAll"] += self.FindKeyFromCurrency(currency, i)
                    elif i != self.currency[0]:
                        Order["Buy"] += self.FindKeyFromCurrency(currency, i)
                        self.isPos[i] = True

        return Order

    def GetSpecificBuySignal(self, i, state):
        return [c for c, s in self.Buy_Signal[i].items() if s == state]

    def CheckTrueIsPos(self):
        return [k for k, s in self.isPos.items() if s]

    def CheckPosInBuySignal(self, pos, buy_signal_list):
        for i in pos:
            if i in buy_signal_list:
                return True
        return False

    def CheckNewBuy(self, pos, one_buy_signal, two_buy_signal):
        for i in two_buy_signal:
            if i not in pos:
                return True
        for i in one_buy_signal:
            if self.currency[0] in one_buy_signal and i != self.currency[0]:
                if i not in pos:
                    return True
        return False

    def RunAlgorithm(self):
        balance = {"Current": 1000, "Max": 1000, "Min": 1000, "Available": 1000, "All": []}
        self.isPos = {}
        valume = {}
        buy_price = {}
        for i in self.currency:
            self.isPos[i] = False
            valume[i] = 0
            buy_price[i] = 0
        profit = []
        loss = []
        isProfitOrLoss = []
        profit_percents = []
        loss_percents = []
        buy_count = 0
        sell_count = 0
        Max_DD_arr = []
        for i in range(1, len(self.klines[self.currency_pair[0]]) - 1):
            action = self.CheckAction(i)
            for j in action["Sell"]:
                sell_count += 1
                if self.currency[-1] in j:
                    d = self.ichi_2_strategy[j].close_data[i] - buy_price[j[:3]]
                    balance["Available"] += valume[j[:3]] * self.ichi_2_strategy[j].close_data[i]
                else:
                    d = self.ichi_2_strategy[j[:3] + self.currency[-1]].close_data[i] - buy_price[j[:3]]
                    balance["Available"] += valume[j[:3]] * self.ichi_2_strategy[j[:3] + self.currency[-1]].close_data[i]

                if d > 0:
                    profit.append(d * valume[j[:3]])
                    profit_percents.append(d / buy_price[j[:3]])
                    balance["Current"] += profit[-1]
                    balance["All"].append(balance["Current"])
                    # Max_DD_arr.append((max(balance["Current"]) - min(balance["Current"])) / max(balance["Current"]))
                    valume[j[:3]] = 0
                    isProfitOrLoss.append(1)
                else:
                    loss.append(abs(d) * valume[j[:3]])
                    loss_percents.append(abs(d) / buy_price[j[:3]])
                    valume[j[:3]] = 0
                    balance["Current"] -= loss[-1]
                    balance["All"].append(balance["Current"])
                    # Max_DD_arr.append((max(balance["Current"]) - min(balance["Current"])) / max(balance["Current"]))
                    isProfitOrLoss.append(0)

                if valume[self.currency[0]] == 0 and len(action["Buy"]) == 0:
                    if j[3:] == self.currency[0]:
                        buy_price[self.currency[0]] = self.ichi_2_strategy[self.currency_pair[0]].close_data[i]
                        valume[self.currency[0]] = balance["Available"] / buy_price[self.currency[0]]
                        balance["Available"] = 0

            for j in action["SellNotAll"]:
                sell_count +=1
                if self.currency[-1] in j:
                    d = self.ichi_2_strategy[j].close_data[i] - buy_price[j[:3]]
                    balance["Available"] += (valume[j[:3]] / len(action["SellNotAll"] + action["Buy"])) *\
                                            len(action["Buy"]) * self.ichi_2_strategy[j].close_data[i]
                else:
                    d = self.ichi_2_strategy[j[:3] + self.currency[-1]].close_data[i] - buy_price[j[:3]]
                    balance["Available"] += (valume[j[:3]] / len(action["SellNotAll"] + action["Buy"])) *\
                                            len(action["Buy"]) * \
                                            self.ichi_2_strategy[j[:3] + self.currency[-1]].close_data[i]
                if d > 0:
                    profit.append(d * (valume[j[:3]] / len(action["SellNotAll"] + action["Buy"])) * len(action["Buy"]))
                    profit_percents.append(d / buy_price[j[:3]])
                    valume[j[:3]] -= (valume[j[:3]] / len(action["SellNotAll"] + action["Buy"])) * len(action["Buy"])
                    balance["Current"] += profit[-1]
                    # Max_DD_arr.append((max(balance["Current"]) - min(balance["Current"])) / max(balance["Current"]))
                    isProfitOrLoss.append(1)
                else:
                    loss.append(abs(d) * (valume[j[:3]] / len(action["SellNotAll"] + action["Buy"])) * len(action["Buy"]))
                    loss_percents.append(abs(d) / buy_price[j[:3]])
                    valume[j[:3]] -= (valume[j[:3]] / len(action["SellNotAll"] + action["Buy"])) * len(action["Buy"])
                    balance["Current"] -= loss[-1]
                    # Max_DD_arr.append((max(balance["Current"]) - min(balance["Current"])) / max(balance["Current"]))
                    isProfitOrLoss.append(0)

            for j in action["Buy"]:
                buy_count += 1
                if valume[self.currency[0]] > 0 and len(j) > 0:
                    d = self.ichi_2_strategy[self.currency_pair[0]].close_data[i] - buy_price[self.currency[0]]
                    balance["Available"] = valume[self.currency[0]] * \
                                           self.ichi_2_strategy[self.currency_pair[0]].close_data[i]
                    if d > 0:
                        profit.append(d * valume[self.currency[0]])
                        profit_percents.append(d / buy_price[self.currency[0]])
                        valume[self.currency[0]] = 0
                        balance["Current"] += profit[-1]
                        # Max_DD_arr.append((max(balance["Current"]) - min(balance["Current"])) / max(balance["Current"]))
                        isProfitOrLoss.append(1)
                    else:
                        loss.append(abs(d) * valume[self.currency[0]])
                        loss_percents.append(abs(d) / buy_price[self.currency[0]])
                        valume[self.currency[0]] = 0
                        balance["Current"] -= loss[-1]
                        # Max_DD_arr.append((max(balance["Current"]) - min(balance["Current"])) / max(balance["Current"]))
                        isProfitOrLoss.append(0)

                if self.currency[-1] in j:
                    buy_price[j[:3]] = ((buy_price[j[:3]] * valume[j[:3]]) + self.ichi_2_strategy[j].close_data[i] *
                                        ((balance["Available"] / len(action["Buy"])) /
                                         self.ichi_2_strategy[j].close_data[i]))\
                                       / (((balance["Available"] / len(action["Buy"])) /
                                          self.ichi_2_strategy[j].close_data[i]) + valume[j[:3]])
                    valume[j[:3]] += ((balance["Available"] / len(action["Buy"])) / self.ichi_2_strategy[j].close_data[i])
                else:
                    buy_price[j[:3]] = ((buy_price[j[:3]] * valume[j[:3]]) +
                                        self.ichi_2_strategy[j[:3] + self.currency[-1]].close_data[i] *
                                        ((balance["Available"] / len(action["Buy"])) /
                                         self.ichi_2_strategy[j[:3] + self.currency[-1]].close_data[i]))\
                                       / (((balance["Available"] / len(action["Buy"])) /
                                           (self.ichi_2_strategy[j[:3] + self.currency[-1]].close_data[i])) + valume[j[:3]])
                    valume[j[:3]] += ((balance["Available"] / len(action["Buy"])) / self.ichi_2_strategy[j[:3] + self.currency[-1]].close_data[i])
            if len(action["Buy"]) > 0:
                balance["Available"] = 0

            # print(action)
        if len(loss) == 0:
            profit_factor = sum(profit)
        else:
            profit_factor = sum(profit) / sum(loss)

        p = 0
        l = 0
        profit_count = []
        loss_count = []
        for i in isProfitOrLoss:
            if i == 1:
                p += 1
                if l != 0:
                    loss_count.append(l)
                    l = 0
            if i == 0:
                l += 1
                if p != 0:
                    profit_count.append(p)
                    p = 0
        try:
            row = [self.param[self.currency_pair[0]]["Win1"], self.param[self.currency_pair[0]]["Win2"],
                   self.param[self.currency_pair[0]]["Win3"], self.param[self.currency_pair[0]]["t"],
                   self.param[self.currency_pair[0]]["a"], self.param[self.currency_pair[0]]["b"]]\
                  + [k for k in balance["All"]]

            # row = ["Algorithm_4", self.param[self.currency_pair_secondery[0]]["Win1"],
            #        self.param[self.currency_pair_secondery[0]]["Win2"],
            #        self.param[self.currency_pair_secondery[0]]["Win3"], self.param[self.currency_pair_secondery[0]]["t"],
            #        self.param[self.currency_pair_secondery[0]]["a"], self.param[self.currency_pair_secondery[0]]["b"],
            #        balance["Current"] - 1000, sum(profit), max(profit_percents), sum(loss), max(loss_percents),
            #        profit_factor, len(profit) / sell_count, len(loss) / sell_count, sell_count,
            #        (balance["Current"] - 1000) / sell_count, max(profit_count), sum(profit_count) / len(profit_count),
            #        max(loss_count), sum(loss_count) / len(loss_count), 0, 0]
        except ZeroDivisionError:
            row = ["Algorithm_2", self.param[self.currency_pair_secondery[0]]["Win1"],
                   self.param[self.currency_pair_secondery[0]]["Win2"],
                   self.param[self.currency_pair_secondery[0]]["Win3"], self.param[self.currency_pair_secondery[0]]["t"],
                   self.param[self.currency_pair_secondery[0]]["a"], self.param[self.currency_pair_secondery[0]]["b"],
                   balance["Current"] - 1000, sum(profit), max(profit_percents), sum(loss),
                          max(loss_percents), profit_factor, 0, 0, sell_count, 0, 0, 0,
                          max(loss_count), 0, 0, 0]

        self.result_row.append(row)
        # print(row)

class Algorithm_5(Algorithm_3):

    def SetAlgorithmParam(self, currency_pair, window1, window2, window3, t, a, b):
        p = {"Win1": window1, "Win2": window2, "Win3": window3, "t": t, "a": a, "b": b}
        self.param[currency_pair] = p

    def CreateThread(self):
        self.th_sec = {}
        try:
            for i in self.currency_pair:
                self.th_sec[i] = threading.Thread(target=self.SecondThread, args=(self.param[i], i,))
                self.th_sec[i].start()
            time.sleep(1)
            self.th_main = threading.Thread(target=self.MainThread, args=(self.param[0],))
            self.th_main.start()
        except:
            print("Error: unable to start thread")

    def RunAlgorithm(self):
        fieldnames = ['Strategy', 'Win1', 'Win2', 'Win3', 'T', 'A', 'B', 'Total Net Profit',
                      'Gross Profit', 'Max Profit', 'Gross Loss', 'Max Loss', 'Profit Factor',
                      'Profit Trade (%)', 'Loss Trade (%)', 'Total Trade', 'Expected Payoff', 'Max Consecutive Wins',
                      'Avg Consecutive Wins', 'Max Consecutive Loss', 'Avg Consecutive Loss',
                      'Max Draw Down (%)', 'Max Draw Down (Time)']
        for win1 in self.window1:
            for win2 in self.window2:
                for win3 in self.window3:
                    for t in self.t:
                        print(win1, " ", win2, " ", win3, " ", t, " ")
                        for a in self.a:
                            for b in self.b:
                                # for i in self.currency_pair:
                                #     self.param[i] = {"Win1": win1, "Win2": win2, "Win3": win3, "t": t, "a": a, "b": b}
                                self.CreateThread()
                                time.sleep(10)
                                self.th_main.join()
                                for i in self.currency_pair:
                                    self.th_sec[i].join()
        self.WriteResult(fieldnames, self.result_row)




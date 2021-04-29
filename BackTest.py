import threading
from datetime import datetime
import time

import numpy
import pandas as pd

from binance.client import Client
from Algorithm import OfflineAlgorithm
from Strategy import ICHIMOKU_2_Strategy
from IO import CSVFiles, FileWorking


class Algorithm_1(OfflineAlgorithm):

    def __init__(self, candle):
        # self.window1 = [9, 18, 24, 36]
        # self.window2 = [24, 48, 72]
        # self.window3_ = [48, 96, 144]
        # self.t = [18, 26, 48]
        # self.a = [0, 0.01]
        # self.b = [0.04, 0.05, 0.06]
        # self.SL_arr = [0.025, 0.05]
        # self.RR_arr = [1, 1.5, 2, 2.5, 3]

        self.window1 = [36]
        self.window2 = [48]
        self.window3_ = [144]
        self.t = [18]
        self.a = [0]
        self.b = [0.04]
        self.SL_arr = [0.025, 0.05]
        self.RR_arr = [1, 1.5, 2, 2.5, 3]

        global klines
        use_offline_data = True
        if use_offline_data:
            klines = FileWorking.ReadKlines("Data\\BTCUSDT_1HOUR_1.1.2020_1.1.2021.txt")
        else:
            klines = candle.getKlines("BNBUSDT", Client.KLINE_INTERVAL_1HOUR, "1 Jan, 2018", "1 Jan, 2020")
            FileWorking.WriteKlines(klines, "Data\\BNBUSDT_1HOUR_1.1.2018_1.1.2020.txt")
        candle.unpackCandle(klines)
        high = pd.Series(candle.high)
        low = pd.Series(candle.low)

        self.klines = klines
        self.close_data = candle.close

        self.ichi_2_strategy = ICHIMOKU_2_Strategy(high, low, self.close_data)

        self.file = CSVFiles("Strategy_2-WithoutSL-2020_2021-BTCUSDT_1.csv")

    def BuyStrategy(self, i, win1, win2, win3, t, a, b, computeIndicator):
        if computeIndicator:
            self.ichi_2_strategy.ComputeIchimoku_A(win1, win2)
            self.ichi_2_strategy.ComputeIchimoku_B(win2, win3)
            self.ichi_2_strategy.ComputeIchimoku_Base_Line(win1, win2)
            self.ichi_2_strategy.ComputeIchimoku_Conversion_Line(win1, win2)
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
                                        print("Order ", profit_count + loss_count, " Buy_Price = ", buy_price,
                                              "Date = ", order_time)
                                        i += 1
                                        volume = 1000
                                    if not isNotPos:
                                        if self.ichi_2_strategy.SellStrategy(i, t):# or\
                                        #     ((buy_price - self.close_data[i]) / buy_price) > SL:
                                            if self.close_data[i] - buy_price < 0:
                                                loss += ((buy_price - self.close_data[i]) / buy_price) * volume
                                                loss_arr.append(((buy_price - self.close_data[i]) / buy_price) * volume)
                                                balance -= ((buy_price - self.close_data[i]) / buy_price) * volume
                                                balance_arr.append(balance)
                                                print("(Loss) Balance = ", balance, "Date = ",  datetime.utcfromtimestamp(self.klines[i][0] / 1000),
                                                      "Sell Price = ", self.close_data[i] , "Max Price = ", max_price,
                                                      "Missing Profit = ",(max_price - self.close_data[i]) / max_price)
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
                                                print("(Profit) Balance = ", balance, "Date = ",  datetime.utcfromtimestamp(self.klines[i][0] / 1000),
                                                      "Sell Price = ", self.close_data[i] , "Max Price = ", max_price,
                                                      "Missing Profit = ",(max_price - self.close_data[i]) / max_price)
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
        self.SL_arr = [0.025, 0.05]

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

        self.file = CSVFiles("Strategy_2-2020_2021-ETHBTC.csv")
        self.result_row = []

    def CreateThread(self, main_param, second_param):
        try:
            self.th_sec = threading.Thread(target=self.SecondThread, args=(second_param,))
            self.th_sec.start()
            time.sleep(1)
            self.th_main = threading.Thread(target=self.MainThread, args=(main_param,))
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

    def MainThread(self, param):
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
                    # print("Order ", profit_count + loss_count, " Buy_Price_EU = ", buy_price_EU,
                    #       "Date = ", klines[i][0])
                else:
                    buy_price[self.currency[0]] = self.ichi_2_strategy[0].close_data[i]
                    isNotPos[self.currency[0]] = False
                    # print("Order ", profit_count + loss_count, " Buy_Price_BU = ", buy_price_BU,
                    #       "Date = ", klines[i][0])
                # print("Win1=", win1, " Win2=", win2, "T=", t, " Win3=", win3)
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
                        # print("(Loss) Balance = ", balance, "Sell_Price_EU = ", close_arr_EU[i], "Date = ", klines[i][0],
                        #       "ETH_Loss = ", (buy_price_EU - close_arr_EU[i]) / buy_price_EU)
                        loss_count += 1
                        profit_count_arr.append(profit_count)
                        profit_count = 0
                        if balance_dict["Min"] > balance_dict["Current"]:
                            balance_dict["Min"] = balance_dict["Current"]
                            Max_DD_arr[-1] = ((balance_dict["Max"] - balance_dict["Min"]) / balance_dict["Max"])
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
                        # print("(Profit) Balance = ", balance, "Sell_Price_EU = ", close_arr_EU[i],  "Date = ", klines[i][0],
                        #       "ETH_Profit = ", (close_arr_EU[i] - buy_price_EU) / buy_price_EU)
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
                        # print("Volume = ", volume, "Sell_Price_EU = ", close_arr_EU[i], "Buy_Price_BU = ", close_arr_BU[i],
                        #       "Date = ", klines[i][0], "ETH_Loss = ", (buy_price_EU - close_arr_EU[i]) / buy_price_EU,
                        #       "ETH Missing Profit = ", (ETH_max_price - close_arr_EB[i]) / ETH_max_price)
                    else:
                        secondery_profit.append((self.ichi_2_strategy[1].close_data[i] - buy_price[self.currency[1]]) /
                                                buy_price[self.currency[1]])
                        # print("Volume = ", volume, "Sell_Price_EU = ", close_arr_EU[i], "Buy_Price_BU = ", close_arr_BU[i],
                        #       "Date = ", klines[i][0], "ETH_Profit = ", (close_arr_EU[i] - buy_price_EU) / buy_price_EU,
                        #       "ETH Missing Profit = ", (ETH_max_price - close_arr_EB[i]) / ETH_max_price)
                    secondery_missing_profit.append((secondery_max_price - self.ichi_2_strategy[-1].close_data[i]) / secondery_max_price)


            elif not isNotPos[self.currency[0]]:
                if self.ichi_2_strategy[0].SellStrategy(i, param["t"]):
                    if self.ichi_2_strategy[0].close_data[i] - buy_price[self.currency[0]] < 0:
                        loss = ((buy_price[self.currency[0]] - self.ichi_2_strategy[0].close_data[i]) /
                                buy_price[self.currency[0]]) * self.volume
                        loss_arr.append(loss)
                        balance_dict["Current"] -= loss
                        balance_arr.append(balance_dict["Current"])
                        # print("(Loss) Balance = ", balance, "Sell_Price_BU = ", close_arr_BU[i], "Date = ", klines[i][0])
                        loss_count += 1
                        profit_count_arr.append(profit_count)
                        profit_count = 0
                        if balance_dict["Min"] > balance_dict["Current"]:
                            balance_dict["Min"] = balance_dict["Current"]
                            Max_DD_arr[-1] = ((balance_dict["Max"] - balance_dict["Min"]) / balance_dict["Max"])

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
                        # print("(Profit) Balance = ", balance, "Sell_Price_BU = ", close_arr_BU[i], "Date = ", klines[i][0])
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
                    # print("Volume = ", volume, "Sell_Price_BU = ", close_arr_BU[i], "Buy_Price_EU = ", close_arr_EU[i], "Date = ", klines[i][0])
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
            row = ["Algorithm_2", param["Win1"], param["Win2"], param["Win3"], param["t"], param["a"],
                          param["b"], balance_dict["Current"] - 1000, sum(profit_arr), max(profit_arr), sum(loss_arr),
                          max(loss_arr), profit_factor, len(profit_arr) / trade_count, len(loss_arr) / trade_count,
                          trade_count, (balance_dict["Current"] - 1000) / trade_count, max(profit_count_arr),
                          avg_profit, max(loss_count_arr), avg_loss, max(Max_DD_arr) * 100, 0,sum(secondery_profit),
                          sum(secondery_loss), len(secondery_profit) / (len(secondery_profit) + len(secondery_loss)),
                          len(secondery_loss) / (len(secondery_profit) + len(secondery_loss)),
                          len(secondery_profit) + len(secondery_loss), sum(secondery_missing_profit)]
        except ZeroDivisionError:
            row = ["Algorithm_2", param["Win1"], param["Win2"], param["Win3"], param["t"], param["a"],
                          param["b"], balance_dict["Current"] - 1000, sum(profit_arr), max(profit_arr), sum(loss_arr),
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
    def __init__(self, candle, currency, currency_pair):
        self.window1 = [9, 18, 24, 36]
        self.window2 = [24, 48, 72]
        self.window3 = [48, 96, 144]
        self.t = [18, 26, 48]
        self.a = [0, 0.01]
        self.b = [0.04, 0.05, 0.06]
        self.SL_arr = [0.025, 0.05]

        start_time = "1.1.2020"
        end_time = "1.1.2021"

        self.currency = currency
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

        self.file = CSVFiles("Strategy_2-2020_2021-ETHBTC.csv")
        self.result_row = []

    def CreateThread(self, main_param, second_param):
        try:
            for i in self.currency_pair:
                self.th_sec[i] = threading.Thread(target=self.SecondThread, args=(second_param, i,))
                self.th_sec[i].start()
            time.sleep(1)
            self.th_main = threading.Thread(target=self.MainThread, args=(main_param,))
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
                                self.th_main.join()
                                for i in self.currency_pair:
                                    self.th_sec[i].join()
        self.WriteResult(fieldnames, self.result_row)

    def SecondThread(self, param, currency):
        self.BuySignal[currency] = [False] * len(self.klines[currency])
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
                self.BuySignal[currency][j] = True
                isNotPos = False
            elif not isNotPos:
                if j - param["t"] - 1 > 0:
                    if self.ichi_2_strategy[currency].SellStrategy(j, param["t"]):
                        self.BuySignal[currency][j] = False
                        isNotPos = True
                    else:
                        self.BuySignal[currency][j] = True
            update_strategy = False
            j += 1

    def MainThread(self, param):
        update_strategy = True
        balance_dict = {"Current": 1000, "Max": 1000, "Min": 1000}
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
        secondery_max_price = 0
        secondery_missing_profit = []
        secondery_profit = []
        secondery_loss = []
        for i in range(1, len(self.klines[self.currency[0]]) - 1):
            if update_strategy:
                self.ichi_2_strategy[self.currency[0]].ComputeIchimoku_A(param["Win1"], param["Win2"])
                self.ichi_2_strategy[self.currency[0]].ComputeIchimoku_B(param["Win2"], param["Win3"])
                self.ichi_2_strategy[self.currency[0]].ComputeIchimoku_Base_Line(param["Win1"], param["Win2"])
                self.ichi_2_strategy[self.currency[0]].ComputeIchimoku_Conversion_Line(param["Win1"], param["Win2"])
            if self.ichi_2_strategy[self.currency[0]].BuyStrategy(i, param["t"], param["a"], param["b"])\
                    and isNotPos[self.currency[0]] and isNotPos[self.currency[1]]:
                if self.BuySignal[i]:
                    buy_price[self.currency[1]] = self.ichi_2_strategy[1].close_data[i]
                    isNotPos[self.currency[1]] = False
                    secondery_max_price = self.ichi_2_strategy[-1].close_data[i]
                    # print("Order ", profit_count + loss_count, " Buy_Price_EU = ", buy_price_EU,
                    #       "Date = ", klines[i][0])
                else:
                    buy_price[self.currency[0]] = self.ichi_2_strategy[0].close_data[i]
                    isNotPos[self.currency[0]] = False
                    # print("Order ", profit_count + loss_count, " Buy_Price_BU = ", buy_price_BU,
                    #       "Date = ", klines[i][0])
                # print("Win1=", win1, " Win2=", win2, "T=", t, " Win3=", win3)
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
                        # print("(Loss) Balance = ", balance, "Sell_Price_EU = ", close_arr_EU[i], "Date = ", klines[i][0],
                        #       "ETH_Loss = ", (buy_price_EU - close_arr_EU[i]) / buy_price_EU)
                        loss_count += 1
                        profit_count_arr.append(profit_count)
                        profit_count = 0
                        if balance_dict["Min"] > balance_dict["Current"]:
                            balance_dict["Min"] = balance_dict["Current"]
                            Max_DD_arr[-1] = ((balance_dict["Max"] - balance_dict["Min"]) / balance_dict["Max"])
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
                        # print("(Profit) Balance = ", balance, "Sell_Price_EU = ", close_arr_EU[i],  "Date = ", klines[i][0],
                        #       "ETH_Profit = ", (close_arr_EU[i] - buy_price_EU) / buy_price_EU)
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
                        # print("Volume = ", volume, "Sell_Price_EU = ", close_arr_EU[i], "Buy_Price_BU = ", close_arr_BU[i],
                        #       "Date = ", klines[i][0], "ETH_Loss = ", (buy_price_EU - close_arr_EU[i]) / buy_price_EU,
                        #       "ETH Missing Profit = ", (ETH_max_price - close_arr_EB[i]) / ETH_max_price)
                    else:
                        secondery_profit.append((self.ichi_2_strategy[1].close_data[i] - buy_price[self.currency[1]]) /
                                                buy_price[self.currency[1]])
                        # print("Volume = ", volume, "Sell_Price_EU = ", close_arr_EU[i], "Buy_Price_BU = ", close_arr_BU[i],
                        #       "Date = ", klines[i][0], "ETH_Profit = ", (close_arr_EU[i] - buy_price_EU) / buy_price_EU,
                        #       "ETH Missing Profit = ", (ETH_max_price - close_arr_EB[i]) / ETH_max_price)
                    secondery_missing_profit.append((secondery_max_price - self.ichi_2_strategy[-1].close_data[i]) / secondery_max_price)


            elif not isNotPos[self.currency[0]]:
                if self.ichi_2_strategy[0].SellStrategy(i, param["t"]):
                    if self.ichi_2_strategy[0].close_data[i] - buy_price[self.currency[0]] < 0:
                        loss = ((buy_price[self.currency[0]] - self.ichi_2_strategy[0].close_data[i]) /
                                buy_price[self.currency[0]]) * self.volume
                        loss_arr.append(loss)
                        balance_dict["Current"] -= loss
                        balance_arr.append(balance_dict["Current"])
                        # print("(Loss) Balance = ", balance, "Sell_Price_BU = ", close_arr_BU[i], "Date = ", klines[i][0])
                        loss_count += 1
                        profit_count_arr.append(profit_count)
                        profit_count = 0
                        if balance_dict["Min"] > balance_dict["Current"]:
                            balance_dict["Min"] = balance_dict["Current"]
                            Max_DD_arr[-1] = ((balance_dict["Max"] - balance_dict["Min"]) / balance_dict["Max"])

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
                        # print("(Profit) Balance = ", balance, "Sell_Price_BU = ", close_arr_BU[i], "Date = ", klines[i][0])
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
                    # print("Volume = ", volume, "Sell_Price_BU = ", close_arr_BU[i], "Buy_Price_EU = ", close_arr_EU[i], "Date = ", klines[i][0])
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
            row = ["Algorithm_2", param["Win1"], param["Win2"], param["Win3"], param["t"], param["a"],
                          param["b"], balance_dict["Current"] - 1000, sum(profit_arr), max(profit_arr), sum(loss_arr),
                          max(loss_arr), profit_factor, len(profit_arr) / trade_count, len(loss_arr) / trade_count,
                          trade_count, (balance_dict["Current"] - 1000) / trade_count, max(profit_count_arr),
                          avg_profit, max(loss_count_arr), avg_loss, max(Max_DD_arr) * 100, 0,sum(secondery_profit),
                          sum(secondery_loss), len(secondery_profit) / (len(secondery_profit) + len(secondery_loss)),
                          len(secondery_loss) / (len(secondery_profit) + len(secondery_loss)),
                          len(secondery_profit) + len(secondery_loss), sum(secondery_missing_profit)]
        except ZeroDivisionError:
            row = ["Algorithm_2", param["Win1"], param["Win2"], param["Win3"], param["t"], param["a"],
                          param["b"], balance_dict["Current"] - 1000, sum(profit_arr), max(profit_arr), sum(loss_arr),
                          max(loss_arr), profit_factor, 0, 0, trade_count, 0, max(profit_count_arr), avg_profit,
                          max(loss_count_arr), avg_loss, max(Max_DD_arr) * 100, 0, sum(secondery_profit), sum(secondery_loss),
                          0, 0, len(secondery_profit) + len(secondery_loss), sum(secondery_missing_profit)]

        self.result_row.append(row)

    def CheckAllPos(self, pos):
        for i in pos:
            if not i:
                return False
        return True




from datetime import datetime

import numpy

from Algorithm import OfflineAlgorithm
from Strategy import ICHIMOKU_2_Strategy
from IO import CSVFiles

class Algorithm_1(OfflineAlgorithm):

    def __init__(self, klines, high, low, close):
        self.window1 = [9, 18, 24, 36]
        self.window2 = [24, 48, 72]
        self.window3_ = [48, 96, 144]
        self.t = [18, 26, 48]
        self.a = [0, 0.01]
        self.b = [0.04, 0.05, 0.06]
        self.SL_arr = [0.025, 0.05]
        self.RR_arr = [1, 1.5, 2, 2.5, 3]

        self.klines = klines
        self.close_data = close

        self.ichi_2_strategy = ICHIMOKU_2_Strategy(high, low, close)

        self.file = CSVFiles("Strategy_2-SL-2020_2021-BNB.csv")

    def CheckStrategy(self, i, win1, win2, win3, t, a, b, computeIndicator):
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
        fieldnames = ['Strategy', 'Win1', 'Win2', 'Win3', 'T', 'A', 'B', 'SL', 'Total Net Profit',
                      'Gross Profit', 'Max Profit', 'Gross Loss', 'Max Loss', 'Profit Factor',
                      'Profit Trade (%)', 'Loss Trade (%)', 'Total Trade', 'Expected Payoff', 'Max Consecutive Wins',
                      'Avg Consecutive Wins', 'Max Consecutive Loss', 'Avg Consecutive Loss',
                      'Max Draw Down (%)']
        rows = []
        for win1 in self.window1:
            for win2 in self.window2:
                for win3 in self.window3_:
                    for t in self.t:
                        print(win1, " ", win2, " ", win3, " ", t, " ")
                        for a in self.a:
                            for b in self.b:
                                for SL in self.SL_arr:
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
                                    for i in range(1, len(self.klines) - 1):
                                        if self.CheckStrategy(i, win1, win2, win3, t, a, b, ICHIMOKU_fill) and isNotPos:
                                            isNotPos = False
                                            buy_price = self.close_data[i]
                                            order_time = datetime.utcfromtimestamp(self.klines[i][0] / 1000)
                                            # print("Win1=", win1, " Win2=", win2, "T=", t, " Win3=", win3)
                                            # print("Order ", profit_count + loss_count, " Buy_Price = ", buy_price,
                                            #       "Date = ", order_time)
                                            i += 1
                                            volume = balance
                                        if not isNotPos:
                                            if self.ichi_2_strategy.SellStrategy(i, t) or\
                                                ((buy_price - self.close_data[i]) / buy_price) > SL:
                                                if self.close_data[i] - buy_price < 0:
                                                    loss += ((buy_price - self.close_data[i]) / buy_price) * volume
                                                    loss_arr.append(((buy_price - self.close_data[i]) / buy_price) * volume)
                                                    balance -= ((buy_price - self.close_data[i]) / buy_price) * volume
                                                    balance_arr.append(balance)
                                                    # print("(Loss) Balance = ", balance, "Date = ",  datetime.utcfromtimestamp(self.klines[i][0] / 1000))
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
                                                    # print("(Profit) Balance = ", balance, "Date = ",  datetime.utcfromtimestamp(self.klines[i][0] / 1000))
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
                                                    # writer.writerow({'Order': profit_count + loss_count, 'Price': buy_price,
                                                    #                  'Time': order_time, 'Sell Time': klines[i][0],
                                                    #                  'Loss/Profit': "Profit", 'Sell Price': close_arr[i],
                                                    #                  'Volume': volume})
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
                                        row = ["ICHIMOKU_Strategy", str(win1), str(win2), str(win3), t, a, b, SL,
                                               balance - 1000, profit, numpy.max(profit_arr), loss, numpy.max(loss_arr),
                                               profit_factor, profit_count / trade_count, loss_count / trade_count, trade_count,
                                               (balance - 1000) / trade_count, max_profit_count, avg_profit, max_loss_count,
                                               avg_loss, numpy.max(Max_DD_arr) * 100]
                                        rows.append(row)
                                    except ZeroDivisionError:
                                        row_zero_division = ["ICHIMOKU_Strategy", str(win1), str(win2), str(win3), t,
                                                             a, b, SL, balance - 1000, profit, numpy.max(profit_arr), loss,
                                                             numpy.max(loss_arr), profit_factor, 0, 0, trade_count, 0,
                                                             max_profit_count, avg_profit, max_loss_count, avg_loss,
                                                             numpy.max(Max_DD_arr) * 100]
                                        rows.append(row_zero_division)
        self.WriteResult(fieldnames, rows)

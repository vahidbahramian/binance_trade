from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceWithdrawException
from binance.enums import *
import talib
import numpy
from datetime import datetime
from enum import Enum
import csv
import matplotlib.pyplot as plt

from Connect import Connect
from Candles import Candles
from OnlineTrade import Trade
import Strategy


def main(client):
    """

    :type client: type of binance client
    """
    # order = client.create_order(
    #     symbol='BNBBTC',
    #     side=SIDE_BUY,
    #     type=ORDER_TYPE_STOP_LOSS,
    #     timeInForce=TIME_IN_FORCE_GTC,
    #     quantity=100,
    #     price='0.00001')
    # # get market depth
    candle = Candles(client)
    trade = Trade(client)
    trade.RunTradeThread()
    # klines = candle.getCandle("ETHBTC", Client.KLINE_INTERVAL_1HOUR, "1 Aug, 2018", "1 Aug, 2019")
    # candle.unpackCandle(klines)
    # candle_close = candle.getClose()
    # candle_open = candle.getOpen()
    # candle_high = candle.getHigh()
    # candle_low = candle.getLow()
    # candle_volume = candle.getVolume()
    #
    # ema_strategy = Strategy.EMA_Strategy(candle_close)
    # ema_stocastic_strategy = Strategy.EMA_Stocastic_Strategy(candle_high, candle_low, candle_close)
    #
    # isNotPos = True
    # e1_arr = [5, 6, 7, 8, 9, 10]
    # e2_arr = [20, 30, 40, 50]
    # e_st1_arr = [10, 20, 30, 40, 50, 60, 70, 80]
    # e_st2_arr = [3, 4, 5, 6, 7, 8, 9, 10]
    # SL_arr = [0.05, 0.1, 0.15, 0.2]
    # RR_arr = [1, 2, 3]
    # filename = 'data.csv'
    # with open(filename, 'w', newline='') as csvfile:
    #     fieldnames = ['Strategy', 'SL', 'RR', 'Total Net Profit', 'Gross Profit', 'Gross Loss', 'Profit Factor',
    #                   'Profit Trade (%)', 'Loss Trade (%)', 'Total Trade', 'Expected Payoff', 'Max Consecutive Wins',
    #                   'Avg Consecutive Wins', 'Max Consecutive Loss', 'Avg Consecutive Loss',
    #                   'Max Draw Down (%)', 'Max Draw Down (Time)']
    #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    #     writer.writeheader()
    #     for es1 in e_st1_arr:
    #         print(es1)
    #         for es2 in e_st2_arr:
    #             ema_stocastic_strategy.ComputeStocasticArray(es1, es2)
    #             for e1 in e1_arr:
    #                 ema_stocastic_strategy.ComputeEMAArray_1(e1)
    #                 for e2 in e2_arr:
    #                     ema_stocastic_strategy.ComputeEMAArray_2(e2)
    #                     for SL in SL_arr:
    #                         for RR in RR_arr:
    #                             balance = 1000
    #                             balance_arr = []
    #                             max_balance = balance
    #                             min_balance = balance
    #                             Max_DD_arr = [0]
    #                             profit = 0
    #                             loss = 0
    #                             profit_count = 0
    #                             loss_count = 0
    #                             temp_profit_count = 0
    #                             max_profit_count = 0
    #                             avg_profit_count = []
    #                             temp_loss_count = 0
    #                             max_loss_count = 0
    #                             avg_loss_count = []
    #                             for i in range(1, len(klines) - 1):
    #                                 if ema_stocastic_strategy.Check(i) and isNotPos:
    #                                     isNotPos = False
    #                                     buy_price = candle_close[i]
    #                                     # print("Order ", profit_count + loss_count, " Buy_Price = ",buy_price , "Date = ", klines[i][0])
    #                                     i += 1
    #                                     order = (balance * 0.01) / SL
    #                                 if not isNotPos:
    #                                     if (buy_price - candle_low[i]) / buy_price > SL:
    #                                         loss += (order * SL)
    #                                         balance -= (order * SL)
    #                                         balance_arr.append(balance)
    #                                         # print("(Loss) Balance = ", balance, "Date = ", klines[i][0])
    #                                         loss_count += 1
    #                                         temp_loss_count += 1
    #                                         if max_profit_count < temp_profit_count:
    #                                             max_profit_count = temp_profit_count
    #                                         if temp_profit_count != 0:
    #                                             avg_profit_count.append(temp_profit_count)
    #                                         temp_profit_count = 0
    #                                         if min_balance > balance:
    #                                             min_balance = balance
    #                                             Max_DD_arr[-1] = ((max_balance - min_balance) / max_balance)
    #                                         isNotPos = True
    #                                     elif (candle_high[i] - buy_price) / buy_price > SL * RR:
    #                                         profit += (order * SL * RR)
    #                                         balance += (order * SL * RR)
    #                                         balance_arr.append(balance)
    #                                         # print("(Profit) Balance = ", balance, "Date = ", klines[i][0])
    #                                         profit_count += 1
    #                                         temp_profit_count += 1
    #                                         if max_loss_count < temp_loss_count:
    #                                             max_loss_count = temp_loss_count
    #                                         if temp_loss_count != 0:
    #                                             avg_loss_count.append(temp_loss_count)
    #                                         temp_loss_count = 0
    #                                         if max_balance < balance:
    #                                             max_balance = balance
    #                                             min_balance = balance
    #                                             Max_DD_arr.append((max_balance - min_balance) / max_balance)
    #                                         isNotPos = True
    #                                 ema_fill = False
    #                             # # plt.imshow(balance)
    #                             #
    #                             # plt.plot(balance_arr)
    #                             # plt.show()
    #                             trade_count = profit_count + loss_count
    #                             if temp_profit_count != 0:
    #                                 avg_profit_count.append(temp_profit_count)
    #                             avg_profit = numpy.average(avg_profit_count)
    #                             if temp_loss_count != 0:
    #                                 avg_loss_count.append(temp_loss_count)
    #                             avg_loss = numpy.average(avg_loss_count)
    #                             # print("Total order = ", trade_count ,"SL =", SL, "RR = ", RR, "Balance = ", balance)
    #                             writer.writerow(
    #                                 {'Strategy': Strategy.EMA_Stocastic_Strategy.__name__ + "_" + str(e1) + "_" + str(e2) +
    #                                              "_" + str(es1) + "_" + str(es2), 'SL': SL, 'RR': RR,
    #                                  'Total Net Profit': balance - 1000,
    #                                  'Gross Profit': profit, 'Gross Loss': loss, 'Profit Factor': profit / loss,
    #                                  'Profit Trade (%)': profit_count / trade_count,
    #                                  'Loss Trade (%)': loss_count / trade_count,
    #                                  'Total Trade': trade_count, 'Expected Payoff': (balance - 1000) / trade_count,
    #                                  'Max Consecutive Wins': max_profit_count, 'Avg Consecutive Wins': avg_profit,
    #                                  'Max Consecutive Loss': max_loss_count, 'Avg Consecutive Loss': avg_loss,
    #                                  'Max Draw Down (%)': numpy.max(Max_DD_arr) * 100})
    # try:
    #     pass
    # except BinanceAPIException as e:
    #     print(e)
    # except BinanceWithdrawException as e:
    #     print(e)
    # else:
    #     print("Success")


if __name__ == "__main__":
    connectToBinance = Connect()
    client = connectToBinance.ConnectTo
    main(client)

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceWithdrawException
from binance.enums import *
import talib
import numpy
from datetime import datetime
from enum import Enum
import csv
import matplotlib.pyplot as plt

api_key = "NfjCKix0SSnVigM7dPhluUKxpFZnmd3s5bUVdfZMer4KlSZGpnMdw2815Oa5BiMR"
api_secret = "ChEyzzYY7EMtbrmKvZ3Jltfip1loihGoaT2UtGEeLHHI5bMfSNqDHPQuPq7I7Ezi"
try:
    client = Client(api_key, api_secret)
except BinanceAPIException as e:
    print(e)
except BinanceWithdrawException as e:
    print(e)
else:
    print("Success Connection")


# order = client.create_order(
#     symbol='BNBBTC',
#     side=SIDE_BUY,
#     type=ORDER_TYPE_STOP_LOSS,
#     timeInForce=TIME_IN_FORCE_GTC,
#     quantity=100,
#     price='0.00001')
# # get market depth
klines = client.get_historical_klines("ETHBTC", Client.KLINE_INTERVAL_1HOUR, "1 Aug, 2018", "1 Aug, 2019")
_close = []
_open = []
_high = []
_low = []
_volume = []
for i in range(len(klines)):
    klines[i][0] = datetime.utcfromtimestamp(klines[i][0]/1000)
    _close.append(float(klines[i][4]))
    _open.append(float(klines[i][1]))
    _high.append(float(klines[i][2]))
    _low.append(float(klines[i][3]))
    _volume.append(float(klines[i][5]))
close_arr = numpy.array(_close)
open_arr = numpy.array(_open)
high_arr = numpy.array(_high)
low_arr = numpy.array(_low)
volume_arr = numpy.array(_volume)

#rsi = talib.RSI(close_arr)
# ema_20 = talib.EMA(close_arr, timeperiod=20)
# ema_100 = talib.EMA(close_arr, timeperiod=100)
#macd, macdsignal, macdhist = talib.MACD(close_arr, fastperiod=12, slowperiod=26, signalperiod=9)
#mfi = talib.MFI(high_arr,low_arr,close_arr,volume_arr)

e1_arr = [5,10,15,20]
e2_arr = [50,60,70,80,90,100]

def ema(i,p1,p2,fill):
    global ema_1
    global ema_2
    if fill:
        ema_1 = talib.EMA(close_arr, timeperiod=p1)
        ema_2 = talib.EMA(close_arr, timeperiod=p2)
    if ema_1[i - 1] < ema_2[i - 1]:
        if ema_1[i] > ema_2[i]:
            return True

def ema_20_100_RSI_30(i):
    return True

isNotPos = True
SL_arr = [0.05, 0.1, 0.15, 0.2]
RR_arr = [1, 2, 3]
filename = 'data.csv'
with open(filename, 'w', newline='') as csvfile:
    fieldnames = ['Strategy', 'SL', 'RR', 'Total Net Profit', 'Gross Profit', 'Gross Loss', 'Profit Factor',
                  'Profit Trade (%)', 'Loss Trade (%)', 'Total Trade', 'Expected Payoff', 'Max Consecutive Wins',
                  'Avg Consecutive Wins', 'Max Draw Down (%)', 'Max Draw Down (Time)']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for e1 in e1_arr:
        for e2 in e2_arr:
            ema_fill = True
            for SL in SL_arr:
                for RR in RR_arr:
                    balance = 1000
                    balance_arr = []
                    max_balance = balance
                    min_balance = balance
                    Max_DD_arr = [0]
                    profit = 0
                    loss = 0
                    profit_count = 0
                    loss_count = 0
                    temp_profit_count = 0
                    max_profit_count = 0
                    avg_profit_count = []
                    for i in range(1,len(klines)-1):
                        if ema(i,e1,e2,ema_fill) and isNotPos:
                            isNotPos = False
                            buy_price = open_arr[i]
                            # print("Order ", count, " Buy_Price = ",buy_price , "Date = ", klines[i][0])
                            i += 1
                            order = (balance * 0.01) / SL
                        if not isNotPos:
                            if (buy_price - low_arr[i]) / buy_price > SL:
                                loss += (order * SL)
                                balance -= (order * SL)
                                balance_arr.append(balance)
                                # print("(Loss) Balance = ", balance)
                                loss_count += 1
                                if max_profit_count < temp_profit_count:
                                    max_profit_count = temp_profit_count
                                if temp_profit_count != 0:
                                    avg_profit_count.append(temp_profit_count)
                                temp_profit_count = 0
                                if min_balance > balance:
                                    min_balance = balance
                                    Max_DD_arr[-1] = ((max_balance - min_balance) / max_balance)
                                isNotPos = True
                            elif (high_arr[i] - buy_price) / buy_price > SL * RR:
                                profit += (order * SL)
                                balance += (order * SL)
                                balance_arr.append(balance)
                                # print("(Profit) Balance = ", balance)
                                profit_count += 1
                                temp_profit_count += 1
                                if max_balance < balance:
                                    max_balance = balance
                                    min_balance = balance
                                    Max_DD_arr.append((max_balance - min_balance) / max_balance)
                                isNotPos = True
                        ema_fill = False
                    # # plt.imshow(balance)
                    #
                    # plt.plot(balance_arr)
                    # plt.show()
                    trade_count = profit_count + loss_count
                    if temp_profit_count != 0:
                        avg_profit_count.append(temp_profit_count)
                    avg = numpy.average(avg_profit_count)
                    print("Total order = ", trade_count ,"SL =", SL, "RR = ", RR, "Balance = ", balance)
                    writer.writerow({'Strategy': ema.__name__+"_" + str(e1) + "_" + str(e2), 'SL': SL, 'RR': RR, 'Total Net Profit': balance - 1000,
                                     'Gross Profit': profit, 'Gross Loss': loss, 'Profit Factor': profit/loss,
                                     'Profit Trade (%)': profit_count/trade_count, 'Loss Trade (%)': loss_count/trade_count,
                                     'Total Trade': trade_count, 'Expected Payoff': (balance - 1000)/trade_count,
                                     'Max Consecutive Wins': max_profit_count, 'Avg Consecutive Wins': avg,
                                     'Max Draw Down (%)': numpy.max(Max_DD_arr) * 100})
try:
    pass
except BinanceAPIException as e:
    print(e)
except BinanceWithdrawException as e:
    print(e)
else:
    print("Success")

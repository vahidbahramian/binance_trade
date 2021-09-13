import configparser
import sys
from datetime import date

from Candles import Candles
from ExchangeFactory import ExchangeFactory
from OnlineTrade import Algo_1, Algo_2, Algo_3
import BackTest
from threading import Lock
import ast

def main(client, currency, param):
    """

    :type client: type of binance client
    """
    back_test = True

    # start_time = "1.1.2020"
    # end_time = "1.1.2021"
    # klines = (candle.getKlines("LTCUSDT", Client.KLINE_INTERVAL_1HOUR, "1 Jan, 2020", "1 Jan, 2021"))
    # FileWorking.WriteKlines(klines, "Data\\" + "LTCUSDT" + "_1HOUR_" + start_time + "_" + end_time + ".txt")
    if back_test:
        mutex = Lock()
        candle = Candles(client, mutex)
        # alg = BackTest.Algorithm_1(candle)
        # alg.RunAlgorithm()

        # currency = ["BTCUSDT", "BNBUSDT", "BNBBTC"]
        # alg = BackTest.Algorithm_2(candle, currency)
        # alg.RunAlgorithm()

        # currency = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        # currency_pair = ["ETHBTC", "BNBBTC"]
        # correspond = {}
        # for i, item in enumerate(currency_pair):
        #     correspond[item] = currency[i+1]
        # alg = BackTest.Algorithm_3(candle, currency, currency_pair, correspond)
        # alg.RunAlgorithm()

        c = {"XRP": [[date(2018, 5, 1), date(2019, 5, 1)], [date(2019, 5, 1), date(2020, 5, 1)],
                     [date(2018, 5, 1), date(2020, 5, 1)], [date(2020, 5, 1), date(2021, 5, 1)]],
             "LTC": [[date(2018, 1, 1), date(2019, 1, 1)], [date(2019, 1, 1), date(2020, 1, 1)],
                     [date(2018, 1, 1), date(2020, 1, 1)], [date(2020, 1, 1), date(2021, 1, 1)]],
             "TRX": [[date(2018, 6, 1), date(2019, 6, 1)], [date(2019, 6, 1), date(2020, 6, 1)],
                     [date(2018, 6, 1), date(2020, 6, 1)], [date(2020, 6, 1), date(2021, 6, 1)]],
             "ADA": [[date(2018, 4, 1), date(2019, 4, 1)], [date(2019, 4, 1), date(2020, 4, 1)],
                     [date(2018, 4, 1), date(2020, 4, 1)], [date(2020, 4, 1), date(2021, 4, 1)]],
             "ALGO": [[date(2019, 6, 1), date(2020, 6, 1)], [date(2020, 6, 1), date(2021, 6, 1)],
                      [date(2019, 6, 1), date(2021, 6, 1)]],
             "MATIC": [[date(2019, 4, 1), date(2020, 4, 1)], [date(2020, 4, 1), date(2021, 4, 1)],
                       [date(2019, 4, 1), date(2021, 4, 1)]]}
        for c, v in c.items():
            for i in v:
                currency = [c, "USDT"]
                start = i[0]
                stop = i[1]
                trade = BackTest.Algorithm_5(candle, currency, start, stop)
                window1 = [9, 18, 24, 36]
                window2 = [24, 48, 72]
                window3 = [48, 72, 96, 120, 144]
                t_ = [18, 26, 48]
                McGinley_period = [12, 18, 24, 30]
                keltner = [12, 18, 24]
                multi_atr = [1, 1.5, 2]
                for win1 in window1:
                    for win2 in window2:
                        if win1 < win2:
                            for win3 in window3:
                                if win2 < win3:
                                    for t in t_:
                                        print(c, " ", win1, " ", win2, " ", win3, " ", t, " ")
                                        for mc_ginley in McGinley_period:
                                            for k in keltner:
                                                for atr in multi_atr:
                                                    p = {"Win1": win1, "Win2": win2, "Win3": win3, "t": t, "a": 0,
                                                         "McGinley_Period": mc_ginley, "keltner_Window": k, "Multi_ATR": atr}
                                                    trade.SetAlgorithmParam(currency[0] + currency[1], p)
                                                    trade.Run()
                trade.LogResult()

        # currency = ["ALGO", "USDT"]
        # # trade = BackTest.Algorithm_4(candle, currency)
        # trade = BackTest.Algorithm_5(candle, currency)
        #
        # # trade.SetAlgorithmParam(currency[0] + currency[2], window1=36, window2=72, window3=144, t=26, a=0.01, b=0.06)
        # # trade.SetAlgorithmParam(currency[1] + currency[2], window1=18, window2=24, window3=48, t=26, a=0, b=0.06)
        # window1 = [9, 18, 24, 36]
        # window2 = [24, 48, 72]
        # window3 = [48, 72, 96, 120, 144]#[48, 96, 144]
        # t_ = [18, 26, 48]
        # # a_ = [0.03, 0.05, 0.07, 2]#[0, 0.01]
        # # b_ = [0.04, 0.05, 0.06]
        # # SL_arr = [0.025, 0.05]
        #
        # # window1 = [36]
        # # window2 = [48]
        # # window3 = [144]
        # # t_ = [18]
        # # a_ = [0.05]
        # # b_ = [0.05]
        # McGinley_period = [12, 18, 24, 30]
        # keltner = [12, 18, 24]
        # multi_atr = [1, 1.5, 2]
        # # tema_period = [24, 36, 48]
        # for win1 in window1:
        #     for win2 in window2:
        #         if win1 < win2:
        #             for win3 in window3:
        #                 if win2 < win3:
        #                     for t in t_:
        #                         print(win1, " ", win2, " ", win3, " ", t, " ")
        #                         # for a in a_:
        #                         for mc_ginley in McGinley_period:
        #                             for k in keltner:
        #                                 for atr in multi_atr:
        #                                     # for tema in tema_period:
        #                                     p = {"Win1": win1, "Win2": win2, "Win3": win3, "t": t, "a": 0,
        #                                          "McGinley_Period": mc_ginley, "keltner_Window": k, "Multi_ATR": atr}
        #                                     trade.SetAlgorithmParam(currency[0] + currency[1], p)
        #                                     trade.Run()
        # trade.LogResult()

        # fast_k = [12, 24, 36, 48]
        # slow_k = [24, 36, 48, 60]
        # slow_d = [6, 9, 12]
        # r_ = [-40, -50, -60]
        # r_down = [-80, -90]
        # r_up = [-10, -20, -30]
        # r_period = [12, 24, 36]
        # ema_period = [24, 46, 48, 60]
        # for f in fast_k:
        #     for s in slow_k:
        #         for si in slow_d:
        #             print(f, " ", s, " ", si, " ")
        #             # for r in r_:
        #             #     for rd in r_down:
        #             #         for ru in r_up:
        #             #             for rp in r_period:
        #             for ema in ema_period:
        #                 if f < s:
        #                     p = {"Win1": window1[0], "Win2": window2[0], "Win3": window3[0], "t": t_[0],
        #                          "a": a_[0], "b": b_[0], "Fast": f, "Slow": s, "Signal": si, "R": 0,
        #                          "R_Down": 0, "R_Up": 0, "R_Period": 0, "EMA_Period": ema, "HMA_Period": hma}
        #                     trade.SetAlgorithmParam(currency[0] + currency[1], p)
        #                     trade.Run()
        # trade.LogResult()

        # currency = ["BTC", "ETH", "BNB", "LTC", "XRP", "USDT"]
        # trade.SetAlgorithmParam("BTCUSDT", window1=36, window2=72, window3=96, t=26, a=0.01, b=0.06)
        # trade.SetAlgorithmParam("ETHUSDT", window1=9, window2=24, window3=144, t=26, a=0, b=0.05)
        # trade.SetAlgorithmParam("BNBUSDT", window1=18, window2=72, window3=96, t=26, a=0, b=0.04)
        # trade.SetAlgorithmParam("LTCUSDT", window1=18, window2=72, window3=96, t=26, a=0, b=0.04)
        # trade.SetAlgorithmParam("XRPUSDT", window1=18, window2=72, window3=96, t=26, a=0, b=0.04)
        # trade.SetAlgorithmParam("ETHBTC", window1=9, window2=24, window3=144, t=26, a=0, b=0.05)
        # trade.SetAlgorithmParam("BNBBTC", window1=18, window2=72, window3=96, t=26, a=0, b=0.04)
        # trade.SetAlgorithmParam("LTCBTC", window1=18, window2=72, window3=96, t=26, a=0, b=0.04)
        # trade.SetAlgorithmParam("XRPBTC", window1=18, window2=72, window3=96, t=26, a=0, b=0.04)
        # trade.Run()
    else:
        # bsm.start()
        # bsm.close()
        # reactor.stop()

        # btc_trade = Algo_1(client, bsm , candle, "BTC", "USDT", ignoreLastTrade=False)
        # btc_trade.SetAlgorithmParam(window1=36, window2=48, window3=144, t=18, a=0, b=0.04)
        # btc_trade.RunTradeThread()
        #
        # eth_trade = Algo_1(client, bsm ,candle, "ETH", "USDT", ignoreLastTrade=False)
        # eth_trade.SetAlgorithmParam(window1=9, window2=24, window3=96, t=26, a=0, b=0.04)
        # eth_trade.RunTradeThread()

        # currency = ["BTC", "ETH", "BNB", "USDT"]
        # trade = Algo_2(client, bsm, candle, currency)
        # trade.SetAlgorithmParam("BTCUSDT", window1=36, window2=72, window3=96, t=26, a=0.01, b=0.06)
        # trade.SetAlgorithmParam("ETHBTC", window1=9, window2=24, window3=144, t=26, a=0, b=0.05)
        # trade.SetAlgorithmParam("BNBBTC", window1=18, window2=72, window3=96, t=26, a=0, b=0.04)
        # trade.RunTradeThread()

        # currency = ["BTC", "USDT"]
        trade = Algo_3(exchange, currency)
        # p = {"Win1": 9, "Win2": 24, "Win3": 144, "t": 18, "a": 0, "McGinley_Period": 24, "keltner_Window": 24,
        #      "Multi_ATR": 2}
        trade.SetAlgorithmParam(currency[0] + currency[1], param)
        # trade.SetAlgorithmParam("ETHUSDT", p)
        # trade.SetAlgorithmParam("BNBUSDT", p)
        # trade.SetAlgorithmParam("LTCUSDT", window1=9, window2=24, window3=144, t=26, a=0.06, b=0.05)
        # trade.SetAlgorithmParam("XRPUSDT", window1=18, window2=72, window3=96, t=26, a=0.06, b=0.04)
        # trade.SetAlgorithmParam("ETHBTC", p)
        # trade.SetAlgorithmParam("BNBBTC", p)
        # trade.SetAlgorithmParam("LTCBTC", window1=9, window2=24, window3=144, t=26, a=0.06, b=0.05)
        # trade.SetAlgorithmParam("XRPBTC", window1=18, window2=72, window3=96, t=26, a=0.06, b=0.04)
        trade.RunTradeThread()

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('Config.ini')
    section = str(sys.argv[1])
    currency = ast.literal_eval(config[section]["Currency"])
    param = ast.literal_eval(config[section]["Param"])
    exchange = ExchangeFactory.Create("Binance", config[section])
    isConnect = exchange.Connect()
    if isConnect:
        main(exchange, currency, param)
    else:
        print("Can not to connect exchange!")

from datetime import datetime
import numpy


class Candles:

    def __init__(self, client, mutex):
        self.client = client
        self.klines_ready = False
        self.mutex = mutex

    def getKlines(self, currency_pair, time_frame, start_date, end_date):
        """
        :type currency_pair: string
        :param end_date: string
        :param start_date: string
        :param time_frame: KLINE_INTERVAL from binance.client
        """
        self.klines_ready = True
        self.mutex.acquire()
        historical_klines = self.client.get_historical_klines(currency_pair, time_frame, start_date, end_date)
        self.mutex.release()
        return historical_klines

    def getCandle(self, currency_pair, time_frame):
        return self.client.get_klines(symbol=currency_pair, interval=time_frame)

    def unpackCandle(self, klines):
        """

        :param klines: klines from binance.client
        """
        _timeUTC = []
        _close = []
        _open = []
        _high = []
        _low = []
        _volume = []
        for i in range(len(klines)):
            _timeUTC.append(datetime.utcfromtimestamp(klines[i][0] / 1000))
            _close.append(float(klines[i][4]))
            _open.append(float(klines[i][1]))
            _high.append(float(klines[i][2]))
            _low.append(float(klines[i][3]))
            _volume.append(float(klines[i][5]))

        self.timeUTC = _timeUTC
        self.close = numpy.array(_close)
        self.open = numpy.array(_open)
        self.high = numpy.array(_high)
        self.low = numpy.array(_low)
        self.volume = numpy.array(_volume)

    def getUTCTime(self):
        if self.timeUTC:
            return self.timeUTC

    def getClose(self):
        if self.close.any():
            return self.close

    def getOpen(self):
        if self.open.any():
            return self.open

    def getHigh(self):
        if self.high.any():
            return self.high

    def getLow(self):
        if self.low.any():
            return self.low

    def getVolume(self):
        if self.volume.any():
            return self.volume

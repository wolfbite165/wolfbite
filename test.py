from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import sys
import os.path
import backtrader as bt
import pandas as pd
import numpy as np
class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod)

    def cancel_all_order(self):
        if self.order_buy is True:
            self.cancel(self.order_buy)
            self.order_buy = None
        if self.order_sell:
            self.cancel(self.order_sell)
            self.order_sell = None
        if self.order_sell_stop:
            self.cancel(self.order_sell_stop)
            # self.order_sell_stop = None
        if self.order_buy_stop:
            self.cancel(self.order_buy_stop)
            # self.order_buy_stop = None
        if self.order_buy_trail:
            self.cancel(self.order_buy_trail)
            # self.order_buy_trail = None
        if self.order_sell_trail:
            self.cancel(self.order_sell_trail)
            # self.order_sell_trail = None

    def get_Bollinger(self):
        close_set = []
        for i in range(-self.period_long+1 , 1):
            close_set.append(self.dataclose[i])
        mean = np.mean(close_set)
        std = np.std(close_set)
        self.up_track = mean + self.dev_long * std

        close_set = []
        for i in range(-self.period_short + 1, 1):
            close_set.append(self.dataclose[i])
        mean = np.mean(close_set)
        std = np.std(close_set)
        self.down_track = mean - self.dev_short * std

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return
        sell_size = self.position.size#剩余币
        buy_size = cerebro.broker.getvalue()
        # kkk = round(buy_size / self.dataclose[0], 3)
        # print(kkk)

        # print('仓位余额%s'%sell_size)
        # print(('钱包余额%s'%buy_size))


        # Check if we are in the market
        if not self.position:
            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] > self.sma[0]:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                kkk = round(buy_size/self.dataclose[0]*0.5,3)
                print(kkk)


                self.order = self.buy(size=round(buy_size/self.dataclose[0],3))

        else:

            if self.dataclose[0] < self.sma[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell(size=sell_size)


if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.addstrategy(TestStrategy)
    cerebro.broker.setcash(1000000)
    cerebro.broker.setcommission(0.001)
    # modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    # datapath = os.path.join(modpath,'test_data/bitfinex_BTC_2016_1m.csv')

    dataframe = pd.read_csv('布林策略/hour_data/bitmex_xbtusd_hour_2018_1-12.csv', index_col=0, parse_dates=[0])
    data = bt.feeds.PandasData(dataname=dataframe)
    cerebro.adddata(data)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.run()

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.plot()
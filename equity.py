from time import sleep
from upstox_api import api as upstox
from datetime import datetime, timedelta
from itertools import groupby
from logging import DEBUG
from utils import BUY, SELL,create_logger, ts_to_datetime
from collections import namedtuple
from indicators import ema
from eqbot import EqBot

N50_SYMBOL = 'reliance'
LOT_SIZE = 1

SLOW_EMA = 21
FAST_EMA = 5

MAX_CYCLES = 2


Crossover = namedtuple('Crossover', ['direction', 'date', 'instrument'])


class EQUITY:
    def __init__(self, debug=False):
        if debug:
            self.logger = create_logger(self.__class__.__name__,
                                        console=True, level=DEBUG)
        else:
            self.logger = create_logger(self.__class__.__name__, console=False)

        self.state = []
        self.cycles = 0
        self.buy_bot = EqBot()
        #self.sell_bot = EqBot()
        #self.symbol = N50_SYMBOL
        #self.sym_bot = EqBot()
        self.buy_symbol = N50_SYMBOL

        self.logger.debug('')
        self.logger.debug('Initialised class')

    def setup(self, client=None):
        tod = datetime.today()
        # fromdt = (tod - timedelta(days= 6)).date() #changed to 7 days
        # todt = (tod - timedelta(days=0)).date()
        # nifty = client.get_instrument_by_symbol('NSE_EQ', N50_SYMBOL)
        # ohlc_arr = self._get_ohlc(client, nifty, fromdt, todt)
        #
        # import csv
        # with open('nifty_ohlc_sample.csv', 'w') as cfile:
        #     fields = ['timestamp', 'open', 'high', 'low', 'close']
        #     writer = csv.DictWriter(cfile, fieldnames=fields)
        #     writer.writeheader()
        #     for ohlc in ohlc_arr:
        #         row = {'timestamp': ts_to_datetime(ohlc['timestamp']).strftime('%d-%m-%Y'),
        #                'open': ohlc['open'],
        #                'high': ohlc['high'],
        #                'low': ohlc['low'],
        #                'close': ohlc['close']}
        #         writer.writerow(row)
        #
        # for i, ohlc in enumerate(ohlc_arr):
        #     if i <= SLOW_EMA + 1:
        #         continue
        #     ema_3 = []
        #     ema_5 = []
        #     ema_3 = (ema(ohlc_arr[i - FAST_EMA - 2:i - 1], n=FAST_EMA, seed=None),
        #              ema(ohlc_arr[i - FAST_EMA - 1:i], n=FAST_EMA, seed=None))
        #     ema_5 = (ema(ohlc_arr[i - SLOW_EMA - 2:i - 1:], n=SLOW_EMA, seed=None),
        #              ema(ohlc_arr[i - SLOW_EMA - 1:i], n=SLOW_EMA, seed=None))
        #     cross = self._check_crossover(ema_3, ema_5)
        #     if cross is not None:
        #         d = ts_to_datetime(ohlc['timestamp'])#.date()
        #         self.logger.debug('Crossover on %s. Direction = %s' %
        #                           (d.strftime('%d-%m-%Y,%H:%M:%S'), cross))
        #         self.logger.debug('3 EMAs = %.2f | %.2f' % (ema_3[0], ema_3[1]))
        #         self.logger.debug('5 EMAs = %.2f | %.2f' % (ema_5[0], ema_5[1]))
        #         self.logger.debug('-------------------------------\n')
        sym_inst = client.get_instrument_by_symbol('NSE_EQ', self.buy_symbol)
        print(sym_inst)
        while client.subscribe(sym_inst, upstox.LiveFeedType.LTP)['success'] is not True:
            sleep(1)
        else:
            self.logger.debug('Subscribed to %s' % self.buy_symbol)
            self.logger.debug('close = %f' % sym_inst.closing_price)
            pass

        self.state.append('setup complete')
        #self.logger.debug(self.state[-1])

    def process_quote(self, quote):
        sym = quote['symbol'].lower()
        buy_order = None
        sell_order = None

        #if sym == self.symbol:
        buy_order = self.buy_bot.process_quote(quote)


        if self.state[-1] in ('setup complete') and self.cycles < MAX_CYCLES:
            if buy_order is not None and 'sell position closed' not in self.state:
                self.state.append('buy ordered')
                return buy_order
            # elif ce_order is not None and 'ce position closed' not in self.state:
            #     self.state.append('ce ordered')
            #     return ce_order
        elif self.cycles == MAX_CYCLES:
            self.state.append('finished trading')

    def process_order(self, order):
        sym = order['symbol'].lower()
        self.buy_bot.process_order(order)
        # if sym == self.pe_symbol:
        #     self.pe_bot.process_order(order)
        # elif sym == self.ce_symbol:
        #     self.ce_bot.process_order(order)

    def process_trade(self, trade):
        self._log_trade(trade)
        sym = trade['symbol'].lower()
        #@if sym=='RELIANCE':
        self.buy_bot.process_trade(trade)
        newstate = 'ce' + self.buy_bot.state[-1]
        # if sym == self.pe_symbol:
        #     self.pe_bot.process_trade(trade)
        #     newstate = 'pe ' + self.pe_bot.state[-1]
        # elif sym == self.ce_symbol:
        #     self.ce_bot.process_trade(trade)
        #     newstate = 'ce ' + self.pe_bot.state[-1]
        if newstate != self.state[-1]:
             self.state.append(newstate)

        if 'position closed' in self.state[-1]:
            self.cycles += 1

    def _get_ohlc(self, client, instrument, fromdt, todt):
        self.logger.debug('Retrieving daily ohlc data for period %s to %s' %
                          (fromdt.strftime('%d-%m-%Y'), todt.strftime('%d-%m-%Y')))
        data = client.get_ohlc(instrument, upstox.OHLCInterval.Minute_5, fromdt, todt) #Minute_15
        self.logger.debug('Total records  = %d' % len(data))
        data = sorted(data[:], key=lambda k: k['timestamp'])
        ohlc = [list(g)[0] for k, g in groupby(data, key=lambda k: k['timestamp'])]
        self.logger.debug('Unique records = %d' % len(ohlc))
        return ohlc

    def get_symbols(self):
        if 'setup complete' not in self.state:
            return None
        return (self.buy_symbol,"VEDL")


    def _check_crossover(self, fast_ma, slow_ma):
        if fast_ma is None or slow_ma is None:
            return None
        if len(fast_ma) < 2 or len(slow_ma) < 2:
            return None
        if fast_ma[0] < slow_ma[0] and fast_ma[1] > slow_ma[1]:
            return 'up'
        elif fast_ma[0] > slow_ma[0] and fast_ma[1] < slow_ma[1]:
            return 'down'
        else:
            return None
    def _create_symbol(self, client):
        return self.buy_symbol.lower()

    def _log_trade(self, trade_info=None):
        if trade_info is None:
            self.logger.error('Invalid trade info given to _log_trade()')
        lots = int(trade_info['quantity']) # might need to change
        sym = trade_info['symbol'].lower()
        oid = str(trade_info['order_id'])
        poid = str(trade_info['parent_order_id'])

        if trade_info['transaction_type'] == BUY:
            self.logger.info('Purchased %d lots of %s' % (lots, sym))
        else:
            self.logger.info('Sold %d lots of %s' % (lots, sym))

        if poid != 'NA':
            self.logger.info('Parent OID - %s' % poid)
        self.logger.info('Order ID - %s' % oid)


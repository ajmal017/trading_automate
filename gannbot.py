from bot import LinearBot
from upstox_api import api as upstox
from indicators import gann
from utils import BUY, SELL, round_off
from datetime import datetime

DEFAULTS = {'buy': 4, 'target': -1, 'stoploss': 5}
LOT_SIZE = 75


class GannBot(LinearBot):
    def __init__(self, balance=25000, debug=False):
        super().__init__()

        self.running = False
        self.messages = None

        self.buy = 0
        self.target = 0
        self.stoploss = 0
        self.prev_ltp = 0

        self.balance = balance
        self.state = []
        self.holdings = 0
        self.uptrend = True
        self.instrument = None

        self.oid = None
        self.poid = None

        self.state.append('Initialised')

    def process_quote(self, quote):
        ltp = quote['ltp']
        act = None
        if 'setup complete' not in self.state:
            self._setup(quote)
            return act

        if ltp > self.buy + ltp * 0.01:
            self.uptrend = False
            return act

        if 'order placed' == self.state[-1]:
            return act
        elif ltp > self.buy:
            act = self._create_buy_order()
            self.state.append('order placed')
        elif ltp < self.prev_ltp:
            levels = gann(ltp)
            self.buy = levels[DEFAULTS['buy']]
            self.target = levels[DEFAULTS['target']]
            self.stoploss = gann(ltp, 'down')[DEFAULTS['stoploss']]
            self.prev_ltp = ltp
            self._print_levels()
        return act

    def process_order(self, order):
        print(order)
        #status = order['status'].lower()
        #if status == 'rejected':
        #   self.state.append('last order rejected')

    def process_trade(self, trade):
        status = str(trade['message'])
        tt = str(trade['transaction_type'])
        qty = int(trade['quantity'])
        if trade['parent_order_id'] != 'NA':
            oid = str(trade['parent_order_id'])
        else:
            oid = str(trade['order_id'])

        if status in ('completed', 'complete'):
            if tt == BUY:
                self.holdings += qty
            elif tt == SELL:
                self.holdings -= qty
                if self.holdings < 1:
                    self.status.append('position closed')
            self.poid = oid
            self.status.append('position open')

    def get_symbols(self):
        if 'setup complete' not in self.state:
            return None
        else:
            return self.instrument.symbol.lower()

    def _setup(self, ltp_quote):
        self.instrument = ltp_quote['instrument']
        ltp = ltp_quote['ltp']
        levels = gann(ltp)
        self.buy = levels[DEFAULTS['buy']]
        self.target = levels[DEFAULTS['target']]
        self.stoploss = gann(ltp, 'down')[DEFAULTS['stoploss']]
        self.prev_ltp = ltp
        self._print_levels()
        self.state.append('setup complete')

    def _create_buy_order(self):
        order = {'transaction': upstox.TransactionType.Buy,
                 'instrument': self.instrument,
                 'quantity': int(round_off(self.balance / self.buy, LOT_SIZE)),
                 'order_type': upstox.OrderType.Limit,
                 'product': upstox.ProductType.OneCancelsOther,
                 'buy_price': self.buy,
                 'stoploss': abs(self.buy - self.stoploss),
                 'target': abs(self.target - self.buy)}
        return order

    def _print_levels(self):
        print('\n--------')
        print(datetime.now().isoformat())
        print('Calculated values for %s - ' % self.instrument.symbol)
        print('\tBuy   - %f' % self.buy)
        print('\tSell  - %f' % self.target)
        print('\tSL    - %f' % self.stoploss)
        print('--------')

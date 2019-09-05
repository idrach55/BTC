import deribit_api as api
import threading
import numpy as np
import time
from datetime import datetime

def read_keys():
    return open('keys.txt', 'r').read().split('\n')[:-1]

class Future:
    def __init__(self, contract):
        self.contract = contract
        self.expiry = datetime.strptime(self.contract[4:]+'-05', '%d%b%y-%H')

    # measured in days to expiry
    def time_to_expiry(self):
        return (self.expiry - datetime.now()).total_seconds() / 60 / 60 / 24

    # cost of carry in daily compounded terms
    def implied_spot(self, future, carry, riskfree):
        T = self.time_to_expiry()
        return future/np.exp((riskfree - carry)*T/365)

    def implied_carry(self, future, spot, riskfree):
        T = self.time_to_expiry()
        return riskfree - np.log(future/spot)/(T/365)

class Book:
    def __init__(self, contract, client, depth=100):
        self.contract = contract
        self.client = client
        self.depth = depth
        self.bids = []
        self.asks = []
        self.stamp = None
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            book = self.client.getorderbook(self.contract, depth=self.depth)
            self.stamp = datetime.fromtimestamp(book['tstamp']/1e3)
            self.bids = book['bids']
            self.asks = book['asks']

    def get_top(self):
        return self.bids[0]['price'], self.asks[0]['price']

    def get_top_with_size(self):
        return self.bids[0]['price'], self.bids[0]['quantity'], \
               self.asks[0]['price'], self.asks[0]['quantity']

    def get_mid(self):
        return 0.5*(self.bids[0]['price'] + self.asks[0]['price'])

    def get_index(self, flag='btc'):
        return self.client.index()[flag]

    def get_vwap(self, size):
        if size == 0.0: return 0.0
        orders = self.asks if size > 0 else self.bids
        target = abs(size)
        basis = 0.0
        level = 0
        while target > 0:
            price, quantity = orders[level]['price'], orders[level]['quantity']
            if quantity <= target:
                basis += price*quantity
                target -= quantity
            else:
                basis += price*target
                target = 0
            level += 1
        return abs(basis/size)

class Strategy:
    def __init__(self, contract):
        self.client = api.RestClient(read_keys()[0], read_keys()[1])
        self.contract = contract
        self.book = Book(self.contract, self.client)
        #self.future = Future(contract)
        self._position = 0.0

    def position(self):
        pos = self.client.positions()
        self._position = 0.0
        if len(pos) > 0:
            for item in pos:
                if item['instrument'] == self.contract:
                    self._position = item['size']
                    break
        return self._position

    def ask(self, quantity, price, postOnly='True'):
        # price increments of 25 cents
        price = np.ceil(25*price)/25
        if quantity <= 0:
            return None
        return self.client.sell(self.contract, quantity, price, postOnly=postOnly)

    def bid(self, quantity, price, postOnly='True'):
        # price increments of 25 cents
        price = np.floor(25*price)/25
        if quantity <= 0:
            return None
        return self.client.buy(self.contract, quantity, price, postOnly=postOnly)

    def make_market_inside(self, quantity):
        best_bid, best_ask = self.book.get_top()
        self.ask(quantity, best_ask-0.01)
        self.bid(quantity, best_bid+0.01)

    def make_market_around_mid(self, quantity, spread):
        mid = self.book.get_mid()
        self.ask(quantity, mid+spread/2)
        self.bid(quantity, mid-spread/2)

class Mid(Strategy):
    def __init__(self, contract):
        Strategy.__init__(self, contract)
        self.mid = None

    def run(self, quantity, update_on_diff):
        while True:
            if self.mid is None:
                self.mid = self.book.get_mid()
                if quantity > 0: self.bid(quantity, self.mid)
                else:            self.ask(-quantity, self.mid)
            else:
                if abs(self.book.get_mid() - self.mid) > update_on_diff:
                    self.mid = self.book.get_mid()
                    self.client.cancelall()
                    if quantity > 0: self.bid(quantity, self.mid)
                    else:            self.ask(-quantity, self.mid)

example_helium_params = {'size': 100, 'width': 0.7, 'vwap': 1000, 'update': 0.5, 'thresh': 0.20}
class Helium(Strategy):
    def __init__(self, contract, params):
        Strategy.__init__(self, contract)
        self.params = params
        self.market = (None, None)

    def run(self):
        while True:
            time.sleep(self.params['update'])
            vwap_bid = self.book.get_vwap(-self.params['vwap'])
            vwap_ask = self.book.get_vwap(self.params['vwap'])
            spread = 4.00 #(vwap_ask - vwap_bid)*self.params['width']
            #mid = self.book.get_mid()
            mid = (vwap_bid + vwap_ask)/2
            my_bid = mid - spread/2
            my_ask = mid + spread/2
            positions = [pos for pos in self.client.positions() if pos['instrument'] == self.contract]
            inventory = 0
            if len(positions) > 0:
                inventory = positions[0]['size'] if positions[0]['direction'] == 'buy' else -positions[0]['size']
            ask_size = self.params['size'] if inventory >= 100 else self.params['size'] + (inventory-100)
            bid_size = self.params['size'] if inventory <= 100 else self.params['size'] - (inventory-100)
            if ask_size < 100:
                my_ask += 1.00
            if bid_size < 100:
                my_bid -= 1.00
            print('vwap mid: %0.1f, top mid: %0.1f, inventory: %d, market: (%d) %0.1f | %0.1f (%d)' \
                  %(mid,self.book.get_mid(), inventory, bid_size, my_bid, my_ask, ask_size))
            if self.market != (None, None):
                if abs(my_bid - self.market[0]) < self.params['thresh'] and abs(my_ask - self.market[1]) < self.params['thresh']:
                    continue
            self.client.cancelall()
            self.ask(ask_size, my_ask)
            self.bid(bid_size, my_bid)
            self.market = (my_bid, my_ask)

class TestBook(Strategy):
    def __init__(self, contract):
        Strategy.__init__(self, contract)

    def display(self):
        while True:
            bidPrice, bidSize, askPrice, askSize = self.book.get_top_with_size()
            print('(%d) %0.1f | %0.1f (%d)      '%(bidSize, bidPrice, askPrice, askSize),end='\r')

class Arber:
    def __init__(self, threshold=10.0, max_trade=100):
        self.A = Strategy('BTC-PERPETUAL')
        self.B = Strategy('BTC-29MAR19')

        self.threshold = threshold
        self.max_trade = max_trade

    def scan(self, trade=False):
        bid_A, bsize_A, ask_A, asize_A = self.A.book.get_top_with_size()
        bid_B, bsize_B, ask_B, asize_B = self.B.book.get_top_with_size()

        long_A_short_B = bid_B - ask_A
        long_B_short_A = bid_A - ask_B

        if long_A_short_B >= self.threshold:
            size = min(min(bsize_B, asize_A), self.max_trade)
            print("buy %d A, sell %d B, collect %0.1f"%(size,size,long_A_short_B))

            if trade:
                self.A.bid(size, ask_A)
                self.B.ask(size, bid_B)
        elif long_B_short_A >= self.threshold:
            size = min(min(bsize_A, asize_B), self.max_trade)
            print("buy %d B, sell %d A, collect %0.1f"%(size,size,long_B_short_A))

            if trade:
                self.A.ask(size, bid_A)
                self.B.bid(size, ask_B)
        else:
            return False
        return True

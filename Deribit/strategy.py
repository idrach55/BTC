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

class TestBook(Strategy):
    def __init__(self, contract):
        Strategy.__init__(self, contract)

    def display(self):
        while True:
            bidPrice, bidSize, askPrice, askSize = self.book.get_top_with_size()
            print('(%d) %0.1f | %0.1f (%d)      '%(bidSize, bidPrice, askPrice, askSize),end='\r')

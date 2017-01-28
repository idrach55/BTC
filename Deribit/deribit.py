import requests
import threading
import time
import math
import base64

from hashlib import sha256
from collections import namedtuple


Entry = namedtuple('Entry', ['price', 'size'])
Order = namedtuple('Order', ['oid', 'side', 'price', 'size'])


class RESTError(Exception):
    pass


class RESTProtocol():
    def __init__(self):
        self.keys = open('keys.txt').read().split('\n')

    def _call(self, action, params):
        nonce = int(time.time() * 1000)
        data = '_=%s&_ackey=%s&_acsec=%s&_action=%s' % (nonce, self.keys[0], self.keys[1], action)
        if params is not None:
            for key in sorted(params.keys()):
                data += '&' + key + '=' + str(params[key])
        hashed = base64.b64encode(sha256(data.encode()).digest())
        signature = '%s.%s.%s' % (self.keys[0], nonce, hashed.decode())
        return requests.get('https://www.deribit.com'+action, params=params, headers={'x-deribit-sig': signature})

    def buy(self, instrument, size, price):
        params = {'instrument': instrument, 'price': price, 'quantity': size, 'post_only': 'true'}
        resp = self._call('/api/v1/private/buy', params).json()
        if resp['success']:
            result = resp['result']['order']
            return Order(result['orderId'], result['direction'], result['price'], result['quantity'])
        else:
            raise RESTError()

    def sell(self, instrument, size, price):
        params = {'instrument': instrument, 'price': price, 'quantity': size, 'post_only': 'true'}
        resp = self._call('/api/v1/private/sell', params).json()
        if resp['success']:
            result = resp['result']['order']
            return Order(result['orderId'], result['direction'], result['price'], result['quantity'])
        else:
            raise RESTError()

    def cancel(self, oid):
        params = {'orderId': oid}
        resp = self._call('/api/v1/private/cancel', params).json()
        if resp['success']:
            if resp.get('order') is not None:
                return True
            else:
                return False
        else:
            raise RESTError()

    def cancelall(self, asset='futures'):
        params = {'type': asset}
        resp = self._call('/api/v1/private/cancelall', params).json()
        if resp['success']:
            return True
        else:
            raise RESTError()


class Book(object):
    def __init__(self, instrument):
        self.instrument = instrument
        self.bids = []
        self.asks = []

        thread = threading.Thread(target=self._subscribe, args=())
        thread.daemon = True
        thread.start()

    def _subscribe(self):
        while True:
            r = requests.get('https://www.deribit.com/api/v1/public/getorderbook', params={'instrument': self.instrument})
            book = r.json()['result']
            self.bids = book['bids']
            self.asks = book['asks']
            time.sleep(0.1)

    def get_top(self):
        bid = Entry(self.bids[0]['price'], self.bids[0]['quantity'])
        ask = Entry(self.asks[0]['price'], self.asks[0]['quantity'])
        return bid, ask

    def get_spread(self):
        bid, ask = self.get_top()
        return round(ask.price - bid.price, 2)


class Arber:
    def __init__(self, instrument):
        self.instrument = instrument
        self.book = Book(self.instrument)
        self.protocol = RESTProtocol()
        self.params = {'spread': 0.85,
                       'size':   100}

        self.open_orders = []

    def buy(self, size, price):
        try:
            order = self.protocol.buy(self.instrument, size, price).json()
            self.open_orders.append(order)
        except RESTError as e:
            pass

    def sell(self, size, price):
        try:
            order = self.protocol.sell(self.instrument, size, price).json()
            self.open_orders.append(order)
        except RESTError as e:
            pass

    def print_top(self):
        bid, ask = self.book.get_top()
        print('(%d) %0.2f | %0.2f (%d)' % (bid.size, bid.price, ask.price, ask.size))

    def market(self):
        bid, ask = self.book.get_top()
        mid = 0.5 * (bid.price + ask.price)
        spread = self.params['spread'] * (ask.price - bid.price)

        my_bid = math.floor(100*(mid - spread/2))/100
        my_ask = math.ceil(100*(mid + spread/2))/100

        my_bid = Order(my_bid, self.params['size'])
        my_ask = Order(my_ask, self.params['size'])
        return my_bid, my_ask

import requests
import threading
import time
import math
import base64

from hashlib import sha256
from collections import namedtuple

public = 'https://www.deribit.com/api/v1/public'
private = 'https://deribit.com/api/v1/private'

Order = namedtuple('Order', ['price', 'size'])

class RESTProtocol():
    def __init__(self):
        self.keys = open('keys.txt').read().split('\n')

    def buy(self, size, price):
        instrument = 'BTC-31MAR17'
        tstamp = str(int(time.time()*1e3))

        params = (tstamp, self.keys[0], self.keys[1], instrument, price, size)
        data = '_=%s&_ackey=%s&_acsec=%s&_action=/api/v1/private/buy&instrument=%s&post_only=true&price=%0.2f&quantity=%d' % params
        hashed = base64.b64encode(sha256(data.encode()).digest())
        signature = '%s.%s.%s' % (self.keys[0], tstamp, hashed.decode('ascii'))
        print(signature)
        return requests.post(private+'/buy', data={'instrument': instrument,
                                                   'post_only':  True,
                                                   'price':      '%0.2f'%price,
                                                   'quantity':   size},
                                            headers={'x-deribit-sig': signature,
                                                     'Accept':        'application/json, text/javascript, */*; q=0.01',
                                                     'Content-Type':  'application/x-www-form-urlencoded; charset=UTF-8'})

class Book(object):
    def __init__(self):
        self.bids = []
        self.asks = []

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            r = requests.get(public+'/getorderbook', params={'instrument': 'BTC-31MAR17'})
            book = r.json()['result']
            self.bids = book['bids']
            self.asks = book['asks']
            time.sleep(0.1)

    def get_top(self):
        bid = Order(self.bids[0]['price'], self.bids[0]['quantity'])
        ask = Order(self.asks[0]['price'], self.asks[0]['quantity'])
        return bid, ask

    def get_spread(self):
        bid, ask = self.get_top()
        return round(ask.price - bid.price, 2)

class Arber:
    def __init__(self):
        self.book = Book()
        self.params = {'spread': 0.85,
                       'size':   100}

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

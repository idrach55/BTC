import requests
import threading
import time
import math

from collections import namedtuple

url = 'https://deribit.com/api/v1/public'

Order = namedtuple('Order', ['price', 'size'])

class RESTProtocol():
    def __init__(self):
        self.keys = open('keys.txt').split('\n')

    def auth(self):
        tstamp = int(time.time()*1e3)
        data = ’_=%d&_ackey=29mtdvvqV56&_acsec=BP2FEOFJLFENIYFBJI7PYWGFNPZOTRCE&_action=/api/v1/private/buy&instrument=BTC-15JAN16&price=500&quantity=1’
        signature = ’29mtdvvqV56.1452237485895.0nkPWTDunuuc220vojSTirSj8/2eGT8Wv30YeLj+i4c=’

class Book(object):
    def __init__(self):
        self.bids = []
        self.asks = []

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            r = requests.get(url+'/getorderbook', params={'instrument': 'BTC-3FEB17'})
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
        return ask.price - bid.price

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

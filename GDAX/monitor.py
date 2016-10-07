from autobahn.twisted.websocket import WebSocketClientFactory, connectWS
from twisted.python import log
from twisted.internet import reactor
from pprint import pprint

from blobprotocol import BlobProtocol
from book import Book, BookClient, Order

import sys
import os
import math
import time
import pandas


class Monitor(BookClient):
    def __init__(self, side, price):
        self.order = Order(None, side, price, None)

    def add(self, oid, side, price, size):
        pass

    def change(self, oid, side, newsize):
        pass

    def match(self, oid, side, price, size):
        if self.order is None:
            return
        if (self.order.side == 'buy' and price <= self.order.price) or (self.order.side == 'sell' and price >= self.order.price):
            os.system('say %s at %0.2f' % ('bought' if self.order.side == 'buy' else 'sold', self.order.price))
            self.order = None

    def done(self, oid):
        pass


if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')
    factory.protocol = BlobProtocol

    mon = Monitor(sys.argv[1], float(sys.argv[2]))
    bb = Book(factory.protocol, debug=False)
    bb.add_client(mon)

    connectWS(factory)
    reactor.run()

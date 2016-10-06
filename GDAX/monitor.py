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
    def __init__(self):
        self.waiting_on = []

    def add(self, oid, side, price, size):
        pass

    def change(self, oid, side, newsize):
        pass

    def match(self, oid, side, price, size):
        for order in self.waiting_on:
            if order.price == price:
                os.system('say %s at %0.2f' % ('bought' if order.side == 'buy' else 'sold', order.price))
                self.waiting_on.remove(order)

    def done(self, oid):
        pass

    def loop(self):
        info = input('> ').split(' ')
        self.waiting_on.append(Order(None, info[0], float(info[1]), None))
        reactor.callLater(1.0, self.loop)


if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')
    factory.protocol = BlobProtocol

    mon = Monitor()
    bb = Book(factory.protocol, debug=False)
    bb.add_client(mon)

    connectWS(factory)

    reactor.callLater(1.0, mon.loop)
    reactor.run()

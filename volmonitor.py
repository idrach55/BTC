from autobahn.twisted.websocket import WebSocketClientFactory, connectWS
from twisted.python import log
from twisted.internet import reactor
from pprint import pprint

from blobprotocol import BlobProtocol
from book import Book, BookClient

import sys
import math
import time
import pandas


# This records the std. deviation of the midpoint change every delta seconds.  
# Namely, if dS = (sigma)dW, then this estimates sigma.
class VolMonitor(BookClient):
    def __init__(self, delta, debug=False):
        self.delta = delta
        self.debug = debug
        self.mids = []

    def add(self, oid, side, price, size):
        pass

    def change(self, oid, side, newsize):
        pass

    def match(self, oid, side, price, size):
        pass

    def done(self, oid):
        pass
        
    def generate_stamp(self):
        mid = self.book.get_mid()
        self.mids.append(mid)
        if self.debug:
            pprint('volatility: %0.4f' % self.get_hourly_volatility())
        reactor.callLater(self.delta, self.generate_stamp)

    def get_hourly_volatility(self):
        series = pandas.Series(self.mids)
        return math.sqrt(3600. / self.delta)*(series - series.shift(1)).std()

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')
    factory.protocol = BlobProtocol

    vm = VolMonitor(1.0, debug=True)
    bb = Book(factory.protocol, debug=False)
    bb.addClient(vm)

    connectWS(factory)

    reactor.callLater(1.0, vm.generate_stamp)
    reactor.run()
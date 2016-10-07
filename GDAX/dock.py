from autobahn.twisted.websocket import WebSocketClientFactory, connectWS
from twisted.python import log
from twisted.internet import reactor
from blobprotocol import BlobProtocol
from pprint import pprint
from strategy import RESTProtocol, Strategy, read_keys
from book import Book
from datetime import datetime

import pandas as pd
import sys
import numpy as np


class Dock(Strategy):
    def __init__(self, rest):
        Strategy.__init__(self, rest)

        self.initial_marking = 0.

    # Main update loop.
    def update(self):
        pass

    def loop(self):
        if not self.enabled:
            self.enabled = True
            success, usd, btc = self.rest.get_balances()
            if success:
                self.initial_marking = usd + btc*self.book.get_mid()
        success, usd, btc = self.rest.get_balances()
        if success:
            m2m = usd + btc*self.book.get_mid()
            pnl = m2m - self.initial_marking
            pprint("profit/loss: $ %0.4f" % pnl)
        reactor.callLater(5.0, self.loop)

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')
    factory.protocol = BlobProtocol

    rest = RESTProtocol(read_keys('keys.txt'), debug=True)
    dock = Dock(rest)
    dock.enabled = False

    bb = Book(factory.protocol, debug=False)
    bb.add_client(dock)

    connectWS(factory)
    reactor.callLater(5.0, dock.loop)
    reactor.run()

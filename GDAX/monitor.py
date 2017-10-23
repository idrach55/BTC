from autobahn.twisted.websocket import connectWS
from twisted.python import log
from twisted.internet import reactor
from blobprotocol import BlobProtocol, BlobProtocolFactory
from pprint import pprint
from book import Book, BookClient
from datetime import datetime

import pandas as pd
import sys
import numpy as np
import scipy.stats as dists


class Monitor(BookClient):
    def __init__(self):
        BookClient.__init__(self)
        self.initialized = False
        self.book = None

    def add(self, oid, side, price, size, product_id):
        self.update()

    def change(self, oid, side, newsize, product_id):
        self.update()

    def match(self, oid, side, price, size, product_id):
        self.update()

    def done(self, oid, product_id):
        self.update()

    def on_sequence_gap(self):
        pass

    def update(self):
        if not self.initialized:
            mid = self.book.get_mid()
            if mid is not None:
                self.initialized = True
        if not self.initialized:
            return

        up = self.book.get_best_ask()
        dn = self.book.get_best_bid()
        pprint("%0.2f @ %0.2f" % (dn, up))

if __name__ == '__main__':
    log.startLogging(sys.stdout)

    mon = Monitor()
    factory = BlobProtocolFactory('wss://ws-feed.gdax.com', product_ids=['ETH-USD'])
    factory.protocol = BlobProtocol
    bb = Book(factory.protocol, 'ETH-USD', debug=False)
    bb.add_client(mon)
    mon.book = bb

    connectWS(factory)
    reactor.run()

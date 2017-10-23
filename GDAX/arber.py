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


class Arber(BookClient):
    def __init__(self):
        self.initialized = False
        self.books = {}

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
            valid = True
            for key, book in self.books.items():
                mid = book.get_mid()
                if mid is None:
                    valid = False

            if valid:
                self.initialized = True

        if not self.initialized:
            return

        btc_usd_bid = self.books['BTC-USD'].get_best_bid()
        btc_usd_ask = self.books['BTC-USD'].get_best_ask()
        eth_btc_bid = self.books['ETH-BTC'].get_best_bid()
        eth_btc_ask = self.books['ETH-BTC'].get_best_ask()
        eth_usd_bid = self.books['ETH-USD'].get_best_bid()
        eth_usd_ask = self.books['ETH-USD'].get_best_ask()

        ltc_btc_bid = self.books['LTC-BTC'].get_best_bid()
        ltc_btc_ask = self.books['LTC-BTC'].get_best_ask()
        ltc_usd_bid = self.books['LTC-USD'].get_best_bid()
        ltc_usd_ask = self.books['LTC-USD'].get_best_ask()

        btc_eth = (1. / btc_usd_ask) / (eth_btc_ask) * (eth_usd_bid)
        eth_btc = (1. / eth_usd_ask) * (eth_btc_bid) * (btc_usd_bid)
        if btc_eth > 1.0:
            pprint('BTC-ETH: %0.4f' % btc_eth)
        if eth_btc > 1.0:
            pprint('ETH-BTC: %0.4f' % eth_btc)

        btc_ltc = (1. / btc_usd_ask) / (ltc_btc_ask) * (ltc_usd_bid)
        ltc_btc = (1. / ltc_usd_ask) * (ltc_btc_bid) * (btc_usd_bid)
        if btc_ltc > 1.0:
            pprint('BTC-LTC: %0.4f' % btc_ltc)
        if ltc_btc > 1.0:
            pprint('LTC-BTC: %0.4f' % ltc_btc)

if __name__ == '__main__':
    log.startLogging(sys.stdout)

    ar = Arber()
    product_ids = ['BTC-USD', 'ETH-BTC', 'ETH-USD', 'LTC-USD', 'LTC-BTC']
    factory = BlobProtocolFactory('wss://ws-feed.gdax.com', product_ids=product_ids)
    factory.protocol = BlobProtocol
    for product_id in product_ids:
        bb = Book(factory.protocol, product_id, debug=False)
        bb.add_client(ar)
        ar.books[product_id] = bb

    connectWS(factory)
    reactor.run()

from autobahn.twisted.websocket import WebSocketClientFactory, connectWS
from twisted.python import log
from twisted.internet import reactor
from blobprotocol import BlobProtocol
from pprint import pprint
from book import Book, BookClient
from datetime import datetime

import pandas as pd
import sys
import numpy as np
import scipy.stats as dists


class Arber(BookClient):
    def __init__(self):
        self.fname = 'data/'+datetime.now().strftime('%Y-%m-%d')+'.'

        columns = ['t','px','sz','sd','bid','mid','ask']
        self.df = pd.DataFrame(columns=columns)
        self.initialized = False

    def add(self, oid, side, price, size):
        pass

    def change(self, oid, side, newsize):
        pass

    def match(self, oid, side, price, size):
        if not self.initialized:
            if self.book.get_mid() is not None:
                self.initialized = True
            else: return

        side = 'buy' if side == 'sell' else 'sell'
        bid = self.book.get_best_bid()
        ask = self.book.get_best_ask()
        mid = self.book.get_mid()

        entry = {'t':int(datetime.today().strftime('%s')),
                 'px':price, 'sz':size, 'sd':side[0],
                 'bid':bid, 'mid':mid, 'ask':ask}

        fmtsize = "-%0.4f"%size if side == "sell" else "+%0.4f"%size
        pprint('%s (%0.2f), %0.2f/%0.2f/%0.2f'%(fmtsize, price, bid, mid, ask))
        self.df = self.df.append(entry, ignore_index=True)
        self.df.to_csv(self.fname)

    def done(self, oid):
        pass


if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')
    factory.protocol = BlobProtocol

    ar = Arber()
    bb = Book(factory.protocol, debug=False)
    bb.add_client(ar)

    connectWS(factory)
    reactor.run()

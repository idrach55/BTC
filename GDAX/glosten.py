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
import scipy.stats as dists


# Glosten-Milgrom Model
class Glosten(Strategy):
    def __init__(self, rest, params):
        Strategy.__init__(self, rest)

        self.sigma = params['sigma']
        self.alpha = params['alpha']
        self.eta   = params['eta']
        self.save  = params['save']
        self.fname = datetime.now().strftime("data/%Y-%m-%d.trades.csv")

        self.df = pd.DataFrame(columns=['t','px','sz','sd','m','e'])
        self.initialized = False

    def traded(self, side, price):
        modup = (1 - self.alpha)*self.eta + self.alpha
        moddn = (1 - self.alpha) - (1 - self.alpha)*self.eta

        idx = int(100*price + 400*self.sigma - self.v0)
        if side == 'buy':
            self.prob[idx+1:] *= modup
            self.prob[:idx+1] *= moddn
        elif side == 'sell':
            self.prob[:idx] *= modup
            self.prob[idx:] *= moddn
        self.prob /= self.prob.sum()

    def setup_model(self, mid):
        self.v0 = 100*mid
        self.vals = (self.v0 - 4*100*self.sigma + np.arange(int(8*100*self.sigma) + 1))/100.
        self.prob = dists.norm.pdf(100*self.vals, loc=self.v0, scale=100*self.sigma)

    # Main update loop.
    def update(self):
        if not self.initialized and self.book.get_mid() is not None:
            self.initialized = True
            self.setup_model(self.book.get_mid())

    def match(self, oid, side, price, size):
        if not self.initialized:
            return
        side = 'buy' if side == 'sell' else 'sell'
        self.traded(side, price)
        est = (self.vals*self.prob).sum()
        mid = self.book.get_mid()
        fmtsize = "-%0.4f"%size if side == "sell" else "+%0.4f"%size
        pprint('%s (%0.2f), %0.2f/%0.2f'%(fmtsize, price, mid, est))
        self.df = self.df.append({'t':int(datetime.today().strftime('%s')),
                                  'px':price, 'sz':size, 'sd':side[0],
                                  'm':mid, 'e':est}, ignore_index=True)
        if self.save:
            self.df.to_csv(self.fname)

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')
    factory.protocol = BlobProtocol

    params = {'save'  : True,
              'sigma' : float(sys.argv[1]),
              'alpha' : float(sys.argv[2]),
              'eta'   : float(sys.argv[3])}

    rest = RESTProtocol(read_keys('keys.txt'), debug=True)
    gm = Glosten(rest, params=params)
    gm.enabled = False

    bb = Book(factory.protocol, debug=False)
    bb.add_client(gm)

    connectWS(factory)

    reactor.callLater(5.0, gm.enable)
    reactor.run()

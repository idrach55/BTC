'''
Author: Isaac Drachman
Description:
Implementations for TradeLogger and relevant models including Glosten Milgrom.
'''

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

class Model():
    def __init__(self, name):
        '''
        Constructs an abstract model.

        :param name: name of model
        '''
        self.name = name

    def out(self, side, price, size):
        '''
        Product model output given trade data.

        :param side: trade was market buy/sell
        :param price: price trade was executed at
        :param size: size of trade
        :return: model output
        '''
        pass

class Glosten(Model):
    def __init__(self, xk):
        '''
        Constructs a Glosten Milgrom model.

        :param xk: tuple of parameters (sigma, alpha, eta)
        '''
        Model.__init__(self, 'glosten')
        self.sigma, self.alpha, self.eta = xk

    def setup(self, mid):
        '''
        Initializes true value distribution.

        :param mid: midpoint before first recorded tick
        :return: void
        '''
        self.v0 = 100*mid
        self.vals = (self.v0 - 4*100*self.sigma + np.arange(int(8*100*self.sigma) + 1))/100.
        self.prob = dists.norm.pdf(100*self.vals, loc=self.v0, scale=100*self.sigma)

    def out(self, side, price, size):
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

        return (self.vals*self.prob).sum()


class TradeLogger(BookClient):
    def __init__(self, model=None):
        '''
        Constructs new trade logger.

        :param model: (optional) model to recieve trade data
        '''
        self.fname = 'data/'+datetime.now().strftime('%Y-%m-%d')+'.'
        self.model = model
        self.fname += 'trades.csv' if self.model is None else '%s.csv'%self.model.name

        columns = ['t','px','sz','sd','bid','mid','ask']
        if self.model is not None: columns += [self.model.name]
        self.df = pd.DataFrame(columns=columns)
        self.initialized = False

    def add(self, oid, side, price, size, product_id):
        pass

    def change(self, oid, side, newsize, product_id):
        pass

    def match(self, oid, side, price, size, product_id):
        if not self.initialized:
            if self.book.get_mid() is not None:
                self.initialized = True
                if self.model is not None: self.model.setup(self.book.get_mid())
            else: return

        side = 'buy' if side == 'sell' else 'sell'
        bid = self.book.get_best_bid()
        ask = self.book.get_best_ask()
        mid = self.book.get_mid()

        entry = {'t':int(datetime.today().strftime('%s')),
                 'px':price, 'sz':size, 'sd':side[0],
                 'bid':bid, 'mid':mid, 'ask':ask}

        fmtsize = "-%0.4f"%size if side == "sell" else "+%0.4f"%size
        if self.model is not None:
            model_out = self.model.out(side, price, size)
            entry[self.model.name] = model_out
            pprint('%s (%0.2f), %0.2f/%0.2f/%0.2f => %0.2f'%(fmtsize, price, bid, mid, ask, model_out))
        else:
            pprint('%s (%0.2f), %0.2f/%0.2f/%0.2f'%(fmtsize, price, bid, mid, ask))
        self.df = self.df.append(entry, ignore_index=True)
        self.df.to_csv(self.fname)

    def done(self, oid, product_id):
        pass


if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = BlobProtocolFactory('wss://ws-feed.gdax.com')
    factory.protocol = BlobProtocol

    model = None
    if len(sys.argv) >= 2:
        if sys.argv[1] == 'glosten':
            xk = (float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]))
            gm = Glosten(xk)
            model = gm

    tl = TradeLogger(model=model)
    bb = Book(factory.protocol, debug=False)
    bb.add_client(tl)

    connectWS(factory)
    reactor.run()

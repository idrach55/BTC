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
		self.delta = 1.0
		self.mids = []

	def add(self, oid, side, price, size):
		pass

	def change(self, oid, side, newsize):
		pass

	def match(self, oid, side, price, size):
		pass

	def done(self, oid):
		pass
		
	def generateStamp(self):
		mid = self.book.getMidPrice()
		self.mids.append(mid)
		if debug:
			pprint('volatility: %0.1f%%' % self.getHourlyVolatility())
		reactor.callLater(self.delta, self.generateStamp)

	def getHourlyVolatility(self):
		series = pandas.Series(self.mids)
		return sqrt(3600. / self.delta)*(series - series.shift(1)).std()

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')

    factory.protocol = BlobProtocol

    vm = VolMonitor(1.0)
    bb = Book(factory.protocol, debug=False)
    bb.addClient(vm)

    connectWS(factory)

    reactor.callLater(1.0, vm.generateStamp)
    reactor.run()
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


class VolMonitor(BookClient):
	# Setup a volatility monitor which records the midpoint every `dt` seconds.
	def __init__(self, dt):
		self.dt = dt
		self.series = pandas.Series()

	def onOpen(self):
		pass

	def add(self, oid, side, price, size):
		self.update()

	def change(self, oid, side, newsize):
		self.update()

	def match(self, oid, side, price, size):
		self.update()

	def done(self, oid):
		self.update()

	# Update from book messages and record midpoint if necessary.
	def update(self):
		if len(self.book.bids) == 0 or len(self.book.asks) == 0:
			return

		stamp = time.time()
		mid = self.book.getMidPrice()
		if len(self.series) > 0 and stamp - self.series.index[-1] < self.dt:
			return
		self.series = self.series.append(pandas.Series({stamp: mid}))

		# Print the hourly volatility based on these samples.
		pprint('volatility: %0.1f%%' % (100. * math.sqrt(3600. / self.dt) * self.getVolatility()))

	def getVolatility(self):
		return self.series.pct_change()[1:].std()
		

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')

    factory.protocol = BlobProtocol

    vm = VolMonitor(1.0)
    bb = Book(factory.protocol, debug=False)
    bb.addClient(vm)

    connectWS(factory)
    reactor.run()
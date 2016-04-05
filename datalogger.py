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


class DataLogger(BookClient):
	# Logs the TOB bid/ask every `delta` seconds for a total of `duration` seconds.
	def __init__(self, delta, duration, fname):
		self.delta = delta
		self.duration = duration
		self.fname = fname

		self.stamps = []
		self.bids = []
		self.asks = []

	def add(self, oid, side, price, size):
		pass

	def change(self, oid, side, newsize):
		pass

	def match(self, oid, side, price, size):
		pass

	def done(self, oid):
		pass

	def update(self):
		pass

	def generateStamp(self):
		stamp = time.time()
		ask = self.book.getBestAskPrice()
		bid = self.book.getBestBidPrice()

		self.stamps.append(stamp)
		self.asks.append(ask)
		self.bids.append(bid)
		if self.stamps[-1] - self.stamps[0] >= self.duration:
			self.close()
		else:
			reactor.callLater(self.delta, self.generateStamp)

	def close(self):
		df = pandas.DataFrame()
		df["bid"] = self.bids
		df["ask"] = self.asks
		df.index  = self.stamps
		df.to_csv(self.fname)
		reactor.stop()
		

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')

    factory.protocol = BlobProtocol

    delta = float(sys.argv[1])
    duration = float(sys.argv[2])
    filename = sys.argv[3]

    dl = DataLogger(delta, duration, filename+".csv")
    bb = Book(factory.protocol, debug=False)
    bb.addClient(dl)

    connectWS(factory)

    reactor.callLater(1.0, dl.generateStamp)
    reactor.run()
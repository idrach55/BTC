from autobahn.twisted.websocket import WebSocketClientFactory, connectWS
from twisted.python import log
from twisted.internet import reactor
from pprint import pprint

from blobprotocol import BlobProtocol
from book import Book, BookClient

import sys


class MidPointMonitor(BookClient):
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

	def update(self):
		if len(self.book.bids) == 0 or len(self.book.asks) == 0:
			return
		bidprice, bidsize = self.book.getBestBidQuote()
		askprice, asksize = self.book.getBestAskQuote()
		pprint('$ %0.2f (%0.4f) | (%0.4f) $ %0.2f' % (bidprice, bidsize, asksize, askprice))

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')

    factory.protocol = BlobProtocol

    mm = MidPointMonitor()
    bb = Book(factory.protocol, debug=False)
    bb.addClient(mm)

    connectWS(factory)
    reactor.run()
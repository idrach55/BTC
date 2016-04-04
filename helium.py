##################################
#	    UNDER CONSTRUCTION		 #
##################################

from autobahn.twisted.websocket import WebSocketClientFactory, connectWS
from twisted.python import log
from twisted.internet import reactor

import sys

from blobprotocol import BlobProtocol
from book import Book
from strategy import RESTProtocol, Strategy, readKeys


class Helium(Strategy):
	def __init__(self, rest, spread=0.10, tradeSize=1.0, debug=False):
		Strategy.__init__(self, rest, debug=debug)
		self.spread = spread
		self.tradeSize = tradeSize
		self.previousMid = None

	# Main update loop.
	def update(self):
		mid = self.book.getMid()
		# Not enough on book to get mid.
		if mid is None:
			return
		# If no change in midpoint, skip.
		if self.previousMid is not None and self.previousMid == mid:
			return
		bidSize, askSize = self.getOpenSize()
		if bidSize == 0.0 and askSize == 0.0:
			price = mid - self.spread/2.
			self.bid(self.tradeSize, price)

	def onPlace(self, oid, side, price, size):
		Strategy.onPlace(self, oid, side, price, size)

	def onPlaceFail(self, reason):
		Strategy.onPlaceFail(self, reason)

	def onPartialFill(self, order, remaining):
		Strategy.onPartialFill(self, order, remaining)

		price = order.price + self.spread
		self.ask(self.tradeSize - remaining, price)

	def onCompleteFill(self, order):
		Strategy.onCompleteFill(self, order)

		price = order.price + self.spread
		self.ask(self.tradeSize, price)


if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')

    factory.protocol = BlobProtocol

    rest = RESTProtocol(readKeys('keys.txt'), debug=True)

    hh = Helium(rest, spread=0.10, tradeSize=0.2, debug=True)
    bb = Book(factory.protocol, debug=False)
    bb.addClient(hh)

    connectWS(factory)
    reactor.run()
##################################
#	    UNDER CONSTRUCTION		 #
##################################

from autobahn.twisted.websocket import WebSocketClientFactory, connectWS
from twisted.python import log
from twisted.internet import reactor

import sys
import math
import scipy.stats

from blobprotocol import BlobProtocol
from volmonitor import VolMonitor
from book import Book
from strategy import RESTProtocol, Strategy, readKeys
from params import params


class Helium(Strategy):
	def __init__(self, rest, params):
		Strategy.__init__(self, rest, debug=params["debug"])

		self.spread = params["spread"]
		self.tradeSize = params["tradeSize"]
		self.dumpOnLockdown = params["dumpOnLockdown"]
		self.volThresh = params["volThresh"]
		self.maxDistance = params["maxDistance"]

		self.volmonitor = None
		self.previousMid = None

	# Main update loop.
	def update(self):
		if not self.enabled:
			return

		mid = self.book.getMid()
		## Not enough on book to get mid.
		#if mid is None:
		#	return
		# If no change in midpoint, skip.
		if self.previousMid is not None and self.previousMid == mid:
			return
		bidSize, askSize = self.getOpenSize()
		if bidSize == 0.0 and askSize == 0.0:
			price = mid - self.spread/2.
			self.bid(self.tradeSize, price)

		# If outstanding asks are too far from mid, lockdown.
		if askSize > 0.0:
			price = list(self.openOrders.values())[0].price
			if price - mid > self.maxDistance:
				self.lockdown("max distance exceeded")

		# Check for excessive volatility and lockdown if need be.
		if self.volmonitor is None:
			return

		vol = self.volmonitor.getHourlyVolatility()
		if vol >= self.volThresh:
			self.lockdown("excessive volatility")

	def lockdown(self, reason):
		Strategy.lockdown(self, reason)

	def onPlace(self, oid, side, price, size, otype):
		Strategy.onPlace(self, oid, side, price, size, otype)

	def onPlaceFail(self, reason):
		Strategy.onPlaceFail(self, reason)

	def onPartialFill(self, order, remaining):
		Strategy.onPartialFill(self, order, remaining)

		if order.side == "buy":
			price = order.price + self.spread
			self.ask(order.size - remaining, price)

	def onCompleteFill(self, order):
		Strategy.onCompleteFill(self, order)

		if order.side == "buy":
			price = order.price + self.spread
			self.ask(order.size, price)


if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')
    factory.protocol = BlobProtocol

    # Setup params from params.py.
    # paramsFile = 'params.py'
    # exec(compile(open(paramsFile).read(), paramsFile, 'exec')) 

    rest = RESTProtocol(readKeys('keys.txt'), debug=True)
    hh = Helium(rest, params=params)
    hh.enabled = False

    vm = VolMonitor(1.0)
    hh.volmonitor = vm

    bb = Book(factory.protocol, debug=False)
    bb.addClient(hh)
    bb.addClient(vm)

    connectWS(factory)

    reactor.callLater(1.0, vm.generateStamp)
    reactor.callLater(1.0, hh.enable)
    reactor.run()
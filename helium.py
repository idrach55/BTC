##################################
#	    UNDER CONSTRUCTION		 #
##################################

from strategy import RESTProtocol, Strategy, readKeys


class Helium(Strategy):
	def __init__(self, rest, spreadFactor=1.0, tradeSize=1.0):
		Strategy.__init__(self, rest)
		self.spreadFactor = spreadFactor
		self.tradeSize = tradeSize
		self.previousMid = None
		self.savedSpread = None

	# Main update loop.
	def update(self):
		mid = self.book.getMid()
		spread = 0.5*(self.book.getBestAskPrice() - self.book.getBestBidPrice())
		# If no change in midpoint, skip.
		if self.previousMid is not None and self.previousMid == mid:
			return
		bidSize, askSize = self.getOpenSize()
		if bidSize == 0.0:
			self.savedSpread = self.spreadFactor * spread
			price = mid - self.savedSpread
			self.bid(self.tradeSize, price)

	def onPlace(self, oid, side, price, size):
		Strategy.onPlace(self, oid, side, price, size)

	def onPlaceFail(self, reason):
		pass

	def onPartialFill(self, order, remaining):
		price = order.price + self.savedSpread
		self.ask(self.tradeSize - remaining, price)

	def onCompleteFill(self, order):
		spread = self.book.getAskPrice() - self.book.getBidPrice()
		price = order.price + self.savedSpread
		self.ask(self.tradeSize, price)

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')

    factory.protocol = BlobProtocol

    rest = RESTProtocol(readKeys("keys.txt"))

    hh = Helium(rest)
    bb = Book(factory.protocol, debug=False)
    bb.addClient(hh)

    connectWS(factory)
    reactor.run()
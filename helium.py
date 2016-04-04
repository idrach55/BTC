##################################
#	    UNDER CONSTRUCTION		 #
##################################

from strategy import Strategy


class Helium(Strategy):
	def __init__(self, rest, spread=0.10, tradeSize=1.0):
		Strategy.__init__(self, rest)
		self.spread = spread
		self.tradeSize = tradeSize
		self.previousMid = None

	# Main update loop.
	def update(self):
		mid = self.book.getMid()
		# If no change in midpoint, skip.
		if self.previousMid is not None and self.previousMid == mid:
			return
		bidSize, askSize = self.getOpenSize()
		if bidSize == 0.0:
			price = mid - self.spread/2.
			self.bid(self.tradeSize, price)

	def onPlace(self, oid, side, price, size):
		Strategy.onPlace(self, oid, side, price, size)

	def onPlaceFail(self, reason):
		pass

	def onPartialFill(self, order, remaining):
		price = order.price + self.spread
		self.ask(self.tradeSize - remaining, price)

	def onCompleteFill(self, order):
		price = order.price + self.spread
		self.ask(self.tradeSize, price)
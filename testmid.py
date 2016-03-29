import sys

from time import time
from strategy import Strategy

class TestStrat(Strategy):
	def __init__(self, keyfile):
		Strategy.__init__(self, keyfile)
		self.timestamp = None
		self.prediction = None
		self.popt = [0.91979228, 0.09446284, -0.01425317]
		self.book()

	def update(self, book):
		now = time()
		if self.timestamp is None or (now - self.timestamp) >= 1.0:
			self.timestamp = now

			mid = 0.5 * (book.getBestAsk() + book.getBestBid())
			if self.prediction is not None:
				error = 100. * (self.prediction - mid) / mid
				print "mid: %0.2f\tpredicted: %0.2f\terror: %0.2f%%    \r" % (mid, self.prediction, error),
				sys.stdout.flush() 
			vwap1 = 0.5 * (book.getVWAP(1.0) + book.getVWAP(-1.0))
			vwap5 = 0.5 * (book.getVWAP(5.0) + book.getVWAP(-5.0))
			self.prediction = mid * self.popt[0] + vwap1 * self.popt[1] + vwap5 * self.popt[2]
		return True


if __name__ == "__main__":
	test = TestStrat("keys.txt")
'''
Author: Isaac Drachman
Date:   09/05/2015
Description:
Test book with strategy that publishes simple stats.
'''

import sys
from strategy import Strategy

class TestStrat(Strategy):
	def __init__(self, keyfile):
		Strategy.__init__(self, keyfile)
		self.book()

	def update(self, book, msg):
		Strategy.update(self, book, msg)

		bidprice, bidsize = book.getBestBidQuote()
		askprice, asksize = book.getBestAskQuote()
		print "(%f) %f | %f (%f)    \r"%(bidsize, bidprice, askprice, asksize),
		sys.stdout.flush()
		return True

if __name__ == "__main__":
	test = TestStrat("keys.txt")

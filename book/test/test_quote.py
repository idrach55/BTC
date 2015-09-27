'''
Author: Isaac Drachman
Date:   09/05/2015
Description:
Test book with strategy that publishes simple stats.
'''

import sys

from cbe.strat import Strategy

class TestStrat(Strategy):
	def __init__(self, keyfile):
		Strategy.__init__(self, keyfile)
		self.state["updates"] = 0
		self.create_book()

	def update(self, book, state):
		bidprice, bidsize = book.getBestBidQuote()
		askprice, asksize = book.getBestAskQuote()
		print "(%f) %f | %f (%f)    \r"%(bidsize, bidprice, askprice, asksize),
		sys.stdout.flush()
		return True, state

if __name__ == "__main__":
	test = TestStrat("../../keys.txt")

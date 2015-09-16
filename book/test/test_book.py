'''
Author: Isaac Drachman
Date:   09/05/2015
Description:
Test book with strategy that publishes simple stats.
'''

import sys

from cbe.strat import Strategy

class TestBook(Strategy):
	def __init__(self, keyfile):
		Strategy.__init__(self, keyfile)
		self.create_book()

	def update(self, book, state):
		print "(%f) %f | %f (%f)    \r"%(book.get_best_size("bids"),
										 book.get_best_price("bids"),
										 book.get_best_price("asks"),
										 book.get_best_size("asks")),
		sys.stdout.flush()
		return True, state

if __name__ == "__main__":
	test = TestBook("../../keys.txt")

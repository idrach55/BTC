'''
Author: Isaac Drachman
Date:   09/27/2015
Description:
Tests book latency for analyzing messages.
'''

from book import Book
from time import clock
from cbe.strat import Strategy

import pandas
import sys

class TimedBook(Book):
	def __init__(self, cbe, delay, strathandle=None):
		Book.__init__(self, cbe, delay, strathandle)
		self.messageIncomingTime = None

	def update(self, msg):
		self.messageIncomingTime = clock()
		return Book.update(self, msg)

class TestStrat(Strategy):
	def __init__(self, keyfile, maxmsgs, out):
		Strategy.__init__(self, keyfile)

		# Initialize state.
		self.state["latencies"] = []
		self.state["nummsgs"] = 0
		self.state["maxmsgs"] = maxmsgs
		self.state["out"] = out

		# Launch book.
		self.create_book()

	def create_book(self):
		TimedBook(self.cbe, 3.0, (self, self.state))

	def update(self, book, state):
		state["nummsgs"] += 1 
		state["latencies"].append(1000. * (clock() - book.messageIncomingTime))
		if state["nummsgs"] >= state["maxmsgs"]:
			data = pandas.DataFrame(columns=["latencies"])
			data["latencies"] = state["latencies"]
			data.to_csv(state["out"], index=False) 
			return False, state
		return True, state

if __name__ == "__main__":
	test = TestStrat("../../keys.txt", int(sys.argv[1]), sys.argv[2])
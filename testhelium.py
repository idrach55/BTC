from helium import Helium
from book import Book, Order

import unittest
import pytest

from testbook import DummyBlobProtocol
from teststrategy import DummyRESTProtocol


class MyTest(unittest.TestCase):
	def test_update_bids(self):
		class Demo(Helium):
			def __init__(self, rest):
				Helium.__init__(self, rest, spreadFactor=1.0, tradeSize=1.0)

			def onPlace(self, oid, side, price, size):
				assert oid  == "B1"
				assert side == "buy"
				assert price == 100.00
				assert size == 1.0

		book = Book(DummyBlobProtocol())

		# Create following book.
		'''
		A 1.0 - 100.00 | 100.10 - 0.75 C
		B 0.5 -  99.50 | 101.00 - 0.5  D
		'''
		book.add("A", "buy",  100.00, 1.0)
		book.add("B", "buy",   99.50, 0.5)
		book.add("C", "sell", 100.10, 0.75)
		book.add("D", "sell", 101.00, 0.5)

		strat = Demo(DummyRESTProtocol())
		book.addClient(strat)

		# Update the size of order D to trigger update().
		'''
		A 1.0 - 100.00 | 100.10 - 0.75 C
		B 0.5 -  99.50 | 101.00 - 1.0  D
		'''
		book.change("D", "sell", 1.0)

	def test_onPartialFill(self):
		class Demo(Helium):
			def __init__(self, rest):
				Helium.__init__(self, rest, spreadFactor=1.0, tradeSize=1.0)
				self.waitingForAsk = False

			def onPlace(self, oid, side, price, size):
				Helium.onPlace(self, oid, side, price, size)
				if self.waitingForAsk:
					assert oid == "A1"
					assert side == "sell"
					assert price == 100.10
					assert size == 0.5
				if oid == "B1":
					self.waitingForAsk = True

		book = Book(DummyBlobProtocol())

		# Create following book.
		'''
		A 1.0 - 100.00 | 100.10 - 0.75 C
		B 0.5 -  99.50 | 101.00 - 0.5  D
		'''
		book.add("A", "buy",  100.00, 1.0)
		book.add("B", "buy",   99.50, 0.5)
		book.add("C", "sell", 100.10, 0.75)
		book.add("D", "sell", 101.00, 0.5)

		strat = Demo(DummyRESTProtocol())
		book.addClient(strat)

		# Update the size of order D to trigger update().
		'''
		A 1.0 - 100.00 | 100.10 - 0.75 C
		B 0.5 -  99.50 | 101.00 - 1.0  D
		'''
		book.change("D", "sell", 1.0)

		# Hit 1.5 of the bids at $100, 1.0 of the original order and 0.5 of the strategy's bid.
		book.match("A", "buy", 100.00, 1.0)
		book.match("B1", "buy", 100.00, 0.5)

	def test_onCompleteFill(self):
		class Demo(Helium):
			def __init__(self, rest):
				Helium.__init__(self, rest, spreadFactor=1.0, tradeSize=1.0)
				self.waitingForAsk = False

			def onPlace(self, oid, side, price, size):
				Helium.onPlace(self, oid, side, price, size)
				if self.waitingForAsk:
					assert oid == "A1"
					assert side == "sell"
					assert price == 100.10
					assert size == 1.0
				if oid == "B1":
					self.waitingForAsk = True

		book = Book(DummyBlobProtocol())

		# Create following book.
		'''
		A 1.0 - 100.00 | 100.10 - 0.75 C
		B 0.5 -  99.50 | 101.00 - 0.5  D
		'''
		book.add("A", "buy",  100.00, 1.0)
		book.add("B", "buy",   99.50, 0.5)
		book.add("C", "sell", 100.10, 0.75)
		book.add("D", "sell", 101.00, 0.5)

		strat = Demo(DummyRESTProtocol())
		book.addClient(strat)

		# Update the size of order D to trigger update().
		'''
		A 1.0 - 100.00 | 100.10 - 0.75 C
		B 0.5 -  99.50 | 101.00 - 1.0  D
		'''
		book.change("D", "sell", 1.0)

		# Hit 2.0 of the bids at $100, 1.0 of the original order and 1.0 of the strategy's bid.
		book.match("A", "buy", 100.00, 1.0)
		book.match("B1", "buy", 100.00, 1.0)

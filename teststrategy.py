from strategy import Strategy
from book import Book, Order

import unittest
import pytest


class LazyRESTProtcol:
	def request(self, params):
		return False, "did not feel like it"

class DummyRESTProtocol:
	def __init__(self):
		self.count = 0

	def request(self, params):
		return True, "A%d" % self.count

class MyTest(unittest.TestCase):
	def test_onPlaceFail(self):
		class Demo(Strategy):
			def onPlaceFail(self, reason):
				assert reason == "did not feel like it"
		strat = Demo(LazyRESTProtcol())
		strat.ask(1.0, 100.00)

	def test_onPlace(self):
		class Demo(Strategy):
			def onPlace(self, oid, side, price, size):
				Strategy.onPlace(self, oid, side, price, size)
				assert oid == "A0"
				assert self.openOrders.get("A0") == Order("A0", "buy", 100.00, 1.0)
		strat = Demo(DummyRESTProtocol())
		strat.bid(1.0, 100.00)
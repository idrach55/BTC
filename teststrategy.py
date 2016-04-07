from strategy import Strategy
from book import Book, Order

import unittest
import pytest


class LazyRESTProtcol:
    def submitTrade(self, params):
        return False, "did not feel like it"

class DummyRESTProtocol:
    def __init__(self):
        self.asks = 0
        self.bids = 0

    def submitTrade(self, params):
        oid = None
        if params["side"] == "buy":
            self.bids += 1
            oid = "B%d" % self.bids
        else:
            self.asks += 1
            oid = "A%d" % self.asks
        return True, oid

    def submitCancelAll(self):
        return True, None

class DemoStrategy(Strategy):
    def __init__(self):
        Strategy.__init__(self, DummyRESTProtocol())

class MyTest(unittest.TestCase):
    def test_onPlaceFail(self):
        strat = Strategy(LazyRESTProtcol())
        strat.ask(1.0, 100.00)
        assert strat.openOrders == {}

    def test_onPlace(self):
        strat = DemoStrategy()
        strat.bid(1.0, 100.00)
        assert strat.openOrders["B1"] == Order("B1", "buy", 100.00, 1.0)

    def test_onCompleteFill(self):
        strat = DemoStrategy()
        strat.bid(1.0, 100.00)
        strat.match("B1", "buy", 100.00, 1.0)
        assert strat.openOrders == {}

    def test_onPartialFill(self):
        strat = DemoStrategy()
        strat.bid(1.0, 100.00)
        strat.match("B1", "buy", 100.00, 0.5)
        assert strat.openOrders["B1"] == Order("B1", "buy", 100.00, 0.5)

    def test_getOpenSize(self):
        strat = DemoStrategy()
        strat.bid(1.0, 100.00)
        assert strat.getOpenSize() == (1.0, 0.0)
        strat.bid(0.5, 101.00)
        assert strat.getOpenSize() == (1.5, 0.0)
        strat.ask(0.5, 102.00)
        assert strat.getOpenSize() == (1.5, 0.5)

    def test_lockdown(self):
        strat = DemoStrategy()
        strat.lockdown("no reason")
        assert strat.enabled == False
        assert strat.lockdownReason == "no reason"

    def test_dumpOnLockdown(self):
        strat = DemoStrategy()
        strat.dumpOnLockdown = True
        strat.position = 1.0
        strat.lockdown("no reason")
        assert strat.enabled == False
        assert strat.position == 0.0
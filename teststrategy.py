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

class MyTest(unittest.TestCase):
    def test_onPlaceFail(self):
        class Demo(Strategy):
            def onPlaceFail(self, reason):
                assert reason == "did not feel like it"
        strat = Demo(LazyRESTProtcol())
        strat.ask(1.0, 100.00)

    def test_onPlace(self):
        class Demo(Strategy):
            def onPlace(self, oid, side, price, size, otype):
                Strategy.onPlace(self, oid, side, price, size, otype)
                assert oid == "B1"
                assert self.openOrders.get("B1") == Order("B1", "buy", 100.00, 1.0)
        strat = Demo(DummyRESTProtocol())
        strat.bid(1.0, 100.00)

    def test_onCompleteFill(self):
        class Demo(Strategy):
            def onCompleteFill(self, order):
                assert order.oid == "B1"
                assert self.openOrders.get("B1") is None
        strat = Demo(DummyRESTProtocol())
        strat.bid(1.0, 100.00)
        strat.match("B1", "buy", 100.00, 1.0)

    def test_onPartialFill(self):
        class Demo(Strategy):
            def onPartialFill(self, order, remaining):
                assert order.oid == "B1"
                assert remaining == 0.5
        strat = Demo(DummyRESTProtocol())
        strat.bid(1.0, 100.00)
        strat.match("B1", "buy", 100.00, 0.5)

    def test_getOpenSize(self):
        class Demo(Strategy):
            def onPlace(self, oid, side, price, size, otype):
                Strategy.onPlace(self, oid, side, price, size, otype)
                if oid == "B1":
                    assert self.getOpenSize() == (1.0, 0.0)
                elif oid == "B2":
                    assert self.getOpenSize() == (1.5, 0.0)
                elif oid == "A1":
                    assert self.getOpenSize() == (1.5, 0.5)
        strat = Demo(DummyRESTProtocol())
        strat.bid(1.0, 100.00)
        strat.bid(0.5, 101.00)
        strat.ask(0.5, 102.00)

    def test_dumpOnLockdown(self):
        class Demo(Strategy):
            def onPlace(self, oid, side, price, size, otype):
                Strategy.onPlace(self, oid, side, price, size, otype)
                assert otype == "market"
                assert size == 1.0
        strat = Demo(DummyRESTProtocol())
        strat.dumpOnLockdown = True
        strat.position = 1.0
        strat.lockdown("no reason")
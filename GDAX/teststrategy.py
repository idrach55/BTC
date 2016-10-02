from strategy import Strategy
from book import Book, Order

import unittest
import pytest


class LazyRESTProtcol:
    def submit_trade(self, params):
        return False, "did not feel like it"

class DummyRESTProtocol:
    def __init__(self):
        self.asks = 0
        self.bids = 0

    def submit_trade(self, params):
        oid = None
        if params["side"] == "buy":
            self.bids += 1
            oid = "B%d" % self.bids
        else:
            self.asks += 1
            oid = "A%d" % self.asks
        return True, oid

    def submit_cancel(self, oid=None):
        return True, None

    def get_balances(self):
        return True, 500.0, 0.0

class DemoStrategy(Strategy):
    def __init__(self):
        Strategy.__init__(self, DummyRESTProtocol())

class MyTest(unittest.TestCase):
    def test_on_place_fail(self):
        strat = Strategy(LazyRESTProtcol())
        strat.ask(1.0, 100.00)
        assert strat.open_orders == {}

    def test_on_place(self):
        strat = DemoStrategy()
        strat.bid(1.0, 100.00)
        assert strat.open_orders == {"B1": Order("B1", "buy", 100.00, 1.0)}

    def test_on_complete_fill(self):
        strat = DemoStrategy()
        strat.bid(1.0, 100.00)
        strat.match("B1", "buy", 100.00, 1.0)
        assert strat.open_orders == {}
        assert strat.btc_position == 1.0

    def test_on_partial_fill(self):
        strat = DemoStrategy()
        strat.bid(1.0, 100.00)
        strat.match("B1", "buy", 100.00, 0.5)
        assert strat.open_orders == {"B1": Order("B1", "buy", 100.00, 0.5)}
        assert strat.btc_position == 0.5

    def test_get_open_size(self):
        strat = DemoStrategy()
        strat.bid(1.0, 100.00)
        assert strat.get_open_size() == (1.0, 0.0)
        strat.bid(0.5, 101.00)
        assert strat.get_open_size() == (1.5, 0.0)
        strat.ask(0.5, 102.00)
        assert strat.get_open_size() == (1.5, 0.5)

    def test_lockdown(self):
        strat = DemoStrategy()
        strat.open_orders = {"B1": Order("B1", "buy", 100.00, 0.5)}
        strat.lockdown("no reason")
        assert strat.enabled == False
        assert strat.open_orders == {}
        assert strat.lockdown_reason == "no reason"

    def test_dump_on_lockdown(self):
        strat = DemoStrategy()
        strat.dump_on_lockdown = True
        strat.position = 1.0
        strat.lockdown("no reason")
        assert strat.btc_position == 0.0

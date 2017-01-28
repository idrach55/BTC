import unittest
import pytest

from deribit import Book, Arber, Entry, Order

class TestBook(Book):
    def __init__(self):
        """
        Set up following test book
        100 920.50 | 920.70 50
         50 920.00 | 921.20 150
        """
        self.bids = [{'price': 920.50, 'quantity': 100},
                     {'price': 920.00, 'quantity': 50}]
        self.asks = [{'price': 920.70, 'quantity': 50},
                     {'price': 921.20, 'quantity': 150}]

class TestArber(Arber):
    def __init__(self):
        self.book = TestBook()
        self.params = {'spread': 0.85,
                       'size':   100}

class TestCase(unittest.TestCase):
    def test_get_top(self):
        book = TestBook()
        bid, ask = book.get_top()
        assert bid == Entry(920.50, 100)
        assert ask == Entry(920.70, 50)

    def test_get_spread(self):
        book = TestBook()
        assert book.get_spread() == 0.20

    def test_market(self):
        arber = TestArber()
        bid, ask = arber.market()
        assert bid == Entry(920.51, 100)
        assert ask == Entry(920.69, 100)

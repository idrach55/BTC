from book import Book, Order

import unittest
import pytest


class DummyBlobProtocol:
    pass

class MyTest(unittest.TestCase):
    def test_add(self):
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

        # Get orders and assert.
        bids = [bid for bid in book.bids.items()]
        asks = [ask for ask in book.asks.items()]

        assert bids == [(99.50, [Order("B", "buy", 99.50, 0.5)]),
                        (100.00, [Order("A", "buy", 100.00, 1.0)])]
        assert asks == [(100.10, [Order("C", "sell", 100.10, 0.75)]),
                        (101.00, [Order("D", "sell", 101.00, 0.5)])]

    def test_change(self):
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

        # Halve the size of order D.
        '''
        A 1.0 - 100.00 | 100.10 - 0.75 C
        B 0.5 -  99.50 | 101.00 - 0.25 D
        '''
        book.change("D", "sell", 0.25)

        # Get orders and assert
        bids = [bid for bid in book.bids.items()]
        asks = [ask for ask in book.asks.items()]

        assert bids == [(99.50, [Order("B", "buy", 99.50, 0.5)]),
                        (100.00, [Order("A", "buy", 100.00, 1.0)])]
        assert asks == [(100.10, [Order("C", "sell", 100.10, 0.75)]),
                        (101.00, [Order("D", "sell", 101.00, 0.25)])]

    def test_match(self):
        book = Book(DummyBlobProtocol())

        # Create following book
        '''
        A 1.0 - 100.00 | 100.10 - 0.75 C
        B 0.5 -  99.50 | 101.00 - 0.5  D
        '''
        book.add("A", "buy",  100.00, 1.0)
        book.add("B", "buy",   99.50, 0.5)
        book.add("C", "sell", 100.10, 0.75)
        book.add("D", "sell", 101.00, 0.5)

        # Hit 0.5 off the top bid
        '''
        A 0.5 - 100.00 | 100.10 - 0.75 C
        B 0.5 -  99.50 | 101.00 - 0.25 D
        '''
        book.match("A", "buy", 100.00, 0.5)

        # Get orders and assert
        bids = [bid for bid in book.bids.items()]
        asks = [ask for ask in book.asks.items()]

        assert bids == [(99.50, [Order("B", "buy", 99.50, 0.5)]),
                        (100.00, [Order("A", "buy", 100.00, 0.5)])]
        assert asks == [(100.10, [Order("C", "sell", 100.10, 0.75)]),
                        (101.00, [Order("D", "sell", 101.00, 0.5)])]

        # Hit the rest of the top bid
        '''
        B 0.5 -  99.50 | 100.10 - 0.75 C
                       | 101.00 - 0.25 D
        '''
        book.match("A", "buy", 100.00, 0.5)

        # Get orders and assert
        bids = [bid for bid in book.bids.items()]
        asks = [ask for ask in book.asks.items()]

        assert bids == [(99.50, [Order("B", "buy", 99.50, 0.5)])]
        assert asks == [(100.10, [Order("C", "sell", 100.10, 0.75)]),
                        (101.00, [Order("D", "sell", 101.00, 0.5)])]

    def test_done(self):
        book = Book(DummyBlobProtocol())

        # Create following book
        '''
        A 1.0 - 100.00 | 100.10 - 0.75 C
        B 0.5 -  99.50 | 101.00 - 0.5  D
        '''
        book.add("A", "buy",  100.00, 1.0)
        book.add("B", "buy",   99.50, 0.5)
        book.add("C", "sell", 100.10, 0.75)
        book.add("D", "sell", 101.00, 0.5)

        # Drop order D
        '''
        A 1.0 - 100.00 | 100.10 - 0.75 C
        B 0.5 -  99.50 |
        '''
        book.done("D")

        # Get orders and assert
        bids = [bid for bid in book.bids.items()]
        asks = [ask for ask in book.asks.items()]

        assert bids == [(99.50, [Order("B", "buy", 99.50, 0.5)]),
                        (100.00, [Order("A", "buy", 100.00, 1.0)])]
        assert asks == [(100.10, [Order("C", "sell", 100.10, 0.75)])]

    def test_getBestPrices(self):
        book = Book(DummyBlobProtocol())

        # Create following book
        '''
        A 1.0 - 100.00 | 100.10 - 0.75 C
        B 0.5 -  99.50 | 101.00 - 0.5  D
        '''
        book.add("A", "buy",  100.00, 1.0)
        book.add("B", "buy",   99.50, 0.5)
        book.add("C", "sell", 100.10, 0.75)
        book.add("D", "sell", 101.00, 0.5)

        assert book.get_best_bid() == 100.00
        assert book.get_best_ask() == 100.10

    def test_getBestQuotes(self):
        book = Book(DummyBlobProtocol())

        # Create following book
        '''
        A 1.0 - 100.00 | 100.10 - 0.75 C
        B 0.5 -  99.50 | 101.00 - 0.5  D
        '''
        book.add("A", "buy",  100.00, 1.0)
        book.add("B", "buy",   99.50, 0.5)
        book.add("C", "sell", 100.10, 0.75)
        book.add("D", "sell", 101.00, 0.5)

        assert book.get_best_bid_quote() == (100.00, 1.0)
        assert book.get_best_ask_quote() == (100.10, 0.75)

    def test_getMid(self):
        book = Book(DummyBlobProtocol())

        # Create following book
        '''
        A 1.0 - 100.00 | 100.10 - 0.75 C
        B 0.5 -  99.50 | 101.00 - 0.5  D
        '''
        book.add("A", "buy",  100.00, 1.0)
        book.add("B", "buy",   99.50, 0.5)
        book.add("C", "sell", 100.10, 0.75)
        book.add("D", "sell", 101.00, 0.5)

        assert book.get_mid() == 100.05

    def test_getVWAP(self):
        book = Book(DummyBlobProtocol())

        # Create following book
        '''
        A 1.0 - 100.00 | 100.10 - 0.75 C
        B 0.5 -  99.50 | 101.00 - 0.5  D
        '''
        book.add("A", "buy",  100.00, 1.0)
        book.add("B", "buy",   99.50, 0.5)
        book.add("C", "sell", 100.10, 0.75)
        book.add("D", "sell", 101.00, 0.5)

        assert book.get_vwap(1.0) == (100.10 * 0.75 + 101.00 * 0.25)
        assert book.get_vwap(-1.5) == (100.00 * 1.0 + 99.50 * 0.5) / 1.5

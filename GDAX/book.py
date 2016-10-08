'''
Author: Isaac Drachman
Description:
Implementations for Book and its client BookClient.
'''

from bintrees import FastRBTree
from collections import namedtuple
from blobprotocol import BlobClient
from pprint import pprint

import requests


# Nifty namedtuples are nifty.
Order = namedtuple('Order', ['oid', 'side', 'price', 'size'])

class InsufficientSizeForVWAP(Exception):
    pass


class BookClient:
    '''
    BookClient is fed all messages which hit the book.
    '''
    def on_book_connected(self, book):
        self.book = book

    def add(self, oid, side, price, size):
        raise NotImplementedError

    def change(self, oid, side, newsize):
        raise NotImplementedError

    def match(self, oid, side, price, size):
        raise NotImplementedError

    def done(self, oid):
        raise NotImplementedError

    def on_sequence_gap(self):
        raise NotImplementedError

class Book(BlobClient):
    def __init__(self, protocol, debug=False):
        '''
        Constructs an order book which will be a client to
        the given blob protocol.

        :param protocol: blob protocol to which this will be a client
        :param debug: flag to print debug message
        '''
        BlobClient.__init__(self, protocol)

        self.debug = debug
        # A book can forward messages to multiple BookClients.
        self.clients = []

        # Track sequence number for blob protocol.
        self.sequence = None

        # Internal data structures for storing orders.
        self.orders_by_id = {}
        self.bids = FastRBTree()
        self.asks = FastRBTree()

    def add_client(self, client):
        '''
        Add client to this book to be forwarded messages.

        :param client: book client
        '''
        self.clients.append(client)
        client.on_book_connected(self)

    def on_open(self):
        r = requests.get('https://api.exchange.coinbase.com/products/BTC-USD/book', params={'level': 3})
        book = r.json()
        for bid in book["bids"]:
            self.add(bid[2], "buy", float(bid[0]), float(bid[1]))
        for ask in book["asks"]:
            self.add(ask[2], "sell", float(ask[0]), float(ask[1]))
        # Track sequence since the BlobProtocol will check this off us to look for gaps.
        self.sequence = book["sequence"]
        if self.debug:
            pprint('downloaded (bids: %d, asks: %d)' % (len(self.bids), len(self.asks)))

    def add(self, oid, side, price, size):
        order = Order(oid, side, price, size)
        tree = self._get_order_tree(order.side)
        try:
            tree[order.price].append(order)
        except KeyError:
            tree[order.price] = [order]
        self.orders_by_id[order.oid] = order
        if self.debug:
            pprint('added (%s, %s, $ %0.2f, %0.4f BTC)' % (oid, side, price, size))
        for client in self.clients:
            client.add(oid, side, price, size)

    def change(self, oid, side, newsize):
        order = self._get_order_by_id(oid)
        if order is None:
            return
        tree = self._get_order_tree(side)
        oidx = tree[order.price].index(order)
        tree[order.price][oidx] = Order(oid, side, order.price, newsize)
        self.orders_by_id[order.oid] = tree[order.price][oidx]
        if self.debug:
            pprint('changed (%s, %s, $ %0.2f, %0.2f BTC)' % (oid, side, order.price, newsize))
        for client in self.clients:
            client.change(oid, side, newsize)

    def match(self, oid, side, price, size):
        tree = self._get_order_tree(side)
        if self._get_order_by_id(oid) is None or tree[price][0].oid != oid:
            return
        tree[price][0] = Order(tree[price][0].oid, tree[price][0].side, tree[price][0].price, tree[price][0].size - size)
        self.orders_by_id[oid] = tree[price][0]
        if tree[price][0].size <= 0:
            self.done(oid)
        if self.debug:
            pprint('matched (%s, %s, $ %0.2f, %0.4f BTC)' % (oid, side, price, size))
        for client in self.clients:
            client.match(oid, side, price, size)

    def done(self, oid):
        order = self._get_order_by_id(oid)
        if order is None:
            return
        tree = self._get_order_tree(order.side)
        if len(tree[order.price]) > 1:
            tree[order.price].remove(order)
        else:
            del tree[order.price]
        del self.orders_by_id[oid]
        if self.debug:
            pprint('removed (%s)' % (oid,))
        for client in self.clients:
            client.done(oid)

    def on_sequence_gap(self):
        if self.debug:
            pprint('sequence gap')
        for client in self.clients:
            client.on_sequence_gap()

    def get_best_bid(self):
        '''
        Return the price of the highest bid.

        :return: float for price or None if no bids
        '''
        if len(self.bids) == 0:
            return None
        return self._get_order_tree("buy").max_item()[0]

    def get_best_ask(self):
        '''
        Return the price of the lowest ask.

        :return: float for price or None if no asks
        '''
        if len(self.asks) == 0:
            return None
        return self._get_order_tree("sell").min_item()[0]

    def get_best_bid_quote(self):
        '''
        Return price and size of highest bid.
        '''
        if len(self.bids) == 0:
            return None, None
        price, orders = self._get_order_tree("buy").max_item()
        size = 0.0
        for order in orders:
            size += order.size
        return price, size

    def get_best_ask_quote(self):
        '''
        Return price and size of lowest ask.
        '''
        if len(self.asks) == 0:
            return None
        price, orders = self._get_order_tree("sell").min_item()
        size = 0.0
        for order in orders:
            size += order.size
        return price, size

    def get_mid(self):
        '''
        Return mid between best bid/ask.
        '''
        if len(self.bids) == 0 or len(self.asks) == 0:
            return None
        return 0.5 * (self.get_best_bid() + self.get_best_ask())

    def get_vwap(self, target):
        '''
        Returns VWAP for a given target size.
        Positive sizes will sweep up the asks.
        Negative sizes will sweep down the bids.

        :param target: size to sweep (pos is buy, neg is sell)
        :return: vwap for target size
        '''
        side = "buy" if target < 0 else "sell"
        tree = self._get_order_tree(side)
        iterator = tree.items(True) if target < 0 else tree.items()
        levels = [(l[0], sum([o.size for o in l[1]])) for l in iterator]

        avgprice = 0.0
        target = abs(target)
        cumsize = target
        idx = 0
        while target > 0:
            if idx >= len(levels):
                raise InsufficientSizeForVWAP(target)
            price, size = levels[idx]
            avgprice += price * min(target, size)
            target = target - size if target > size else 0
            idx += 1
        return avgprice / cumsize

    # Order operations.
    def _get_order_by_id(self, oid):
        try:
            return self.orders_by_id[oid]
        except:
            return None

    # Return red-black binary tree by side of book.
    def _get_order_tree(self, side):
        return self.bids if side == "buy" else self.asks

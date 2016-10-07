'''
UNDER CONSTRUCTION
'''

from autobahn.twisted.websocket import WebSocketClientFactory, connectWS
from twisted.python import log
from twisted.internet import reactor
from pprint import pprint
from time import time

import sys
import math
import scipy.stats

from blobprotocol import BlobProtocol
from book import Book, InsufficientSizeForVWAP
from strategy import RESTProtocol, Strategy, read_keys


class Helium(Strategy):
    def __init__(self, rest, params):
        Strategy.__init__(self, rest, debug=params['debug'])

        if self.debug:
            pprint('params: %s' % str(params))
        self.spread            = params['spread']
        self.trade_size        = params['trade_size']
        self.dump_on_lockdown  = params['dump_on_lockdown']
        self.max_distance      = params['max_distance']
        self.shading           = params['shading']
        self.stop_loss         = params.get('stop_loss')
        self.max_inactive_time = params.get('max_inactive_time')

        self.time_of_last_bid = 0.

    # Main update loop.
    def update(self):
        if not self.enabled:
            return

        # ask_vwap = self.book.get_vwap(self.trade_size)
        # bid_vwap = self.book.get_vwap(-self.trade_size)
        # mid = 0.5 * (bid_vwap + ask_vwap)
        mid = self.book.get_mid()

        if self.initial_marking is None and self.stop_loss is not None:
            success, usd, btc = self.rest.get_balances()
            if success:
                self.usd_position = usd
                self.initial_marking = self.usd_position
                if self.debug:
                    pprint("initial positions read %0.2f USD" % usd)

        # We want bids + position = trade_size.
        # However, minimum trade size is 0.01 btc.
        bid_size, ask_size = self.get_open_size()
        if self.trade_size - (bid_size + self.btc_position) >= 0.01:
            self.time_of_last_bid = time()
            price = mid - self.shading * self.spread
            self.bid(self.trade_size - bid_size - self.btc_position, price)

        # If time since last bid exceeds maximum, re-place bids.
        if self.max_inactive_time is not None:
            inactive_time = time() - self.time_of_last_bid
            if bid_size > 0 and inactive_time > self.max_inactive_time:
                pprint('bids inactive for %d seconds' % inactive_time)
                self.replace_bids()

        # If outstanding asks are too far from mid, lockdown.
        if ask_size > 0.0:
            price = list(self.open_orders.values())[0].price
            if price - mid > self.max_distance:
                self.lockdown("max distance exceeded")

        # If stop-loss triggered, lockdown.
        if self.stop_loss is not None:
            marked = self.btc_position * mid + self.usd_position
            if marked - self.initial_marking <= -self.stop_loss:
                self.lockdown("stop loss of %0.2f triggered" % self.stop_loss)

    def replace_bids(self):
        self.time_of_last_bid = time()
        bids = [order for order in self.open_orders.values() if order.side == "buy"]
        bid_size = sum(map(lambda bid: bid.size, bids))
        for bid in bids:
            self.cancel(bid.oid)

        mid = self.book.get_mid()
        self.bid(bid_size, mid - self.shading * self.spread)

    def place_spread_ask(self, size, bought_at):
        price = bought_at + self.spread
        self.ask(size, price)

    def lockdown(self, reason):
        Strategy.lockdown(self, reason)

    def on_place(self, oid, side, price, size, otype):
        Strategy.on_place(self, oid, side, price, size, otype)

    def on_place_fail(self, reason):
        Strategy.on_place_fail(self, reason)

    def on_partial_fill(self, order, remaining):
        Strategy.on_partial_fill(self, order, remaining)
        if order.side == "buy":
            self.place_spread_ask(order.size - remaining, order.price)

    def on_complete_fill(self, order):
        Strategy.on_complete_fill(self, order)
        if order.side == "buy":
            self.place_spread_ask(order.size, order.price)


if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')
    factory.protocol = BlobProtocol

    # Setup params from params.py.
    params_file = sys.argv[1]
    exec(compile(open(params_file).read(), params_file, 'exec'))

    if len(sys.argv) > 2:
        params["spread"] = float(sys.argv[2])
        params["shading"] = float(sys.argv[3])

    rest = RESTProtocol(read_keys('keys.txt'), debug=True)
    hh = Helium(rest, params=params)
    hh.enabled = False

    bb = Book(factory.protocol, debug=False)
    bb.add_client(hh)

    connectWS(factory)

    reactor.callLater(5.0, hh.enable)
    reactor.run()

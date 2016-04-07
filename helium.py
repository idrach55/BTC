##################################
#       UNDER CONSTRUCTION       #
##################################

from autobahn.twisted.websocket import WebSocketClientFactory, connectWS
from twisted.python import log
from twisted.internet import reactor

import sys
import math
import scipy.stats

from blobprotocol import BlobProtocol
from volmonitor import VolMonitor
from book import Book
from strategy import RESTProtocol, Strategy, read_keys


class Helium(Strategy):
    def __init__(self, rest, params):
        Strategy.__init__(self, rest, debug=params['debug'])

        self.spread = params['spread']
        self.trade_size = params['trade_size']
        self.dump_on_lockdown = params['dump_on_lockdown']
        self.vol_thresh = params['vol_thresh']
        self.max_distance = params['max_distance']

        self.volmonitor = None
        self.previous_mid = None

    # Main update loop.
    def update(self):
        if not self.enabled:
            return

        mid = self.book.get_mid()
        # If no change in midpoint, skip.
        if self.previous_mid is not None and self.previous_mid == mid:
            return

        # We want bids + position = trade_size...
        bid_size, ask_size = self.get_open_size()
        if bid_size + self.position < self.trade_size:
            price = mid - self.spread/2.
            self.bid(self.trade_size - bid_size - self.position, price)

        # If outstanding asks are too far from mid, lockdown.
        if ask_size > 0.0:
            price = list(self.open_orders.values())[0].price
            if price - mid > self.max_distance:
                self.lockdown("max distance exceeded")

        # We leave the vol monitor as optional, skip checks if not found.
        if self.volmonitor is None:
            return

        # Check for excessive volatility and lockdown if need be.
        vol = self.volmonitor.get_hourly_volatility()
        if vol >= self.vol_thresh:
            self.lockdown("excessive volatility")

    def lockdown(self, reason):
        Strategy.lockdown(self, reason)

    def on_place(self, oid, side, price, size, otype):
        Strategy.on_place(self, oid, side, price, size, otype)

    def on_place_fail(self, reason):
        Strategy.on_place_fail(self, reason)

    def on_partial_fill(self, order, remaining):
        Strategy.on_partial_fill(self, order, remaining)
        if order.side == "buy":
            price = order.price + self.spread
            self.ask(order.size - remaining, price)

    def on_complete_fill(self, order):
        Strategy.on_complete_fill(self, order)
        if order.side == "buy":
            price = order.price + self.spread
            self.ask(order.size, price)


if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')
    factory.protocol = BlobProtocol

    # Setup params from params.py.
    params_file = sys.argv[1]
    exec(compile(open(params_file).read(), params_file, 'exec')) 

    rest = RESTProtocol(read_keys('keys.txt'), debug=True)
    hh = Helium(rest, params=params)
    hh.enabled = False

    vm = VolMonitor(1.0)
    hh.volmonitor = vm

    bb = Book(factory.protocol, debug=False)
    bb.add_client(hh)
    bb.add_client(vm)

    connectWS(factory)

    reactor.callLater(1.0, vm.generate_stamp)
    reactor.callLater(1.0, hh.enable)
    reactor.run()
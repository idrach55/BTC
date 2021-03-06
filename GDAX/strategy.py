'''
Author: Isaac Drachman
Description:
Class implementations for Strategy, RESTProtocol, and Authorizer.
'''

from twisted.internet import reactor
from twisted.internet.error import ReactorNotRunning
from requests.auth import AuthBase
from book import BookClient, Order
from pprint import pprint

import hashlib
import time
import json
import hmac
import base64
import requests
import math
import codecs


# Read authorization keys from file.
def read_keys(filename):
    with open(filename, "r") as f:
        return f.read().split("\n")[:3]

'''
This is the outlet to the exchange via the REST api.
We use this to submit orders, cancel requests, and soon to get account data.
'''
class RESTProtocol:
    def __init__(self, keys, debug=False):
        self.auth = Authorizer(keys)
        self.debug = debug

    # Submit a trade.
    def submit_trade(self, params):
        if self.debug:
            pprint('trade: %s' % str(params))
        r = requests.post("https://api.gdax.com/orders", json=params, auth=self.auth)
        if r.status_code == 200:
            return True, r.json()["id"]
        return False, r.json()["message"]

    # Submit a cancel.
    def submit_cancel(self, oid=None):
        url = 'https://api.gdax.com/orders'
        if oid is not None:
            url += '/%s' % oid
        r = requests.delete(url, auth=self.auth)
        if r.status_code == 200:
            return True, None
        return False, r.json()["message"]

    def get_balances(self, other='BTC'):
        r = requests.get("https://api.gdax.com/accounts", auth=self.auth)
        if r.status_code == 200:
            accounts = r.json()
            btc = 0.0
            usd = 0.0
            if accounts[0]["currency"] == "USD":
                usd = float(accounts[0]["balance"])
                btc = float(accounts[1]["balance"])
            elif accounts[0]["currency"] == other:
                btc = float(accounts[0]["balance"])
                usd = float(accounts[1]["balance"])
            return True, usd, btc
        return False, None, None

# Authorizes coinbase exchange calls.
class Authorizer(AuthBase):
    # Initialize authorizer with keys and passphrase.
    def __init__(self, keys):
        self.api_key, self.secret_key, self.passphrase = keys

    # This method is called by the requests when authentication is needed.
    def __call__(self, request):
        timestamp = str(time.time())
        body = request.body.decode('utf-8') if request.body is not None else ''
        message = timestamp + request.method + request.path_url + body
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message.encode('utf-8'), hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest())

        request.headers.update({
            "CB-ACCESS-SIGN": signature_b64,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-PASSPHRASE": self.passphrase,
            'Content-Type': 'application/json'
        })
        return request

# A strategy is book client attached to a REST protocol.
class Strategy(BookClient):
    def __init__(self, rest, debug=False, product='BTC'):
        self.rest = rest

        # These are the only parameters.
        # Subclasses of Strategy should combine these into a params dict.
        self.debug = debug
        self.dump_on_lockdown = False
        self.stop_loss = None

        # Track enabled: has the book been primed, open orders, and BTC position.
        self.enabled = True
        self.lockdown_reason = None
        self.open_orders = {}
        self.btc_position = 0.
        self.usd_position = 0.
        self.initial_marking = None

    # Makes strategy wait while book is primed.
    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    # BookClient methods.
    def add(self, oid, side, price, size, product_id):
        self.update()

    def change(self, oid, side, newsize, product_id):
        self.update()

    def match(self, oid, side, price, size, product_id):
        # Look for our fills here!
        order = self.open_orders.get(oid)
        if order is not None:
            remaining = order.size - size

            # Adjust internal BTC position accordingly.
            self.btc_position += size if side == "buy" else -size
            self.usd_position += size * price if side == "sell" else -size * price

            # Check with some epsilon for complete vs. partial fills.
            if remaining <= 0.00000001:
                del self.open_orders[oid]
                self.on_complete_fill(order)
            else:
                self.open_orders[oid] = Order(oid, side, price, remaining)
                self.on_partial_fill(order, remaining)
        # Relay!
        self.update()

    def done(self, oid, product_id):
        self.update()

    def on_sequence_gap(self):
        self.lockdown('sequence gap')

    # Main update loop.
    def update(self):
        if not self.enabled:
            return

    def dump_btc(self):
        self.trade(self.btc_position, "sell", otype="market")

    def lockdown(self, reason):
        if self.debug:
            pprint("lockdown: %s" % reason)
        self.lockdown_reason = reason
        success = self.cancel()
        if self.dump_on_lockdown:
            self.dump_btc()
        self.disable()
        try:
        	reactor.stop()
        except ReactorNotRunning as e:
        	return

    '''
    We assume 100 percent fill rate on market orders.
    Since the blob protocol (for now) only handles
    maker_order_id on matches we would not see
    our market orders. Since we don't do it too often
    this has not been changed.
    '''
    def on_place(self, oid, side, price, size, otype):
        if self.debug:
            pprint('on_place: %s' % oid)

        # If limit order, add to open_orders.
        # If market order, change BTC position now.
        if otype == "limit":
            order = Order(oid, side, price, size)
            self.open_orders[oid] = order
        elif otype == "market":
            self.btc_position += size if side == "buy" else -size

    def on_place_fail(self, reason):
        if self.debug:
            pprint('on_place_fail: %s' % reason)

    def on_partial_fill(self, order, remaining):
        if self.debug:
            pprint('on_partial_fill: %s, with %0.4f remaining' % (str(order), remaining))

    def on_complete_fill(self, order):
        if self.debug:
            pprint('on_complete_fill: %s' % (str(order)))

    def get_open_bids(self):
        return [order for order in self.open_orders.values() if order.side == "buy"]

    def get_open_asks(self):
        return [order for order in self.open_orders.values() if order.side == "sell"]

    def get_open_size(self):
        bid_size = sum(map(lambda order: order.size, self.get_open_bids()))
        ask_size = sum(map(lambda order: order.size, self.get_open_asks()))
        return bid_size, ask_size

    def cancel(self, oid=None):
        success = self.rest.submit_cancel(oid=oid)
        if success and oid is None:
            if self.debug:
                pprint('cancelled all orders')
            self.open_orders = {}
        elif success and oid is not None:
            if self.debug:
                pprint('cancelled order %s' % oid)
            del self.open_orders[oid]

    # Submit trade.
    def trade(self, size, side, price=None, otype="limit", post_only=True):
        if not self.enabled:
            return

        product_id = self.product

        if otype == "limit" and not price:
            self.on_place_fail("price not specified")

        # Prevent size from being too precise.
        size  = math.floor(1e8 * size) / 1e8

        # Fill order parameters.
        params = {"type":       otype,
                  "side":       side,
                  "price":      price,
                  "size":       size,
                  "product_id": product_id}
        if otype == "limit":
            params["post_only"] = True

        '''
        Send request. There's no need to trigger onPlace for market orders
        since they will only occur with lockdown.
        '''
        success, res = self.rest.submit_trade(params)
        if success:
            self.on_place(res, side, price, size, otype)
        else:
            self.on_place_fail(res)

    '''
    Prices and sizes cannot be too precise.
    Therefore, ceiling ask prices and floor bid prices.
    TODO: this is not general enough. The above method
    should do this on its own in some way. Additionally
    only sizes on asks are fixed, but not bids.
    '''
    def ask(self, size, price):
        price = math.ceil(100 * price) / 100.
        size = math.floor(1e8 * size) / 1e8
        self.trade(size, "sell", price=price)

    def bid(self, size, price):
        price = math.floor(100 * price) / 100.
        self.trade(size, "buy", price=price)

# Author: Isaac Drachman
# Description:
# Class implementations for Strategy, RESTProtocol, and Authorizer.

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
def readKeys(filename):
    with open(filename, "r") as f:
        return f.read().split("\n")

# This is the outlet to the exchange via the REST api.
# We use this to submit orders, cancel requests, and soon to get account data.
class RESTProtocol:
    def __init__(self, keys, debug=False):
        self.auth = Authorizer(keys)
        self.debug = debug

    # Submit a trade.
    def submitTrade(self, params):
        if self.debug:
            pprint('trade: %s' % str(params))
        r = requests.post("https://api.exchange.coinbase.com/orders", json=params, auth=self.auth)
        if r.status_code == 200:
            return True, r.json()["id"]
        else:
            return False, r.json()["message"]

    # Submit a cancelAll.
    # TODO: this should be duplicated/modified to create a 
    # method for cancelling single orders.
    def submitCancelAll(self):
        if self.debug:
            pprint('cancelling all orders')
        r = requests.delete("https://api.exchange.coinbase.com/orders", auth=self.auth)
        if r.status_code == 200:
            return True, None
        else:
            return False, r.json()["message"]

# Authorizes coinbase exchange calls.
class Authorizer(AuthBase):
    # Initialize authorizer with keys and passphrase.
    def __init__(self, keys):
        self.api_key, self.secret_key, self.passphrase = keys

    # This method is called by the requests when authentication is needed.
    def __call__(self, request):
        timestamp = str(time.time())
        message = timestamp + request.method + request.path_url + (request.body or "")
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, str(message).encode('utf-8'), hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest())

        request.headers.update({
            "CB-ACCESS-SIGN": signature_b64,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-PASSPHRASE": self.passphrase,
        })
        return request

# A strategy is book client attached to a REST protocol.
class Strategy(BookClient):
    def __init__(self, rest, debug=False):
        self.rest = rest

        # These are the only parameters.
        # Subclasses of Strategy should combine these into a params dict.
        self.debug = debug
        self.dumpOnLockdown = False

        # Track enabled: has the book been primed, open orders, and BTC position.       
        self.enabled = True
        self.lockdownReason = None
        self.openOrders = {}
        self.position = 0.

    # Makes strategy wait while book is primed.
    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    # BookClient methods.
    def add(self, oid, side, price, size):
        self.update()

    def change(self, oid, side, newsize):
        self.update()

    def match(self, oid, side, price, size):
        # Look for our fills here!
        order = self.openOrders.get(oid)
        if order is not None:
            remaining = order.size - size

            # Adjust internal BTC position accordingly. 
            self.position += size if order.side == "buy" else -size

            # Check with some epsilon for complete vs. partial fills.
            if remaining <= 0.00000001:
                del self.openOrders[oid]
                self.onCompleteFill(order)
            else:
                self.openOrders[oid] = Order(oid, side, price, remaining)
                self.onPartialFill(order, remaining)
        # Relay!
        self.update()

    def done(self, oid):
        self.update()

    def onSequenceGap(self):
        self.lockdown('sequence gap')

    # Main update loop.
    def update(self):
        if not self.enabled:
            return

    def dumpBTC(self):
        self.trade(self.position, "sell", otype="market")

    def lockdown(self, reason):
        if self.debug:
            pprint("lockdown: %s" % reason)
        self.lockdownReason = reason
        success = self.rest.submitCancelAll()
        if self.dumpOnLockdown:
            self.dumpBTC()
        self.disable()

    # We assume 100% fill rate on market orders.
    # Since the blob protocol (for now) only handles
    # maker_order_id on matches we would not see
    # our market orders. Since we don't do it too often
    # this has not been changed.
    def onPlace(self, oid, side, price, size, otype):
        if self.debug:
            pprint('onPlace: %s' % oid)

        # If limit order, add to openOrders.
        # If market order, change BTC position now.
        if otype == "limit":
            order = Order(oid, side, price, size)
            self.openOrders[oid] = order
        elif otype == "market":
            self.position += size if side == "buy" else -size

    def onPlaceFail(self, reason):
        if self.debug:
            pprint('onPlaceFail: %s' % reason)

    def onPartialFill(self, order, remaining):
        if self.debug:
            pprint('onPartialFill: %s, with %0.4f remaining' % (str(order), remaining))

    def onCompleteFill(self, order):
        if self.debug:
            pprint('onCompleteFill: %s' % (str(order)))

    def getOpenSize(self):
        bidSize = 0.0
        askSize = 0.0
        for order in self.openOrders.values():
            if order.side == "buy":
                bidSize += order.size
            elif order.side == "sell":
                askSize += order.size
        return bidSize, askSize

    # Submit trade.
    def trade(self, size, side, price=None, otype="limit", product_id="BTC-USD", post_only=True):
        if otype == "limit" and not price:
            self.onPlaceFail("price not specified")

        # Prevent size from being too precise.
        size  = math.floor(1e8 * size) / 1e8

        # Fill order parameters.
        params = {"type":       otype,
                  "side":       side,
                  "price":      price,
                  "size":       size,
                  "product_id": product_id,
                  "stp":        "dc"}
        if otype == "limit":
            params["post_only"] = True

        # Send request. There's no need to trigger onPlace for market orders
        # since they will only occur with lockdown.
        success, res = self.rest.submitTrade(params)
        if success: 
            self.onPlace(res, side, price, size, otype)
        else: 
            self.onPlaceFail(res)

    # Prices and sizes cannot be too precise.
    # Therefore, ceiling ask prices and floor bid prices.
    # TODO: this is not general enough. The above method
    # should do this on its own in some way. Additionally
    # only sizes on asks are fixed, but not bids.
    def ask(self, size, price):
        price = math.ceil(100 * price) / 100.
        self.trade(size, "sell", price=price)

    def bid(self, size, price):
        price = math.floor(100 * price) / 100.
        self.trade(size, "buy", price=price)
##################################
#	    UNDER CONSTRUCTION		 #
##################################

from requests.auth import AuthBase
from book import BookClient, Order
from pprint import pprint

import hashlib
import time
import json
import hmac
import base64
import requests
import codecs


# Read authorization keys from file.
def readKeys(filename):
	with open(filename, "r") as f:
		return f.read().split("\n")

class RESTProtocol:
	def __init__(self, keys, debug=False):
		self.auth = Authorizer(keys)
		self.debug = debug

	def request(self, params):
		if self.debug:
			pprint("submitted trade: %s" % str(params))
		r = requests.post("https://api.exchange.coinbase.com/orders", json=params, auth=self.auth)
		if r.status_code == 200:
			return True, r.json()["id"]
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

class Strategy(BookClient):
	def __init__(self, rest, debug=False):
		self.rest = rest
		self.debug = debug
		self.openOrders = {}

	# BookClient methods.
	def add(self, oid, side, price, size):
		# Don't pass on adds since they come through on book setup.
		# self.update()
		pass

	def change(self, oid, side, newsize):
		self.update()

	def match(self, oid, side, price, size):
		# Look for our fills here!
		order = self.openOrders.get(oid)
		if order is not None:
			if self.debug:
				pprint("match on our order: %s" % oid)
			remaining = order.size - size
			if remaining <= 0:
				del self.openOrders[oid]
				self.onCompleteFill(order)
			else:
				self.openOrders[oid] = Order(oid, side, price, remaining)
				self.onPartialFill(order, remaining)
		self.update()

	def done(self, oid):
		self.update()
	# End of BookClient methods.

	# Main update loop.
	def update(self):
		pass

	def onPlace(self, oid, side, price, size):
		if self.debug:
			pprint('trade confirmed: %s' % oid)
		order = Order(oid, side, price, size)
		self.openOrders[oid] = order

	def onPlaceFail(self, reason):
		if self.debug:
			pprint('trade rejected: %s' % reason)

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

		# Fill order parameters.
		params = {"type":	    otype,
				  "side":		side,
				  "price":	    price,
				  "size":		size,
				  "product_id": product_id,
				  "stp":		"dc"}
		if otype == "limit":
			params["post_only"] = True

		# Send request.
		success, res = self.rest.request(params)
		if success: 
			self.onPlace(res, side, price, size)
		else: 
			self.onPlaceFail(res)

	def ask(self, size, price):
		self.trade(size, "sell", price=round(price, 2))

	def bid(self, size, price):
		self.trade(size, "buy", price=round(price, 2))
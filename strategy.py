'''
Author: Isaac Drachman
Date:   09/05/2015
Description:
Base class for strategies.
'''

from cbe import Authorizer, CBEProtocol, read_keys
from book import Book

class Strategy:
	def __init__(self, keyfile):
		auth = Authorizer(read_keys(keyfile))
		self.cbe = CBEProtocol(auth)

		# Setup control checks.
		self.secured = {"max_trade_size": 1.5,
 						"cross_allowed":  False}

 		# Monitor open orders.
		self.open_orders = {}

	def book(self):
		Book(self.cbe, self)

	def on_place(self, order_id):
		self.open_orders[r.json()["id"]] = size

	def on_place_fail(self, reason):
		pass

	def on_cancel(self, order_id):
		pass

	def on_cancel_fail(self, order_id, reason):
		pass

	def on_fill(self, order_id, filled):
		self.open_orders[order_id] -= filled
		if self.open_orders[order_id] <= 0.0:
			del self.open_orders[order_id]

	def update(self, book, msg):
		if msg["type"] == "match":
			order_id = msg["maker_order_id"]
			if self.open_orders.get(order_id) is not None:
				self.on_fill(order_id)

	# Control methods...

	# Cancel order with given UUID.
 	# Note: "Order already done" is message when order has been filled.
 	def cancel(self, order_id):
		r = self.cbe.cancel_order(order_id)
		if r.status_code == 200:
			self.on_cancel(order_id)
		else:                    
			self.on_cancel_fail(order_id, r.json()["message"])

	def get_open_size(self):
		return sum(self.open_orders.values())

	# Submit trade.
	def trade(self, size, side, price=None, otype="limit", product_id="BTC-USD", stp="dc", post_only=True):
		if size > self.secured["max_trade_size"]:
			self.on_place_fail("size exceeds max trade size")
		if not self.secured["cross_allowed"] and otype == "market":
			self.on_place_fail("market order will cross")
		elif not self.secured["cross_allowed"]:
			post_only = True
		if otype == "limit" and not price:
			self.on_place_fail("price not specified")

		# Fill order parameters.
		params = {"type":	    otype,
				  "side":		side,
				  "price":	    price,
				  "size":		size,
				  "product_id": product_id,
				  "stp":		stp}
		if otype == "limit":
			params["post_only"] = True

		# Send request.
		r = self.cbe.post_orders(params)
		if r.status_code == 200: 
			self.on_place(r.json()["id"])
		else: 
			self.on_place_fail(r.json()["message"])

	def ask(self, size, price):
		self.trade(size, "sell", price=price)

	def bid(self, size, price):
		self.trade(size, "buy", price=price)
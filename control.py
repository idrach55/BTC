'''
Author: Isaac Drachman
Date:   09/05/2015
Description:
Class to handle all order submission.
'''

import picklefix
from copy import copy

class Control:
	def __init__(self, cbe):
		self.cbe = cbe

		# Setup control checks.
 		self.secured = {"max_trade_size": 1.5,
 						"cross_allowed":  False}

 		# Track open orders.
 		self.open_orders = {}

 	# Cancel order with given UUID.
 	# Note: "Order already done" is message when order has been filled.
 	def cancel(self, order_id):
		r = self.cbe.cancel_order(order_id)
		if r.status_code == 200:
			self.remove_order(order_id)
			return (True, None)
		else:                    
			return (False, r.json()["message"])

	def remove_order(self, order_id):
		if self.open_orders.get(order_id) is None:
			return
		del self.open_orders[order_id]

	def drop_order_size(self, order_id, size):
		if self.open_orders.get(order_id) is None:
			return -1
		self.open_orders[order_id] -= size
		if self.open_orders[order_id] <= 0.0:
			del self.open_orders[order_id]
			return 0.0
		return self.open_orders[order_id]

	def get_open_size(self):
		return sum(self.open_orders.values())

	'''
	def cancel_all(self, pool=True):
		r = self.cbe.cancel_order("")
		new_orders = copy(self.open_orders)
		for order in self.open_orders:
			if order in r.json():
				new_orders.remove(order)
		self.open_orders = new_orders
		return True if len(self.open_orders) == 0 else False
	'''

	# Submit trade.
	def trade(self, size, side, price=None, otype="limit", product_id="BTC-USD", stp="dc", post_only=True):
		if size > self.secured["max_trade_size"]:
			return (False, None)
		if not self.secured["cross_allowed"] and otype == "market":
			return (False, "market order will cross")
		elif not self.secured["cross_allowed"]:
			post_only = True
		if otype == "limit" and not price:
			return (False, "price not specified")

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
			self.open_orders[r.json()["id"]] = size
			return (True, r.json()["id"])
		else: 
			return (False, r.json()["message"])

	def ask(self, size, price):
		return self.trade(size, "sell", price=price)

	def bid(self, size, price):
		return self.trade(size, "buy", price=price)



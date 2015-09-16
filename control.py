'''
Author: Isaac Drachman
Date:   09/05/2015
Description:
Class to handle all order submission.
'''

import picklefix

from multiprocessing import Pool
from copy import copy

class Control:
	def __init__(self, cbe):
		self.cbe = cbe

		# Setup control checks.
 		self.secured = {"max_trade_size": 1.5,
 						"cross_allowed":  False}

 		# Track open orders.
 		self.open_orders = []

 	# Cancel order with given UUID.
 	# Note: "Order already done" is message when order has been filled.
 	def cancel(self, order_id):
		r = self.cbe.cancel_order(order_id)
		if r.status_code == 200: 
			return (True, None)
		else:                    
			return (False, r.json()["message"])

	def cancelall(self):
		pool = Pool(processes = 8)
		returns = pool.map(self.poolcancel, self.open_orders)
		pool.close(); pool.join()
		new_open = copy(self.open_orders)
		for idx in range(len(self.open_orders)):
			if returns[idx][0] == True: 
				new_open.remove(self.open_orders[idx])
			elif returns[idx][1] == "Order already done": 
				new_open.remove(self.open_orders[idx])
		self.open_orders = new_open

	def poolcancel(self, order_id):
		success, msg = self.cancel(order_id)
		return success, msg

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
			self.open_orders.append(r.json()["id"])
			return (True, r.json()["id"])
		else: 
			return (False, r.json()["message"])

	def ask(self, size, price):
		return self.trade(size, "sell", price=price)

	def bid(self, size, price):
		return self.trade(size, "buy", price=price)



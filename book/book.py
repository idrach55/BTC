'''
Author: Isaac Drachman
Date:   09/27/2015
Description:
New class to handle a live (real-time) book. Slightly based on Coinbase's node.js library.
'''

from bintrees import FastRBTree
from bookbuilder import bookbuilder

class Book:
	def __init__(self, cbe, delay, strathandle=None):
		self.cbe = cbe
		self.strathandle = strathandle

		self.ordersById = {}
		self.bids = FastRBTree()
		self.asks = FastRBTree()

		bookbuilder(self, delay)

	# Order operations.
	def _getOrderById(self, orderId):
		try:
			return self.ordersById[orderId]
		except:
			return None

	def _getOrderId(self, order):
		try:
			return order["order_id"]
		except KeyError:
			return order["id"]

	def _getOrderSize(self, order):
		try:
			return float(order["size"])
		except KeyError:
			return float(order["remaining_size"])

	# Return red-black binary tree by side of book. 
	def _getOrderTree(self, side):
		return self.bids if side == "buy" else self.asks

	# Download orderbook via the REST api and add to trees.
	def begin(self):
		book = self.cbe.get_book(level=2).json()
		for bid in book["bids"]:
			order = {"id":    bid[2],
					 "side":  "buy",
					 "price": float(bid[0]),
					 "size":  float(bid[1])}
			self.add(order)
		for ask in book["asks"]:
			order = {"id":    ask[2],
					 "side":  "sell",
					 "price": float(ask[0]),
					 "size":  float(ask[1])}
			self.add(order)
		self.sequence = book["sequence"]

	# Orderbook messages...
	def add(self, order):
		order = {"id":    self._getOrderId(order),
				 "side":  order["side"],
				 "price": float(order["price"]),
				 "size":  self._getOrderSize(order)}
		tree = self._getOrderTree(order["side"])
		try:
			tree[order["price"]].append(order)
		except KeyError:
			tree[order["price"]] = [order]
		self.ordersById[order["id"]] = order

	def remove(self, orderId):
		order = self._getOrderById(orderId)
		if order is None:
			return

		tree = self._getOrderTree(order["side"])
		if len(tree[order["price"]]) > 1:
			tree[order["price"]].remove(order)
		else:
			del tree[order["price"]]
		del self.ordersById[orderId]

	def match(self, matched):
		price = float(matched["price"])
		size = float(matched["size"])

		tree = self._getOrderTree(matched["side"])
		assert(tree[price][0]["id"] == matched["maker_order_id"])

		tree[price][0]["size"] -= size
		self.ordersById[matched["maker_order_id"]] = tree[price][0]
		assert(tree[price][0]["size"] >= 0)

		if tree[price][0]["size"] == 0:
			self.remove(matched["maker_order_id"])

	def change(self, changed):
		order = self.ordersById[changed["order_id"]]
		old_size = float(changed["old_size"])
		new_size = float(changed["new_size"])

		tree = self._getOrderTree(changed["side"])
		assert(tree[order["price"]][tree[order["price"]].index(order)]["size"] == old_size)
		
		tree[order["price"]][tree[order["price"]].index(order)]["size"] = new_size
		self.ordersById[order["id"]] = tree[order["price"]][tree[order["price"]].index(order)]
	# End of orderbook messages.

	# Get functionality.
	def getBestBidPrice(self):
		return self._getOrderTree("buy").max_item()[0]

	def getBestAskPrice(self):
		return self._getOrderTree("sell").min_item()[0]

	def getBestBidQuote(self):
		price, orders = self._getOrderTree("buy").max_item()
		size = 0.0
		for order in orders:
			size += order["size"]
		return (price, size)

	def getBestAskQuote(self):
		price, orders = self._getOrderTree("sell").min_item()
		size = 0.0
		for order in orders:
			size += order["size"]
		return (price, size)

	def getMidPrice(self):
		return 0.5 * (self.getBestBidPrice() + self.getBestAskPrice())

	# Called by bookbuilder with message off queue.
	def update(self, msg):
		self.sequence = msg["sequence"]

		if msg["type"] == "open":
			self.add(msg)
		elif msg["type"] == "done":
			self.remove(msg["order_id"])
		elif msg["type"] == "match":
			self.match(msg)
		elif msg["type"] == "change":
			self.change(msg)

		# Relay to strategy.
		if self.strathandle is not None:
			return self.strathandle[0].update(self, self.strathandle[1])
		return True

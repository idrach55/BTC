from bintrees import FastRBTree
from collections import namedtuple
from blobprotocol import BlobClient
from pprint import pprint

import requests


Order = namedtuple('Order', ['oid', 'side', 'price', 'size'])

class InsufficientSizeForVWAP(Exception):
	pass

class BookClient:
	def onBookConnected(self, book):
		self.book = book

	def add(self, oid, side, price, size):
		raise NotImplementedError

	def change(self, oid, side, newsize):
		raise NotImplementedError

	def match(self, oid, side, price, size):
		raise NotImplementedError

	def done(self, oid):
		raise NotImplementedError

class Book(BlobClient):
	def __init__(self, protocol, debug=False):
		BlobClient.__init__(self, protocol)

		self.debug = debug
		self.clients = []

		self.ordersById = {}
		self.bids = FastRBTree()
		self.asks = FastRBTree()

	def addClient(self, client):
		self.clients.append(client)
		client.onBookConnected(self)

	# Download orderbook via the REST api and add to trees.
	def onOpen(self):
		r = requests.get('https://api.exchange.coinbase.com/products/BTC-USD/book', params={'level': 3})
		book = r.json()
		for bid in book["bids"]:
			self.add(bid[2], "buy", float(bid[0]), float(bid[1]))
		for ask in book["asks"]:
			self.add(ask[2], "sell", float(ask[0]), float(ask[1]))
		self.sequence = book["sequence"]

		if self.debug:
			pprint('downloaded (bids: %d, asks: %d)' % (len(self.bids), len(self.asks)))

	# Orderbook messages.
	def add(self, oid, side, price, size):
		order = Order(oid, side, price, size)
		tree = self._getOrderTree(order.side)
		try:
			tree[order.price].append(order)
		except KeyError:
			tree[order.price] = [order]
		self.ordersById[order.oid] = order

		if self.debug:
			pprint('added (%s, %s, $ %0.2f, %0.4f BTC)' % (oid, side, price, size))
		for client in self.clients:
			client.add(oid, side, price, size)

	def change(self, oid, side, newsize):
		order = self._getOrderById(oid)
		if order is None:
			return
		tree = self._getOrderTree(side)
		oidx = tree[order.price].index(order)

		tree[order.price][oidx] = Order(oid, side, order.price, newsize)
		self.ordersById[order.oid] = tree[order.price][oidx]

		if self.debug:
			pprint('changed (%s, %s, $ %0.2f, %0.2f BTC)' % (oid, side, order.price, newsize))
		for client in self.clients:
			client.change(oid, side, newsize)

	def match(self, oid, side, price, size):
		tree = self._getOrderTree(side)
		if self._getOrderById(oid) is None or tree[price][0].oid != oid:
			return
		tree[price][0] = Order(tree[price][0].oid, tree[price][0].side, tree[price][0].price, tree[price][0].size - size)
		self.ordersById[oid] = tree[price][0]
		if tree[price][0].size <= 0:
			self.done(oid)

		if self.debug:
			pprint('matched (%s, %s, $ %0.2f, %0.4f BTC)' % (oid, side, price, size))
		for client in self.clients:
			client.match(oid, side, price, size)

	def done(self, oid):
		order = self._getOrderById(oid)
		if order is None:
			return
		tree = self._getOrderTree(order.side)
		if len(tree[order.price]) > 1:
			tree[order.price].remove(order)
		else:
			del tree[order.price]
		del self.ordersById[oid]

		if self.debug:
			pprint('removed (%s)' % (oid,))
		for client in self.clients:
			client.done(oid)

	# Get functionality.
	def getBestBidPrice(self):
		if len(self.bids) == 0:
			return None
		return self._getOrderTree("buy").max_item()[0]

	def getBestAskPrice(self):
		if len(self.asks) == 0:
			return None
		return self._getOrderTree("sell").min_item()[0]

	def getBestBidQuote(self):
		if len(self.bids) == 0:
			return None, None
		price, orders = self._getOrderTree("buy").max_item()
		size = 0.0
		for order in orders:
			size += order.size
		return price, size

	def getBestAskQuote(self):
		if len(self.asks) == 0:
			return None
		price, orders = self._getOrderTree("sell").min_item()
		size = 0.0
		for order in orders:
			size += order.size
		return price, size

	def getMid(self):
		if len(self.bids) == 0 or len(self.asks) == 0:
			return None
		return 0.5 * (self.getBestBidPrice() + self.getBestAskPrice())

	def getVWAP(self, target):
		side = "buy" if target < 0 else "sell"
		tree = self._getOrderTree(side)
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
	def _getOrderById(self, oid):
		try:
			return self.ordersById[oid]
		except:
			return None

	# Return red-black binary tree by side of book. 
	def _getOrderTree(self, side):
		return self.bids if side == "buy" else self.asks

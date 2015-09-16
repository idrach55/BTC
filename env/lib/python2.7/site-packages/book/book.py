'''
Author: Isaac Drachman
Date:   09/05/2015
Description:
Class to handle a live (real-time) book.
'''

from bookbuilder import bookbuilder

class Book:
	def __init__(self, cbe, delay, strathandle=None):
		self.cbe = cbe
		self.strathandle = strathandle
		bookbuilder(self, delay)

	def convert_string_to_cents(self, strvalue):
		return int(100. * float(strvalue))

	def format_book(self):
		for side in ["bids", "asks"]:
			for idx in range(len(self.book[side])):
				self.book[side][idx][0] = self.convert_string_to_cents(self.book[side][idx][0])
				self.book[side][idx][1] = float(self.book[side][idx][1])

	def begin(self):
		response = self.cbe.get_book(level=2)
		self.book = response.json()
		self.format_book()
		self.sequence = self.book["sequence"]
		return self.sequence

	def adj_price_level(self, price, amt, side):
		bookside = self.book[side]
		condition = lambda idx: bookside[idx][0] > price if side == "bids" else bookside[idx][0] < price
		
		idx = 0
		while idx < len(bookside) and condition(idx):
			idx += 1

		if idx == len(bookside):
			bookside.append([price, amt])
		elif bookside[idx][0] == price:
			bookside[idx][1] += amt
			if bookside[idx][1] < 0.00000001:
				bookside.pop(idx)
		else:
			if idx == 0:
				bookside.insert(0, [price, amt])
			else:
				bookside.insert(idx, [price, amt])
		self.book[side] = bookside

	def update(self, msg):
		if msg["sequence"] < self.sequence:
			return True

		side = "bids"
		if msg["side"] == "sell": 
			side = "asks"
		price = 0
		if msg["type"] in ["match", "open", "change"]:
			price = self.convert_string_to_cents(msg["price"])
		if msg["type"] == "done" and msg["order_type"] == "limit":
			price = self.convert_string_to_cents(msg["price"])

		if msg["type"] == "match":
			self.adj_price_level(price, -float(msg["size"]), side)
		elif msg["type"] == "open":
			self.adj_price_level(price, float(msg["remaining_size"]), side)
		elif msg["type"] == "done" and msg["order_type"] == "limit" and float(msg["remaining_size"]) > 0.0:
			self.adj_price_level(price, -float(msg["remaining_size"]), side)	
		elif msg["type"] == "change":
			diff = msg["new_size"] - msg["old_size"]
			if (side == "asks" and price <= self.book[side][-1][0]) or (side == "bids" and price >= self.book[side][-1][0]):
				self.adj_price_level(price, diff, side)	

		self.sequence = msg["sequence"]

		if self.strathandle:
			strat, state = self.strathandle
			status, state = strat.update(self, state)
			self.strathandle = (strat, state)
			return status
		return True

	# GET functions.
	def get_best_price(self, side):
		return 0.01 * self.book[side][0][0]

	def get_best_size(self, side):
		return self.book[side][0][1]

	def get_best_quote(self, side):
		return (self.get_best_price(side), self.get_best_size(side))

	def get_spread(self):
		return self.get_best_price("asks") - self.get_best_price("bids")

	def get_mid_point(self):
		return 0.5 * (self.get_best_price("asks") + self.get_best_price("bids"))

	def get_vwap(self, side, throughprice):
		throughprice = int(100. * throughprice)
		bookside = self.book[side]
		condition = lambda idx: bookside[idx][0] >= throughprice if side == "bids" else bookside[idx][0] <= throughprice
		
		idx = 0
		weight = 0.0
		volume = 0.0 
		while idx < len(bookside) and condition(idx):
			weight += 0.01 * bookside[idx][0] * bookside[idx][1]
			volume += bookside[idx][1]
			idx += 1

		if idx == len(bookside):
			if side == "asks" and bookside[idx-1][0] < throughprice:
				return (False, None)

		return (True, weight / volume) 


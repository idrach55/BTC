'''
Author: Isaac Drachman
Date:   07/21/2015
Description:
Class to handle all input/output requests for orders and risk management.
'''

from cbe import Authorizer, CoinbaseExchange
from risky import Risky
import pandas as pd

class Trader:
	# Initialize connection to exchange, risk engine, and some control check parameters.
	def __init__(self):
		# Keys as provided by the exchange API.
		api_key    = # api key
		secret_key = # secret key
		passphrase = # passphrase

 		# Setup authorization and exchange connection.
 		auth = Authorizer(api_key, secret_key, passphrase)
 		self.cbe = CoinbaseExchange(auth)

 		# Setup risk engine.
 		self.risky = Risky(self.cbe)

 		# Setup control checks.
 		self.secured = {"max_trade_size": 0.5,
 						"cross_allowed":  False}

 	# Get the order book of given level (use levels 1 or 2 for polling).
 	def get_book(self, level=1):
 		r = self.cbe.get_book(level=level)
 		if r.status_code == 200:
 			return (True, pd.DataFrame(r.json()))
 		else:
 			return (False, None)

 	# Get most recent price.
 	def get_price(self):
 		r = self.cbe.get_ticker()
 		if r.status_code == 200:
 			return (True, float(r.json()["price"]))
 		else:
 			return (False, None)

 	# Get most recent trade.
 	def get_recent_trade(self):
 		r = self.cbe.get_trades()
 		if r.status_code == 200:
 			return (True, r.json()[0])
 		else:
 			return (False, None)

 	# Get midpoint on order book.
 	def get_mid(self):
 		success, book = self.get_book(level=1)
 		if not success:
 			return (False, None)
 		return (True, 0.5 * (float(book["bids"][0][0]) + float(book["asks"][0][0])))

 	# Get current spread.
 	def get_spread(self):
 		r = self.cbe.get_book(level=1)
 		if r.status_code == 200:
 			top_of_book = r.json()
 			return (True, float(top_of_book["asks"][0][0]) - float(top_of_book["bids"][0][0]))
 		else:
 			return (False, None)

 	# Cancel order with given UUID.
 	def cancel(self, order_id):
		r = self.cbe.cancel_order(order_id)
		if r.status_code == 200:
			return True
		else:
			return False

	# Cancel all open orders.
	# Note: there is a latency conern here since we need to 
	# pull all open orders before cancelling them. Consider
	# updating this to keep track of opened orders and leave
	# it to the exchange to fail on filled orders.
	def cancel_all(self):
		opens = self.risky.get_opens()
		if opens.empty:
			return True
		success = True
		for order_id in opens.id: 
			r = self.cancel(order_id)
			success = success and r
		return success

	# This method will ONLY work with limit orders.
	def trade(self, side, price, size, otype="limit", product_id="BTC-USD", stp="dc"):
		########################
		# Run control checks.
		if size > self.secured["max_trade_size"]:
			return(False, None)
		if self.would_cross(side, price) and not self.secured["cross_allowed"]:
 			return (False, None)
 		# End of control checks.
 		########################

 		# Fill order parameters.
		params = {"type":	    otype,
				  "side":		side,
				  "price":	    price,
				  "size":		size,
				  "product_id": product_id,
				  "stp":		stp}

		# Send request.
		r = self.cbe.post_orders(params)
		if r.status_code == 200:
			return (True, r.json())
		else:
			return (False, None)

	# Checks if order would cross the spread.
 	def would_cross(self, side, price):
 		s, r = self.get_book(level=1)
 		# If status is false, namely failed to receive order book.
 		if s == False:
 			# We don't have the information so fail this trade.
 			return True
 		# If we did receive information on book.
 		else:
			high_bid = float(r["bids"][0][0])
 			low_ask = float(r["asks"][0][0])
 			# We would cross if selling at or below highest bid.
	 		if side == "sell" and price <= high_bid:
	 			return True
	 		# We would cross if buying at or above lowest ask.
	 		elif side == "buy" and price >= low_ask:
	 			return True
	 		# Otherwise we are clear.
	 		else:
	 			return False
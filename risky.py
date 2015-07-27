'''
Author: Isaac Drachman
Date:   07/21/2015
Description:
Class to handle risk management.
'''

import pandas

class Risky:
	def __init__(self, cbe):
		self.cbe = cbe

	# Get recent 100 filled orders.
 	def get_fills(self):
 		r = self.cbe.get_fills()

 		if r.status_code == 200:
 			fills = pandas.DataFrame(r.json())
 			fills.size = map(lambda x: float(x), fills.size)
 			fills.price = map(lambda x: float(x), fills.price)
 			fills.fee = map(lambda x: float(x), fills.fee)

 			fills.size.iloc[fills.loc[fills.side == "sell"].index] *= -1
 			return fills
 		else:
 			return pandas.DataFrame()

 	# Get open orders.
 	def get_opens(self):
 		r = self.cbe.get_orders()

 		if r.status_code == 200:
 			opens = pandas.DataFrame(r.json())
 			if not opens.empty:
 				opens.size = map(lambda x: float(x), opens.size)
 				opens.price = map(lambda x: float(x), opens.price)
 			return opens
 		else:
 			return pandas.DataFrame()

 	# Get traded volume from last 100 filled trades.
 	def get_volume(self):
 		fills = self.get_fills()
 		if fills.empty:
 			return 0.0
 		return abs(fills.size).sum()

 	# Get bitcoin and dollar positions.
 	def get_positions(self):
 		r = self.cbe.get_accounts()
 		if r.status_code != 200:
 			return (False, None)
 		accounts = r.json()
 		a0 = accounts[0]
 		a1 = accounts[1]
 		btc = 0.0
 		usd = 0.0
 		if a0["currency"] == "USD":
 			usd = float(a0["balance"])
 			btc = float(a1["balance"])
 		elif a0["currency"] == "BTC":
 			btc = float(a0["balance"])
 			usd = float(a1["balance"])
 		return (True, {"BTC":round(btc, 8), "USD":round(usd, 5)})

 	# Mark to market some amount of bitcoin.
 	def m2m(self, amount):
 		# Get ticker from exchange.
 		r = self.cbe.get_ticker()
 		# If we didn't get the ticker, we cannot price.
 		if r.status_code == 200:
 			price = float(r.json()["price"])
 			return (True, amount * price)
 		else:
 			return (False, None)

 	# Mark to market btc position and add to usd position.
 	def get_position_m2m(self):
 		success, positions = self.get_positions()
 		if success:
 			success, m2m = self.m2m(positions["BTC"])
 			if success:
 				return (True, m2m + positions["USD"])
 		return (False, None)

 	# Get profit loss from a given previous marked to market position.
 	def get_pnl(self, m2m0):
 		success, m2m = self.get_position_m2m()
 		if success:
 			return (True, m2m - m2m0)
 		else:
 			return (False, None)
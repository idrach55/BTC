'''
Author: Isaac Drachman
Date:   09/05/2015
Description:
Class for handling risk management.
'''

class Risky:
	def __init__(self, cbe):
		self.cbe = cbe

	# GET functions.

	# Get current account balances.
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
 		else: return (False, None)

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
 		if success: return (True, m2m - m2m0)
 		else:       return (False, None)
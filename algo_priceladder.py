'''
Author: Isaac Drachman
Date:   07/21/2015
Description:
Simple first iteration price ladder market making algorithm.
'''

from trader import Trader
import numpy as np

class Algo:
	def __init__(self, trade_size=0.01, ladder=4):
		self.trader = Trader()

		# Algorithm parameters
		self.params = {"trade_size": trade_size,
		 			   "ladder":     ladder,
					   "increment":  0.01}

		# State variables.
		self.state = {"price": 0.0}

		# Auto-run strategy.
		self.strat()

	def strat(self):
		# Continually run strategy (use control-c in terminal to quit)
		while True:
			# Pull most recent trade.
			status, trade = self.trader.get_recent_trade()
			# If fail to pull trade, skip iteration.
			if not status:
				continue
			# Grab price of trade.
			price = float(trade["price"])
			# If price has updated.
			if self.state["price"] != price:
				# Attempt to cancel all trades.
				success = self.trader.cancel_all()
				# We will not proceed until all trades are cancelled.
				# Note: consider updating to track open orders and
				# only cancel those which are necessary and do so
				# directly, i.e. without cancel_all.
				while not success:
					success = self.trader.cancel_all()
				# Build ladder and submit, update price.
				xs, ys = self.build_ladder(price, trade["side"])
				self.submit_ladder(xs, ys)
				self.state["price"] = price

	def build_ladder(self, mid, side):
		# Get number of rungs on each side of spread.
		ladder = self.params["ladder"]
		# We start increments at 0 since one ladder will start
		# at most recent trade price.
		increments = np.array(range(0, ladder)) * self.params["increment"]
		midb = mid; mids = mid
		# If trade was a buy, attempt to make bid most recent trade price.
		# If trade was a sell, attempt to make ask most recent trade price.
		# Note: same price will fail if trade didn't clear entire order at price.
		if side == "buy":
			mids = mid + 0.01
		elif side == "sell":
			midb = mid - 0.01
		# Setup ladders from set points up to increments.
		xs = map(lambda x: round(x,2), mids + increments)
		ys = map(lambda y: round(y,2), midb - increments)
		return xs, ys

	def submit_ladder(self, xs, ys):
		# Submit price ladder.
		# Note: This code has been updated to handle price ladders of non-equal depth.
		# Also, print statements have been removed.
		max_length = max(len(ys),len(xs))
		for index in range(max_length):
			if index  < len(ys): 
				success, trade = self.trader.trade("buy", ys[index], self.params["trade_size"])
			if index < len(xs):
				success, trade = self.trader.trade("sell", xs[index], self.params["trade_size"])

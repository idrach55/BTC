'''
Author: Isaac Drachman
Date:   09/05/2015
Description:
Simple price ladder algorithm.
'''

import time

from util import picklefix
from cbe.strat import Strategy
from math import ceil, floor
from multiprocessing import Pool

# Default parameters.
params = {"widths": 	   	 [(7, 0.10), (9, 0.20), (11, 0.25), (13, 0.35)],
		  "offer_size":      1.0,
		  "update_thresh": 	 0.0001,
		  "position_target": 1.0}

class Helium(Strategy):
	def __init__(self, keyfile, params):
		# Start with default strategy.
		Strategy.__init__(self, keyfile)

		# Customize strategy.
		self.state["mid"] = None
		self.state["params"] = params

		# Start book.
		self.create_book()

	def update(self, book, state):
		mid = book.get_mid_point()
		if not state["mid"] or abs((mid - state["mid"])/state["mid"]) > state["params"]["update_thresh"]:
			print "\n[i] update: mid is %f"%mid
			time_a = time.clock()

			state["control"].cancelall()
			asks, bids = self.ladder(book, state)
			
			pool = Pool(processes = 8)
			ask_ids = pool.map(self.poolsubmitask, asks)
			bid_ids = pool.map(self.poolsubmitbid, bids)
			pool.close(); pool.join()
			
			state["control"].open_orders += [oid for oid in ask_ids if oid] + [oid for oid in bid_ids if oid]
			
			time_b = time.clock()
			print "[i] ladder submitted in %0.2f ms" % (1000. * (time_b - time_a))

			state["mid"] = mid
		return True, state

	def ladder(self, book, state):
		'''
		success, position = self.state["risky"].get_positions()
		if not success:
			return state
		posdiff = position["BTC"] - state["params"]["position_target"]
		'''

		mid = book.get_mid_point()
		bestask, bestbid = book.get_best_price("asks"), book.get_best_price("bids")

		asks, bids = [], []
		for spread, weight in state["params"]["widths"]:
			ask = 0.01 * ceil(100. * (mid + 0.005 * spread))
			bid = 0.01 * floor(100. * (mid - 0.005 * spread))

			if ask <= bestbid:
				ask = bestbid + 0.01
			if bid >= bestask:
				bid = bestask - 0.01

			bidsize = weight * state["params"]["offer_size"]
			asksize = weight * state["params"]["offer_size"]
			
			asks.append({"size": asksize, "price": ask, "state": state})
			bids.append({"size": bidsize, "price": bid, "state": state})
		return asks, bids

	def poolsubmitask(self, order_data):
		success, trade_id = order_data["state"]["control"].ask(order_data["size"], order_data["price"])
		if success: 
			print "[t] ask %f at %f" % (order_data["size"], order_data["price"])
			return trade_id

	def poolsubmitbid(self, order_data):
		success, trade_id = order_data["state"]["control"].bid(order_data["size"], order_data["price"])
		if success: 
			print "[t] bid %f at %f" % (order_data["size"], order_data["price"])
			return trade_id

if __name__ == "__main__":
	helium = Helium("../keys.txt", params)
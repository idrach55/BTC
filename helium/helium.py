'''
Author: Isaac Drachman
Date:   09/05/2015
Description:
Simple price ladder algorithm.
'''

import time
import sys

from util import picklefix
from cbe.strat import Strategy
from math import ceil, floor
from multiprocessing import Pool

class Helium(Strategy):
	def __init__(self, keyfile, params):
		# Start with default strategy.
		Strategy.__init__(self, keyfile)

		# Customize strategy.
		self.params = params
		self.state["mid"] = None

		# Start book.
		self.create_book()

	def update(self, book, state):
		mid = book.getMidPrice()
		if not state["mid"] or self.wasMidChangeSufficient(state["mid"], mid):
			print "\n%0.2f|%0.4f|%0.2f" % (book.getBestBidPrice(), mid, book.getBestAskPrice())

			time_a = time.clock()
			state["control"].cancelall()
			asks, bids = self.ladder(book, state)
			
			pool = Pool(processes = 8)
			ask_ids = pool.map(self.poolsubmitask, asks)
			bid_ids = pool.map(self.poolsubmitbid, bids)
			pool.close(); pool.join()
			
			state["control"].open_orders += [oid for oid in ask_ids if oid] + [oid for oid in bid_ids if oid]
			time_b = time.clock()

			print "submitted: %0.2f ms" % (1000. * (time_b - time_a))

			state["mid"] = mid
		return True, state

	def wasMidChangeSufficient(self, oldmid, newmid):
		return abs((newmid - oldmid) / oldmid) >= self.params["update_thresh"]

	def ladder(self, book, state):
		mid = book.getMidPrice()
		bestbid, bestask = book.getBestBidPrice(), book.getBestAskPrice()

		asks, bids = [], []
		for spread, weight in self.params["widths"]:
			ask = 0.01 * ceil(100. * (mid + 0.005 * spread))
			bid = 0.01 * floor(100. * (mid - 0.005 * spread))

			if ask <= bestbid:
				ask = bestbid + 0.01
			if bid >= bestask:
				bid = bestask - 0.01

			bidsize = weight * self.params["offer_size"]
			asksize = weight * self.params["offer_size"]
			
			asks.append({"size": asksize, "price": ask, "state": state})
			bids.append({"size": bidsize, "price": bid, "state": state})
		return asks, bids

	def poolsubmitask(self, order_data):
		success, trade_id = order_data["state"]["control"].ask(order_data["size"], order_data["price"])
		if success: 
			print "ask: %0.4f|%0.2f" % (order_data["size"], order_data["price"])
			return trade_id

	def poolsubmitbid(self, order_data):
		success, trade_id = order_data["state"]["control"].bid(order_data["size"], order_data["price"])
		if success: 
			print "bid: %0.4f|%0.2f" % (order_data["size"], order_data["price"])
			return trade_id

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print "usage: python helium.py [params-file]"
		quit()

	execfile(sys.argv[1])
	helium = Helium("../keys.txt", params)
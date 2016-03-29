import sys
import os

from strategy import Strategy


class Helium(Strategy):
	def __init__(self, keyfile, params):
		Strategy.__init__(self, keyfile)
		self.params = params
		self.filled = 0.0

		self.book()

	def update(self, book, msg):
		if len(self.control.open_orders) > 0 and msg["type"] == "match":
			remaining = self.control.drop_order_size(msg["maker_order_id"], float(msg["size"]))
			if remaining >= 0.0:
				open_size = self.control.get_open_size()
				print "%0.4f BTC filled at %0.2f" % (open_size - remaining, float(msg["price"]))
				self.filled += open_size - remaining
		
		vbid = book.getVWAP(-self.params["vwap"])
		vask = book.getVWAP( self.params["vwap"])
		vmid = 0.5 * (vbid + vask)
		sprd = (vask - vbid) * self.params["width"]

		sbid = round(vmid - 0.5*sprd, 2)
		sask = round(vmid + 0.5*sprd, 2)

		if self.control.get_open_size() > 0:
			return True

		if self.filled > 0:
			self.place(self.filled, sask, "ask")
		else:
			self.place(self.params["size"], sbid, "bid")
		return True

	def place(self, size, price, side):
		if side == "bid":
			success, message = self.control.bid(size, price)
		elif side == "ask":
			success, message = self.control.ask(size, price)
		if success: 
			print "%s %0.4f BTC at %0.2f" % (side, size, price)
		else:
			print "error with trade: %s" % message

if __name__ == "__main__":
	params = {"size":     0.01,
			  "vwap":     1.0,
	          "width":    0.5}
	helium = Helium("keys.txt", params)
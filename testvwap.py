'''
Author: Isaac Drachman
Date:   09/05/2015
Description:
Test book with strategy that publishes simple stats.
'''

import sys

from strategy import Strategy
from multiprocessing import Process, Pipe

class VWAPper(Strategy):
	def __init__(self, keyfile, conn):
		Strategy.__init__(self, keyfile)
		self.conn = conn
		self.book()

	def update(self, book):
		if self.conn.poll():
			self.conn.send(book.getVWAP(self.conn.recv()))
		return True

if __name__ == "__main__":
	parent, child = Pipe()
	p = Process(target = VWAPper, args=("keys.txt", child))
	p.start()

	while True:
		size = float(raw_input("desired size: "))
		parent.send(size)
		vwap = parent.recv()
		print "VWAP: %0.2f\tw/ fee: %0.2f" % (vwap, 1.0025*vwap)
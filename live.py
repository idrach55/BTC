'''
Author: Isaac Drachman
Date:   12/15/2015
Description:
Live plotting of market data.
'''

import sys
import time

from strategy import Strategy
from multiprocessing import Process, Pipe

import matplotlib
from matplotlib import pyplot as plt

tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),    
			 (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),    
			 (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),    
			 (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),    
			 (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)] 
tableau20 = [(r/255., g/255., b/255.) for r,g,b in tableau20]

class Plotter(Strategy):
	def __init__(self, keyfile, conn, vwaps):
		Strategy.__init__(self, keyfile)
		self.conn  = conn
		self.vwaps = vwaps
		self.book()
		
	def update(self, book, msg):
		Strategy.update(self, book, msg)

		if self.conn.poll():
			_ = self.conn.recv()
			mid = 0.5 * (book.getBestBid() + book.getBestAsk())
			asks = []
			bids = []
			for v in self.vwaps:
				asks.append(book.getVWAP(v))
				bids.append(book.getVWAP(-v))
			
			self.conn.send((mid, bids, asks))
		return True


if __name__ == "__main__":
	count = len(sys.argv) - 1
	vwaps = []
	for v in sys.argv[1:]:
		vwaps.append(float(v))

	plt.rcParams["axes.color_cycle"] = tableau20
	plt.rcParams["lines.linewidth"] = 2.5
	plt.rcParams["axes.grid"] = True
	plt.rcParams["axes.formatter.useoffset"] = False

	plt.ion()
	plt.show()

	parent, child = Pipe()
	p = Process(target=Plotter, args=("keys.txt", child, vwaps))
	p.start()

	mids = []
	vmid = [[] for v in vwaps]
	flag = False 
	while True:
		# tell strategy we want a data update
		parent.send("ack")

		# receive data update
		mid, bids, asks = parent.recv()
		mids.append(mid)
		mins = min(mids[len(mids)-100:])
		maxs = max(mids[len(mids)-100:])
		for idx, v in enumerate(vwaps): 
			vmid[idx].append(0.5 * (bids[idx] + asks[idx]))
			plt.plot(vmid[idx], c=tableau20[1+idx], label="%0.0f BTC vwap mid" % v)

			if min(vmid[idx][len(mids)-100:]) < mins:
				mins = min(vmid[idx][len(mids)-100:])
			if max(vmid[idx][len(mids)-100:]) > maxs:
				maxs = max(vmid[idx][len(mids)-100:])

		plt.plot(mids, c=tableau20[0], label="Top-of-Book mid")
		if len(mids) > 100:
			plt.xlim(len(mids)-100, len(mids))
		plt.ylim(mins-0.05, maxs+0.05)
		if not flag:
			plt.legend(loc="upper left")
		plt.draw()

		flag = True
		time.sleep(0.01)
import pandas
import sys

from time import time
from strategy import Strategy

class Data(Strategy):
	def __init__(self, keyfile, duration, resolution, vwaps, filename):
		Strategy.__init__(self, keyfile)

		self.duration = duration
		self.resolution = resolution
		self.filename = filename

		self.mktasks = []
		self.mktbids = []
		self.vwaps = vwaps
		self.vwapasks = [[] for v in self.vwaps]
		self.vwapbids = [[] for v in self.vwaps]
		self.timestamps = []

		self.timestamp = None
		self.start = time()

		self.book()

	def update(self, book, msg):
		now = time()
		if (now - self.start) >= self.duration:
			df = pandas.DataFrame()
			df["mktask"] = self.mktasks
			df["mktbid"] = self.mktbids
			for i, v in enumerate(self.vwaps):
				df["ask%d" % v] = self.vwapasks[i]
				df["bid%d" % v] = self.vwapbids[i]
			df["stamp"] = self.timestamps
			df.to_csv(self.filename, index=False)
			exit()
		elif self.timestamp is None or (now - self.timestamp) >= self.resolution:
			self.timestamp = now

			self.mktasks.append(book.getBestAsk())
			self.mktbids.append(book.getBestBid())
			for i, v in enumerate(self.vwaps):
				self.vwapasks[i].append(book.getVWAP(v))
				self.vwapbids[i].append(book.getVWAP(-v))
			self.timestamps.append(now)

			print "stamps processed: %d    \r" % len(self.timestamps),
			sys.stdout.flush()
		return True
			

if __name__ == "__main__":
	filename = sys.argv[1]
	duration = float(sys.argv[2])
	resolution = float(sys.argv[3])
	vwaps = map(lambda v: float(v), sys.argv[4:])
	data = Data("keys.txt", duration, resolution, vwaps, "data/" + filename)
'''
Author: Evgeny Yakimenko
Date: 	8/17/2015
Description:
Listens to CBE websocket feed
'''

import websocket, json, sys

# establish ws connection, pass callback functions
class Listener:
	def __init__(self, msg_callback, err_callback, cls_callback):
		self.msg_callback = msg_callback
		self.err_callback = err_callback
		self.cls_callback = cls_callback

		ws = websocket.WebSocketApp("wss://ws-feed.exchange.coinbase.com",
								on_message 	= self.on_message,
								on_error 	= self.on_error,
								on_close	= self.on_close,
								on_open		= self.on_open)

		ws.run_forever()

	def on_message(self, ws, msg):
		self.msg_callback(json.loads(msg))

	def on_error(self, ws, err):
		self.err_callback(json.loads(err))

	def on_close(self, ws):
		self.cls_callback()

	def on_open(self, ws):
		ws.send(json.dumps({"type":"subscribe", "product_id":"BTC-USD"}))

# dump executed trade feed to file
class TradeFeedDownload:
	def __init__(self, filename):
		self.filename = filename
		self.received = 0
		listener = Listener(self.msg_callback, self.err_callback, self.cls_callback)

	def msg_callback(self, msg):

		if msg["type"] == "match":
			self.received += 1
			
			with open(self.filename, 'a') as csv:
				csv.write("%s,%s,%s,%s,%s,%s\n" %
							(msg["trade_id"],
							 msg["sequence"],
							 msg["time"],
							 msg["size"],
							 msg["price"],
							 msg["side"]))

			print "[i] received: %d   \r" % self.received,
			sys.stdout.flush()

	def err_callback(self, err):
		print "\n[!] " + err

	def cls_callback(self):
		print "\n[i] closed"

# dump order feed to file
class OrderFeedDownload:
	def __init__(self, filename):
		self.filename = filename
		self.received = 0
		listener = Listener(self.msg_callback, self.err_callback, self.cls_callback)

	def msg_callback(self, msg):

		if msg["type"] == "open" or (msg["type"] == "done" and msg["reason"] == "canceled"):

			size = msg["remaining_size"]

		elif msg["type"] == "match":

			size = msg["size"]

		elif msg["type"] == "change":

			size = float(msg["old_size"]) - float(msg["new_size"])

		else:
			return

		with open(self.filename, 'a') as csv:
			csv.write("%s,%s,%s,%s,%s\n" % (msg["time"], msg["type"], msg["price"], size, msg["side"]))
			
			self.received += 1
			
		print "[i] received: %d   \r" % self.received,
		sys.stdout.flush()

	def err_callback(self, err):
		print "\n[!] " + err

	def cls_callback(self):
		print "\n[i] closed"


'''
# maintain live order book
class OrderBook:
	def __init__(self, level=3)
'''

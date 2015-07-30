import websocket, json, sys

class Listener:
	def __init__(self, msg_callback, err_callback, cls_callback):
		self.msg_callback = msg_callback
		self.err_callback = err_callback
		self.cls_callback = cls_callback

		ws = websocket.WebSocketApp("wss://ws-feed.exchange.coinbase.com",
								    on_message = self.on_message,
								    on_error   = self.on_error,
								    on_close   = self.on_close,
								    on_open    = self.on_open)
		ws.run_forever()

	def on_message(self, ws, msg):
		self.msg_callback(json.loads(msg))
	
	def on_error(self, ws, err):
		self.err_callback(json.loads(err))

	def on_close(self, ws):
		self.cls_callback()

	def on_open(self, ws):
		 ws.send(json.dumps({"type":"subscribe", "product_id":"BTC-USD"}))


class OrderFeedDownload:
	def __init__(self, filename):
		self.filename = filename
		self.received = 0
		listener = Listener(self.msg_callback, self.err_callback, self.cls_callback)

	def msg_callback(self, msg):
		mtime = msg["time"]
		mtype = None
		if msg["type"] == "received":
			mtype = msg["order_type"]
		elif msg["type"] == "done" and msg["remaining_size"] != 0.0:
			mtype = "cancel"
		if mtype != None:
			self.received += 1
			with open(self.filename, "a") as csv:
				csv.write("%s,%s\n" % (mtime, mtype))
			print "[i] received: %d   \r" % self.received,
			sys.stdout.flush()

	def err_callback(self, err):
		print err

	def cls_callback(self):
		print "[i] closed"
		
class TradeFeedDownload:
	def __init__(self, filename):
		self.filename = filename
		self.received = 0
		listener = Listener(self.msg_callback, self.err_callback, self.cls_callback)

	def msg_callback(self, msg):
		price = None
		size = None
		side = None
		if msg["type"] == "match":
			self.received += 1
			with open(self.filename, "a") as csv:
				csv.write("%s,%s,%s,%s\n" % (msg["time"], msg["side"], msg["price"], msg["size"]))
			print "[i] received: %d   \r" % self.received,
			sys.stdout.flush()

	def err_callback(self, err):
		print "[!] " + err

	def cls_callback(self):
		print "[i] closed" 

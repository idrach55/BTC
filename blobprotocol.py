import websocket
import json

from multiprocessing import Process, Queue

def wss(msgq):
	def on_message(ws, msg): 
		if msg is not None:
			msgq.put(json.loads(msg))

	def on_error(ws, err):   
		print "[!] wss error: " + json.loads(err)

	def on_close(ws):        
		print "[i] wss closed"

	def on_open(ws):       
		ws.send(json.dumps({"type":"subscribe", "product_id":"BTC-USD"}))

	ws = websocket.WebSocketApp("wss://ws-feed.exchange.coinbase.com", 
								on_message = on_message, 
								on_error   = on_error, 
								on_close   = on_close, 
								on_open    = on_open)
	ws.run_forever()	


class BlobProtocol:
	def __init__(self):
		pass

	def subscribe(self):
		msgq = Queue()
		p = Process(target = wss, args=(msgq,))
		p.start()

		self.begin()

		while True:
			msg = msgq.get()
			if msg["sequence"] <= self.sequence:
				continue
			self.update(msg)
		p.join()

	def begin(self):
		raise NotImplementedError

	def add(self, msg):
		raise NotImplementedError

	def change(self, msg):
		raise NotImplementedError

	def remove(self, msg):
		raise NotImplementedError

	def match(self, msg):
		raise NotImplementedError

	def update(self, msg):
		self.sequence = msg["sequence"]

		if msg["type"] == "open":
			self.add(msg)
		elif msg["type"] == "done":
			self.remove(msg["order_id"])
		elif msg["type"] == "match":
			self.match(msg)
		elif msg["type"] == "change":
			self.change(msg)
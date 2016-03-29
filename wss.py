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
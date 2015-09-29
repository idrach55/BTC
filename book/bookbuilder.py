'''
Author: Isaac Drachman
Date:   09/05/2015
Description:
Class to handle web socket messages regarding the live book.
'''

import websocket
import json

from multiprocessing import Process, Queue
from time import clock, sleep

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

def bookbuilder(book, delay):
	msgq = Queue()
	p = Process(target = wss, args=(msgq,))
	p.start()
	
	sleep(delay)

	book.begin()
	msg = msgq.get()
	while msg["sequence"] < book.sequence: 
		msg = msgq.get()

	while True:
		msg = msgq.get()
		if msg["sequence"] < book.sequence:
			continue
		if not book.update(msg):
			break
	p.join()
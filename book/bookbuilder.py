'''
Author: Isaac Drachman
Date:   09/05/2015
Description:
Class to handle web socket messages regarding the live book.
'''

import websocket
import json

from multiprocessing import Process, Queue
from time import clock

def wss(msgq):
	def on_message(ws, msg): 
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
	time_a = clock()
	msgq = Queue()
	p = Process(target = wss, args=(msgq,))
	p.start()
	begun = False
	while True:
		time_b = clock()
		if time_b - time_a < delay:
			continue
		elif not begun:
			seq = book.begin()
			msg = msgq.get()
			while msg["sequence"] < seq: 
				msg = msgq.get()
			begun = True

		msg = msgq.get()
		if not book.update(msg):
			break
	p.join()
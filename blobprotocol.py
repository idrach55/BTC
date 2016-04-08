'''
Author: Isaac Drachman
Description:
Class implementations for BlobProtocol and its client class BlobClient.
'''

'''I don't claim to have any idea how autobahn works but it's good.'''
from autobahn.twisted.websocket import WebSocketClientProtocol
from pprint import pprint

import json


'''
Client for BlobProtocol. All message types from the exchange websocket, i.e.
add, change, match, and done are forwarded here in addition to onOpen:
when the websocket is opened, and onSequenceGap: when the protocol detects 
it missed a message off the exchange. 
'''
class BlobClient:
    def __init__(self, protocol):
        protocol.client = self
        self.sequence = 0

    def on_open(self):
        raise NotImplementedError

    def add(self, oid, side, price, size):
        raise NotImplementedError

    def change(self, oid, side, newsize):
        raise NotImplementedError

    def match(self, oid, side, price, size):
        raise NotImplementedError

    def done(self, oid):
        raise NotImplementedError

    def on_sequence_gap(self):
        raise NotImplementedError

'''
BlobProtocol is the inlet for all market data off the Coinbase exchange
websocket. It inherits from an autobahn/twisted class to get some nice
qualities to it. It opens, sends a subscribe to the exchange for the 
bitcoin/US dollar pair, then is fed through onMessage.
'''
class BlobProtocol(WebSocketClientProtocol):
    # Once the connection is open, hit the exchange with a subscribe.
    def onOpen(self):
        msg = json.dumps({'type': 'subscribe', 'product_id': 'BTC-USD'})
        self.sendMessage(msg.encode('utf-8'), isBinary=False)
        self.client.on_open()

    # All exchange websocket methods come through here in json.
    def onMessage(self, payload, isBinary):
        if not isBinary:
            msg = json.loads(payload.decode('utf8'))
            # Each message has a sequence. We expect the client
            # to figure out what sequence is proper. For example:
            # the book will download a level-3 over REST and get
            # an initial sequence there.
            if msg["sequence"] <= self.client.sequence:
                # If there's a gap we could have lost vital data.
                # Forward this on to the client.
                self.client.on_sequence_gap()
                return
            # Otherwise update sequence.
            self.client.sequence = msg["sequence"]
            # Forward messages internally based on type.
            if msg["type"] == "open":
                self.add(msg)
            elif msg["type"] == "change":
                self.change(msg)
            elif msg["type"] == "match":
                self.match(msg)
            elif msg["type"] == "done":
                self.done(msg)

    # Order is added to the book.
    def add(self, msg):
        oid   = self._get_order_id(msg)
        side  = msg["side"]
        price = float(msg["price"])
        size  = self._get_order_size(msg)
        self.client.add(oid, side, price, size)

    # Order is changed on the book.
    def change(self, msg):
        oid  = msg["order_id"]
        side = msg["side"]
        size = msg["new_size"]
        self.client.change(oid, side, size)

    # Orders (one taker, one maker) are matched.
    def match(self, msg):
        oid   = msg["maker_order_id"]
        side  = msg["side"]
        price = float(msg["price"])
        size  = float(msg["size"])
        self.client.match(oid, side, price, size)

    # Order is done, ex. cancelled.
    def done(self, msg):
        oid = msg["order_id"]
        self.client.done(oid)

    def _get_order_id(self, order):
        try:
            return order["order_id"]
        except KeyError:
            return order["id"]

    def _get_order_size(self, order):
        try:
            return float(order["size"])
        except KeyError:
            return float(order["remaining_size"])

# Barebones startup logic for autobahn.
if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')
    factory.protocol = BlobProtocol
    connectWS(factory)
    reactor.run()
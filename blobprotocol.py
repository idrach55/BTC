from autobahn.twisted.websocket import WebSocketClientProtocol
from pprint import pprint

import json


class BlobClient:
    def __init__(self, protocol):
        protocol.client = self
        self.sequence = 0

    def onOpen(self):
        raise NotImplementedError

    def add(self, oid, side, price, size):
        raise NotImplementedError

    def change(self, oid, side, newsize):
        raise NotImplementedError

    def match(self, oid, side, price, size):
        raise NotImplementedError

    def done(self, oid):
        raise NotImplementedError

class BlobProtocol(WebSocketClientProtocol):
    def onOpen(self):
        msg = json.dumps({'type': 'subscribe', 'product_id': 'BTC-USD'})
        self.sendMessage(msg.encode('utf-8'), isBinary=False)
        self.client.onOpen()

    def onMessage(self, payload, isBinary):
        if not isBinary:
            msg = json.loads(payload.decode('utf8'))
            if msg["sequence"] <= self.client.sequence:
                return
            if msg["type"] == "open":
                self.add(msg)
            elif msg["type"] == "change":
                self.change(msg)
            elif msg["type"] == "match":
                self.match(msg)
            elif msg["type"] == "done":
                self.done(msg)

    def add(self, msg):
        oid   = self._getOrderId(msg)
        side  = msg["side"]
        price = float(msg["price"])
        size  = self._getOrderSize(msg)
        self.client.add(oid, side, price, size)

    def change(self, msg):
        oid  = msg["order_id"]
        side = msg["side"]
        size = msg["new_size"]
        self.client.change(oid, side, size)

    def match(self, msg):
        oid   = msg["maker_order_id"]
        side  = msg["side"]
        price = float(msg["price"])
        size  = float(msg["size"])
        self.client.match(oid, side, price, size)

    def done(self, msg):
        oid = msg["order_id"]
        self.client.done(oid)

    def _getOrderId(self, order):
        try:
            return order["order_id"]
        except KeyError:
            return order["id"]

    def _getOrderSize(self, order):
        try:
            return float(order["size"])
        except KeyError:
            return float(order["remaining_size"])

'''
if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')
    factory.protocol = BlobProtocol
    connectWS(factory)
    reactor.run()
'''
'''
Author: Isaac Drachman
Description:
Class implementations for BlobProtocol and its client class BlobClient.
'''

from autobahn.twisted.websocket import WebSocketClientProtocol
from twisted.internet import reactor
from pprint import pprint

import json


class BlobClient:
    def __init__(self, protocol):
        '''
        Constructs a blob client to which all add, change, match, and
        done messages which are forwarded from the web socket.

        :param protocol: blob protocol to which this will be a client
        '''
        protocol.client = self
        self.sequence = 0

    def on_open(self):
        '''
        The web socket was opened.
        '''
        raise NotImplementedError

    def add(self, oid, side, price, size):
        '''
        An order was added to the book.
        '''
        raise NotImplementedError

    def change(self, oid, side, newsize):
        '''
        An order was changed on the book.
        '''
        raise NotImplementedError

    def match(self, oid, side, price, size):
        '''
        An order was matched.
        '''
        raise NotImplementedError

    def done(self, oid):
        '''
        An order was dropped from the book.
        '''
        raise NotImplementedError

    def on_sequence_gap(self):
        '''
        A gap in web socket messages was detected.
        '''
        raise NotImplementedError

class BlobProtocol(WebSocketClientProtocol):
    '''
    BlobProtocol is the inlet for all market data off the GDAX
    websocket. It inherits from an autobahn/twisted class to get some nice
    qualities to it. It opens, sends a subscribe to the exchange for the
    bitcoin/US dollar pair, then is fed through onMessage.
    '''

    def onOpen(self):
        '''
        Once the connection is open, hit the exchange with a subscribe.
        '''
        msg = json.dumps({'type': 'subscribe', 'product_id': 'BTC-USD'})
        self.sendMessage(msg.encode('utf-8'), isBinary=False)
        reactor.callLater(1.0, self.client.on_open)

    def onMessage(self, payload, isBinary):
        '''
        All exchange websocket messages come through here in json.

        :param payload: message data
        :param isBinary: is the message in binary
        :return: void
        '''
        if not isBinary:
            # Skip messages until the book has been downloaded over REST.
            if self.client.sequence is None:
                return

            msg = json.loads(payload.decode('utf8'))
            if msg["sequence"] <= self.client.sequence:
                return
            if msg["sequence"] > self.client.sequence + 1:
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

    def add(self, msg):
        '''
        An order was added to the book.
        '''
        oid   = self._get_order_id(msg)
        side  = msg["side"]
        price = float(msg["price"])
        size  = self._get_order_size(msg)
        self.client.add(oid, side, price, size)

    def change(self, msg):
        '''
        An order was changed on the book.
        '''
        oid  = msg["order_id"]
        side = msg["side"]
        size = msg["new_size"]
        self.client.change(oid, side, size)

    def match(self, msg):
        '''
        An order was matched.
        '''
        oid   = msg["maker_order_id"]
        side  = msg["side"]
        price = float(msg["price"])
        size  = float(msg["size"])
        self.client.match(oid, side, price, size)

    def done(self, msg):
        '''
        An order was dropped from the book.
        '''
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

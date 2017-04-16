'''
Author: Isaac Drachman
Description:
Implementations for BlobProtocol and its client BlobClient.
'''

from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory
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
        try:
            protocol.clients.append(self)
        except:
            protocol.clients = [self]
        self.sequence = 0

    def on_open(self):
        '''
        The web socket was opened.
        '''
        raise NotImplementedError

    def add(self, oid, side, price, size, product_id):
        '''
        An order was added to the book.
        '''
        raise NotImplementedError

    def change(self, oid, side, newsize, product_id):
        '''
        An order was changed on the book.
        '''
        raise NotImplementedError

    def match(self, oid, side, price, size, product_id):
        '''
        An order was matched.
        '''
        raise NotImplementedError

    def done(self, oid, product_id):
        '''
        An order was dropped from the book.
        '''
        raise NotImplementedError

    def on_sequence_gap(self, product_id):
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
        self.product_ids = self.factory.product_ids
        msg = json.dumps({'type': 'subscribe', 'product_ids': self.product_ids})
        self.sendMessage(msg.encode('utf-8'), isBinary=False)
        for client in self.clients:
            reactor.callLater(1.0, client.on_open)

    def onMessage(self, payload, isBinary):
        '''
        All exchange websocket messages come through here in json.

        :param payload: message data
        :param isBinary: is the message in binary
        :return: void
        '''
        if not isBinary:
            # Skip messages until the book has been downloaded over REST.
            # if self.client.sequence is None:
            #    return

            msg = json.loads(payload.decode('utf8'))
            # if msg["sequence"] <= self.client.sequence:
            #    return
            # if msg["sequence"] > self.client.sequence + 1:
            #    self.client.on_sequence_gap()
            #    return
            # Otherwise update sequence.
            # self.client.sequence = msg["sequence"]
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
        pid   = msg['product_id']
        for client in self.clients:
            client.add(oid, side, price, size, pid)

    def change(self, msg):
        '''
        An order was changed on the book.
        '''
        oid  = msg["order_id"]
        side = msg["side"]
        size = msg["new_size"]
        pid  = msg['product_id']
        for client in self.clients:
            client.change(oid, side, size, pid)

    def match(self, msg):
        '''
        An order was matched.
        '''
        oid   = msg["maker_order_id"]
        side  = msg["side"]
        price = float(msg["price"])
        size  = float(msg["size"])
        pid   = msg['product_id']
        for client in self.clients:
            client.match(oid, side, price, size, pid)

    def done(self, msg):
        '''
        An order was dropped from the book.
        '''
        oid = msg["order_id"]
        pid = msg['product_id']
        for client in self.clients:
            client.done(oid, pid)

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

class BlobProtocolFactory(WebSocketClientFactory):
    protocol = BlobProtocol

    def __init__(self, url, product_ids=['BTC-USD']):
        WebSocketClientFactory.__init__(self, url)
        self.product_ids = product_ids

# Barebones startup logic for autobahn.
if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')
    factory.protocol = BlobProtocol
    connectWS(factory)
    reactor.run()

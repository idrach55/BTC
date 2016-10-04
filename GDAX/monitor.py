from autobahn.twisted.websocket import WebSocketClientFactory, connectWS
from twisted.python import log
from twisted.internet import reactor
from pprint import pprint
from time import time

import sys

from blobprotocol import BlobProtocol
from volmonitor import VolMonitor
from book import Book, InsufficientSizeForVWAP
from strategy import RESTProtocol, Strategy, read_keys


class Monitor(Strategy):
    def __init__(self, rest):
        Strategy.__init__(self, rest)

    # Main update loop.
    def update(self):
        if not self.enabled:
            return

    def match(self, oid, side, price, size):
        pprint('%s of %0.4f at $ %0.2f'%(side, size, price))

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory('wss://ws-feed.exchange.coinbase.com')
    factory.protocol = BlobProtocol

    # Setup params from params.py.
    rest = RESTProtocol(read_keys('keys.txt'), debug=True)
    mon = Monitor(rest)
    mon.enabled = False

    bb = Book(factory.protocol, debug=False)
    bb.add_client(mon)

    connectWS(factory)

    reactor.callLater(5.0, mon.enable)
    reactor.run()

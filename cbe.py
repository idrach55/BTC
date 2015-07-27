'''
Author: Isaac Drachman
Date:   07/21/2015
Description:
Class to handle exchange connectivity.
'''

import json, hmac, hashlib, time, requests, base64
from requests.auth import AuthBase

# Authorizes coinbase exchange calls.
class Authorizer(AuthBase):
	# Initialize authorizer with keys and passphrase.
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    # This method is called by the requests when authentication is needed.
    def __call__(self, request):
        timestamp = str(time.time())
        message = timestamp + request.method + request.path_url + (request.body or "")
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message, hashlib.sha256)
        signature_b64 = signature.digest().encode("base64").rstrip("\n")

        request.headers.update({
            "CB-ACCESS-SIGN": signature_b64,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-PASSPHRASE": self.passphrase,
        })
        return request

# Connects to coinbase exchange.
class CoinbaseExchange(object):
	# Initialize with api url and instance of authorizer class.
    def __init__(self, auth):
        self.api_url = "https://api.exchange.coinbase.com/"
        self.auth = auth

    # Get functionality.
    # Note: not all methods will require authentication but
    # instance will be passed regardless.
    def get(self, method, params={}):
        url = {
            "book"     : "products/BTC-USD/book",
            "ticker"   : "products/BTC-USD/ticker",
            "trades"   : "products/BTC-USD/trades",
            "stats"    : "products/BTC-USD/stats",
            "time"     : "time",
            "fills"    : "fills",
            "orders"   : "orders",
            "accounts" : "accounts"
        }
        r = requests.get(self.api_url + url[method], params=params, auth=self.auth)
        return r

    # Post functionality.
    def post(self, method, params={}):
        url = {
            "orders" : "orders"
        }
        r = requests.post(self.api_url + url[method], json=params, auth=self.auth)
        return r

    # Cancel order, utilizes the delete request.
    def cancel_order(self, order_id):
        r = requests.delete(self.api_url + "orders/"+order_id, auth=self.auth)
        return r

    def get_ticker(self):
        return self.get("ticker")
        
    def get_trades(self):
        return self.get("trades")

    def get_time(self):
        return self.get("time")

    def get_stats(self):
        return self.get("stats")

    def get_book(self, level=1):
        return self.get("book", params={"level":level})

    def get_fills(self):
        return self.get("fills")

    def get_orders(self):
        return self.get("orders")

    def get_accounts(self):
        return self.get("accounts")

    def post_orders(self, params):
        return self.post("orders", params=params)

##################################
#	    UNDER CONSTRUCTION		 #
##################################

from requests.auth import AuthBase
from book import BookClient

import hashlib
import time
import json
import hmac


# Read authorization keys from file.
def read_keys(filename):
	with open(filename, "r") as f:
		return f.read().split("\n")

# Authorizes coinbase exchange calls.
class Authorizer(AuthBase):
	# Initialize authorizer with keys and passphrase.
    def __init__(self, keys):
        self.api_key, self.secret_key, self.passphrase = keys

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

class Strategy(BookClient):
	def __init__(self, auth):
		self.auth = auth

	# Submit trade.
	def trade(self, size, side, price=None, otype="limit", product_id="BTC-USD", post_only=True):
		if otype == "limit" and not price:
			self.on_place_fail("price not specified")

		# Fill order parameters.
		params = {"type":	    otype,
				  "side":		side,
				  "price":	    price,
				  "size":		size,
				  "product_id": product_id,
				  "stp":		"dc"}
		if otype == "limit":
			params["post_only"] = True

		# Send request.
		r = requests.post("https://api.exchange.coinbase.com/orders", json=params, auth=self.auth)
		if r.status_code == 200: 
			self.on_place(r.json()["id"])
		else: 
			self.on_place_fail(r.json()["message"])

	def ask(self, size, price):
		self.trade(size, "sell", price=price)

	def bid(self, size, price):
		self.trade(size, "buy", price=price)
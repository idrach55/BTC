import numpy as np
import requests
from scipy.stats import norm
from collections import namedtuple
from datetime import datetime
from scipy.optimize import brentq


def loop():
    pr = Protocol()
    while True:
        comm = input('> ').split(' ')
        opt = Option(comm[1])
        if len(comm) == 4:
            spt = float(comm[2])
            vol = float(comm[3])
        else:
            spt = pr.get_index()
            vol = float(comm[2])
        if comm[0] == 'val':
            print('$ %0.2f (%0.4f delta)' % (opt.value(spt, vol, 0), opt.delta(spt, vol, 0)))
        elif comm[0] == 'imp':
            print('%0.2f%%' % (100*opt.implied(spt, 0, vol)))

class Manager:
    def __init__(self):
        self.pr = Protocol()

        instruments = self.pr.get_instruments(kind='option')
        self.options = {}
        for inst in instruments:
            self.options[inst] = Option(inst)

    def get_all_for_tenor(self, tenor):
        return [inst for inst in self.options.values() if inst.inst[4:11] == tenor]

    def compute_reversal_longs(self, tenor):
        prices = self.get_prices(tenor)
        strikes = []
        for ticker in prices.keys():
            if float(ticker[-5:-2]) not in strikes:
                strikes.append(float(ticker[-5:-2]))
        return {strike: strike + self.pr.get_index()*(prices['BTC-%s-%0.0f-C'%(tenor, strike)][1] - \
                        prices['BTC-%s-%0.0f-P'%(tenor, strike)][0]) for strike in strikes}

    def compute_reversal_shorts(self, tenor):
        prices = self.get_prices(tenor)
        strikes = []
        for ticker in prices.keys():
            if float(ticker[-5:-2]) not in strikes:
                strikes.append(float(ticker[-5:-2]))
        return {strike: strike - self.pr.get_index()*(prices['BTC-%s-%0.0f-P'%(tenor, strike)][1] - \
                        prices['BTC-%s-%0.0f-C'%(tenor, strike)][0]) for strike in strikes}

    def get_mids(self, tenor):
        instruments = self.get_all_for_tenor(tenor)
        mids = {opt.inst: self.pr.get_orderbook(opt.inst).get_mid() for opt in instruments}
        return mids

    def get_prices(self, tenor):
        instruments = self.get_all_for_tenor(tenor)
        prices = {}
        for opt in instruments:
            bid = self.pr.get_orderbook(opt.inst).get_best_bid()
            ask = self.pr.get_orderbook(opt.inst).get_best_ask()
            if bid is not None and ask is not None:
                prices[opt.inst] = (bid,ask)
        return prices

    def get_implieds(self, tenor):
        instruments = self.get_all_for_tenor(tenor)
        spot = self.pr.get_index()
        fwrd = self.pr.get_orderbook('BTC-%s'%tenor).get_mid()
        implieds = {opt.inst: opt.implied(fwrd, 0.00, spot*self.pr.get_orderbook(opt.inst).get_mid()) for opt in instruments}
        return implieds


class Book:
    def __init__(self, bids, asks):
        self.bids = bids
        self.asks = asks

    def get_best_bid(self):
        return self.bids[0]['price'] if len(self.bids) > 0 else None

    def get_best_ask(self):
        return self.asks[0]['price'] if len(self.asks) > 0 else None

    def get_best_bid_quote(self):
        return self.bids[0]['price'], self.bids[0]['quantity']

    def get_best_ask_quote(self):
        return self.asks[0]['price'], self.asks[0]['quantity']

    def get_mid(self):
        return (self.get_best_bid() + self.get_best_ask())/2


class Option:
    def __init__(self, inst):
        self.inst = inst
        self.K = float(inst[inst[inst.find('-')+1:].find('-')+inst.find('-')+2:-2])
        date = inst[inst.find('-')+1:inst[inst.find('-')+1:].find('-')+inst.find('-')+1]
        self.T = (datetime.strptime(date+':11','%d%b%y:%H') - datetime.now()).total_seconds()/(60.*60*24*365)

    def bs_d1(self, S, sigma, r):
        return (np.log(S/self.K) + (r + sigma**2/2)*(self.T)) / (sigma*np.sqrt(self.T))

    def value(self, S, sigma, r):
        d1 = self.bs_d1(S, sigma, r)
        d2 = d1 - sigma*np.sqrt(self.T)
        call = norm.cdf(d1)*S - norm.cdf(d2)*self.K*np.exp(-r*self.T)
        put  = norm.cdf(-d2)*self.K*np.exp(-r*self.T) - norm.cdf(-d1)*S
        return call if self.inst[-1] == 'C' else put

    def delta(self, S, sigma, r):
        d1 = self.bs_d1(S, sigma, r)
        return norm.cdf(d1) if self.inst[-1] == 'C' else norm.cdf(d1) - 1

    def gamma(self, S, sigma, r):
        d1 = self.bs_d1(S, sigma, r)
        return norm.pdf(d1) / (S * sigma * np.sqrt(self.T))

    def theta(self, S, sigma, r):
        d1 = self.bs_d1(S, sigma, r)
        d2 = d1 - sigma*np.sqrt(self.T)
        a = -S*norm.pdf(d1)*sigma / (2*np.sqrt(self.T))
        b = r*self.K*np.exp(-r*self.T)
        return (a - b*norm.cdf(d2))/360. if self.inst[-1] == 'C' else (a + b*norm.cdf(-d2))/360.

    def vega(self, S, sigma, r):
        d2 = self.bs_d1(S, sigma, r) - sigma*np.sqrt(self.T)
        a = self.K*self.T*np.exp(-r*self.T)
        return a*norm.cdf(d2)/100. if self.inst[-1] == 'C' else -a*norm.cdf(-d2)/100.

    def implied(self, S, r, price):
        return brentq(lambda sigma: price - self.value(S, sigma, r), -1e-9, 2.)


class Protocol:
    def __init__(self, keys=(None,None)):
        self.api_key, self.secret_key = keys
        self.url = 'https://deribit.com/api/v1'

    def get_instruments(self, kind='all'):
        r = requests.get(self.url + '/public/getinstruments')
        results = r.json()['result']
        if kind == 'all':
            return results
        else:
            return [res['instrumentName'] for res in results if res['kind'] == kind]

    def get_index(self):
        r = requests.get(self.url + '/public/index')
        return r.json()['result']['btc']

    def get_orderbook(self, inst):
        r = requests.get(self.url + '/public/getorderbook?instrument=%s' % inst)
        return Book(r.json()['result']['bids'], r.json()['result']['asks'])

    def buy(self, inst, size, price):
        params = {'instrument': inst,
                  'quantity':   size,
                  'price':      price}
        r = requests.post(self.url + '/private/buy', json=params)
        return r

'''
class Authorizer(AuthBase):
    # Initialize authorizer with keys and passphrase.
    def __init__(self, keys):
        self.api_key, self.secret_key = keys

    # This method is called by the requests when authentication is needed.
    def __call__(self, request):
        timestamp = str(time.time())
        message = '_=%s&_ackey=%s&_acsec=%s&_action=%s&instrument=%s&price=%s&quantity=%s'

        hmac_key = base64.b64encode(self.secret_key)
        signature = hmac.new(hmac_key, message.encode('utf-8'), hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest())

        request.headers.update({
            'x-deribit-sig': signature_b64,
            'Content-Type': 'application/json'
        })
        return request


def read_keys(filename):
    with open(filename, "r") as f:
        return f.read().split("\n")[:2]
'''

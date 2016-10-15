import numpy as np
import requests
from scipy.stats import norm
from collections import namedtuple
from datetime import datetime


class Manager:
    def __init__(self):
        self.pr = Protocol()

        instruments = self.pr.get_instruments(kind='option')
        self.options = {}
        for inst in instruments:
            self.options[inst] = Option(inst)

    def get_all_for_tenor(self, tenor):
        return [inst for inst in self.options.values() if inst.inst[4:11] == tenor]


class Book:
    def __init__(self, bids, asks):
        self.bids = bids
        self.asks = asks

    def get_best_bid(self):
        return self.bids[0]['price']

    def get_best_ask(self):
        return self.asks[0]['price']

    def get_best_bid_quote(self):
        return self.bids[0]['price'], self.bids[0]['quantity']

    def get_best_ask_quote(self):
        return self.asks[0]['price'], self.asks[0]['quantity']

    def get_mid(self):
        return (self.get_best_bid() + self.get_best_ask())/2


class Option:
    def __init__(self, inst):
        self.inst = inst
        self.K = float(inst[-5:-2])
        self.T = (datetime.strptime(inst[4:11],'%d%b%y') - datetime.now()).days/360.

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


class Protocol:
    def __init__(self):
        self.public = 'https://deribit.com/api/v1/public'

    def get_instruments(self, kind='all'):
        r = requests.get(self.public + '/getinstruments')
        results = r.json()['result']
        if kind == 'all':
            return results
        else:
            return [res['instrumentName'] for res in results if res['kind'] == kind]

    def get_index(self):
        r = requests.get(self.public + '/index')
        return r.json()['result']['btc']

    def get_orderbook(self, inst):
        r = requests.get(self.public + '/getorderbook?instrument=%s' % inst)
        return Book(r.json()['result']['bids'], r.json()['result']['asks'])

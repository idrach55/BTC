import matplotlib.pyplot as plt
import strategy
import deribit_api as api
import time
import pickle

tableau = pickle.load(open('../Research/tableau.colors', 'rb'))

plt.ion()

keys = strategy.read_keys()
client = api.RestClient(keys[0], keys[1])
book = strategy.Book('BTC-27APR18', client)

def get(ts, bid, ask, vwap_mid):
    ts.append(book.stamp)
    #idx.append(book.get_index())
    top = book.get_top()
    bid.append(top[0])
    ask.append(top[1])
    vwap_mid.append(0.5*(book.get_vwap(1000) + book.get_vwap(-1000)))
    return ts, bid, ask, vwap_mid

def plot():
    ts  = []
    idx = []
    bid = []
    ask = []
    vwap_mid = []
    fut = []
    while True:
        ts, bid, ask, vwap_mid = get(ts, bid, ask, vwap_mid)
        #plt.plot(ts, idx, c=tableau[0], lw=2)
        plt.plot(ts, bid, c=tableau[3], lw=2)
        plt.plot(ts, ask, c=tableau[3], lw=2)
        plt.plot(ts, vwap_mid, c=tableau[1], lw=2)

        # Styles...
        plt.grid(True)
        plt.ylim(vwap_mid[-1]-10,vwap_mid[-1]+10)
        #plt.set

        # Pause...
        plt.pause(0.1)

if __name__ == "__main__":
    time.sleep(1.0)
    plot()

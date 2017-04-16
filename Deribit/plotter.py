import requests
import matplotlib.pyplot as plt

from datetime import datetime


plt.ion()

def get(ts, idx, fut):
    resp = requests.get('https://www.deribit.com/api/v1/public/getsummary?instrument=BTC-10FEB17').json()
    ts.append(datetime.fromtimestamp(resp['msOut']/1e3))
    idx.append(resp['result']['estDelPrice'])
    fut.append(0.5*(resp['result']['askPrice'] + resp['result']['bidPrice']))
    return ts, idx, fut

def plot():
    ts  = []
    idx = []
    fut = []
    while True:
        ts, idx, fut = get(ts, idx, fut)
        plt.plot(ts, idx, c='b')
        plt.plot(ts, fut, c='r')

        # Styles...
        plt.grid(True)
        #plt.set

        # Pause...
        plt.pause(0.1)

if __name__ == "__main__":
    plot()
